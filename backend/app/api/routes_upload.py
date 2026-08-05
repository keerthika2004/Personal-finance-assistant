import hashlib
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.db.database import get_db
from backend.app.db.models import Statement, Transaction, TransactionStatus
from backend.app.services.pdf_parser import StatementParser
from backend.app.agents.reconciliation_graph import build_reconciliation_graph

router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])


@router.post("")
async def upload_statement(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Uploads a bank PDF or CSV statement file, parses transactions, and runs the LangGraph Reconciliation pipeline."""
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file submitted.")

    file_hash = hashlib.sha256(contents).hexdigest()

    # Check for duplicate file upload
    query = await db.execute(select(Statement).where(Statement.file_hash == file_hash))
    existing_stmt = query.scalar_one_or_none()
    if existing_stmt:
        return {
            "message": "Statement previously uploaded.",
            "statement_id": existing_stmt.id,
            "status": existing_stmt.status
        }

    # Parse raw transactions from PDF / CSV
    try:
        parsed_txs = StatementParser.parse_file(contents, file.filename)
    except Exception as e:
        print("PARSE_FILE EXCEPTION:", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to parse statement: {str(e)}")

    if not parsed_txs:
        raise HTTPException(status_code=400, detail="No valid transactions found in statement.")

    # Create Statement record
    file_type = "pdf"
    if file.filename.lower().endswith(".csv"):
        file_type = "csv"
    elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        file_type = "image"

    stmt = Statement(
        file_name=file.filename,
        file_hash=file_hash,
        file_type=file_type,
        status="RECONCILING"
    )
    db.add(stmt)
    await db.flush()

    # Run LangGraph Reconciliation Graph
    reconcile_graph = build_reconciliation_graph()
    initial_state = {
        "statement_id": stmt.id,
        "raw_transactions": parsed_txs,
        "normalized_transactions": [],
        "flagged_transactions": [],
        "approved_transactions": [],
        "current_step": "START",
        "requires_hitl": False
    }

    final_state = reconcile_graph.invoke(initial_state)

    # Persist all normalized/flagged transactions into DB
    created_txs = []
    for tx in final_state.get("normalized_transactions", []):
        tx_status = "PENDING"
        if tx["status"] == "FLAGGED":
            tx_status = "FLAGGED"
        elif tx["status"] == "APPROVED":
            tx_status = "APPROVED"

        from datetime import datetime
        try:
            # Handle standard stringified datetime 'YYYY-MM-DD HH:MM:SS'
            dt = datetime.strptime(str(tx["date"]).split(".")[0], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.utcnow()

        db_tx = Transaction(
            statement_id=stmt.id,
            date=dt,
            amount=tx["amount"],
            raw_description=tx["raw_description"],
            normalized_merchant=str(tx["normalized_merchant"])[:150] if tx["normalized_merchant"] else None,
            category=str(tx["category"])[:100] if tx["category"] else "Uncategorized",
            is_duplicate=tx["is_duplicate"],
            is_suspicious=tx["is_suspicious"],
            anomaly_score=tx["anomaly_score"],
            anomaly_reason=tx["anomaly_reason"],
            status=tx_status
        )
        db.add(db_tx)
        created_txs.append(db_tx)

    stmt.status = "PAUSED_HITL" if final_state.get("requires_hitl") else "COMPLETED"
    await db.commit()

    return {
        "message": "Statement processed successfully.",
        "statement_id": stmt.id,
        "total_parsed": len(parsed_txs),
        "flagged_count": len(final_state.get("flagged_transactions", [])),
        "requires_hitl": final_state.get("requires_hitl", False),
        "status": stmt.status
    }
