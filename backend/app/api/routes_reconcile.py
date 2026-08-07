from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.db.database import get_db
from backend.app.db.models import Transaction, TransactionStatus, AuditLog, Statement
from backend.app.api.auth import get_current_user_id

router = APIRouter(prefix="/api/v1/reconcile", tags=["Reconciliation & HITL"])


class HITLDecisionRequest(BaseModel):
    transaction_id: str
    action: str  # APPROVE or REJECT
    reason: Optional[str] = "User manual review decision"
    category: Optional[str] = None


@router.get("/pending")
async def get_pending_hitl_items(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Retrieves all flagged transactions waiting for Human-in-the-Loop user approval or rejection for current user."""
    query = await db.execute(
        select(Transaction).where(
            Transaction.status == "FLAGGED",
            Transaction.user_id == user_id
        )
    )
    flagged_txs = query.scalars().all()

    return [
        {
            "id": tx.id,
            "statement_id": tx.statement_id,
            "date": tx.date.isoformat(),
            "amount": tx.amount,
            "raw_description": tx.raw_description,
            "normalized_merchant": tx.normalized_merchant,
            "category": tx.category,
            "is_duplicate": tx.is_duplicate,
            "is_suspicious": tx.is_suspicious,
            "anomaly_score": tx.anomaly_score,
            "anomaly_reason": tx.anomaly_reason,
            "status": tx.status
        }
        for tx in flagged_txs
    ]


@router.post("/decision")
async def submit_hitl_decision(
    request: HITLDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Processes a user approval or rejection decision for a flagged transaction."""
    query = await db.execute(select(Transaction).where(Transaction.id == request.transaction_id))
    tx = query.scalar_one_or_none()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    action_upper = request.action.upper()
    if action_upper == "APPROVE":
        tx.status = "APPROVED"
        if request.category:
            tx.category = request.category
    elif action_upper == "REJECT":
        tx.status = "REJECTED"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'APPROVE' or 'REJECT'.")

    # Record Audit Log
    audit = AuditLog(
        transaction_id=tx.id,
        action=action_upper,
        reason=request.reason
    )
    db.add(audit)

    # Check if all transactions for this statement are now resolved
    if tx.statement_id:
        pending_query = await db.execute(
            select(Transaction).where(
                Transaction.statement_id == tx.statement_id,
                Transaction.status == "FLAGGED"
            )
        )
        remaining = pending_query.scalars().all()
        if not remaining:
            # Mark statement as completed
            stmt_query = await db.execute(select(Statement).where(Statement.id == tx.statement_id))
            stmt = stmt_query.scalar_one_or_none()
            if stmt:
                stmt.status = "COMPLETED"
            
            # Automatically approve all remaining PENDING transactions for this statement
            pending_txs_query = await db.execute(
                select(Transaction).where(
                    Transaction.statement_id == tx.statement_id,
                    Transaction.status == "PENDING"
                )
            )
            for p_tx in pending_txs_query.scalars().all():
                p_tx.status = "APPROVED"

    await db.commit()

    return {
        "message": f"Transaction {tx.id} decision '{action_upper}' successfully recorded.",
        "transaction_id": tx.id,
        "new_status": tx.status
    }
