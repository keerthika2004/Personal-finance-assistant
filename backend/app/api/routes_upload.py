import hashlib
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.db.database import get_db
from backend.app.db.models import Statement, Transaction, TransactionStatus
from backend.app.services.pdf_parser import StatementParser
from backend.app.agents.reconciliation_graph import build_reconciliation_graph

router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])


class ManualTransactionRequest(BaseModel):
    date: str
    description: str
    amount: float
    category: Optional[str] = None


class ChatTransactionRequest(BaseModel):
    text: str


class ExtractedTransaction(BaseModel):
    amount: float
    description: str
    date: Optional[str] = None
    transaction_type: Literal["income", "expense"]
    category: str


@router.post("")
async def upload_statement(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Uploads a bank PDF or CSV statement file, parses transactions, and runs the LangGraph Reconciliation pipeline."""
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file submitted.")

    import time
    file_hash = hashlib.sha256(contents + str(time.time()).encode()).hexdigest()

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

    # Load existing database signatures to check for duplicates across uploads
    query = await db.execute(select(Transaction).where(Transaction.status != "REJECTED"))
    existing_db_txs = query.scalars().all()
    
    # We parse the date into the exact format it will be processed in during deduplication
    existing_signatures = []
    for t in existing_db_txs:
        date_str = str(t.date)
        merchant_clean = str(t.normalized_merchant).strip().lower()
        existing_signatures.append(f"{date_str}_{t.amount}_{merchant_clean}")

    # Run LangGraph Reconciliation Graph
    reconcile_graph = build_reconciliation_graph()
    initial_state = {
        "statement_id": stmt.id,
        "raw_transactions": parsed_txs,
        "normalized_transactions": [],
        "flagged_transactions": [],
        "approved_transactions": [],
        "existing_signatures": existing_signatures,
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


@router.post("/manual")
async def upload_manual_transaction(
    request: ManualTransactionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Manually inserts a single transaction and processes it via the LangGraph pipeline."""
    # Create pseudo Statement record
    import time
    pseudo_hash = hashlib.sha256(f"manual_{request.date}_{request.description}_{request.amount}_{time.time()}".encode()).hexdigest()
    stmt = Statement(
        file_name="Manual Entry",
        file_hash=pseudo_hash,
        file_type="manual",
        status="RECONCILING"
    )
    db.add(stmt)
    await db.flush()

    # Format exactly like parsed_txs output from PDF/CSV
    parsed_txs = [{
        "date": request.date,
        "raw_description": request.description,
        "amount": request.amount,
        "category": request.category
    }]

    # Load existing database signatures to check for duplicates across uploads
    query = await db.execute(select(Transaction).where(Transaction.status != "REJECTED"))
    existing_db_txs = query.scalars().all()
    
    # We parse the date into the exact format it will be processed in during deduplication
    existing_signatures = []
    for t in existing_db_txs:
        date_str = str(t.date)
        merchant_clean = str(t.normalized_merchant).strip().lower()
        existing_signatures.append(f"{date_str}_{t.amount}_{merchant_clean}")

    # Run LangGraph Reconciliation Graph
    reconcile_graph = build_reconciliation_graph()
    initial_state = {
        "statement_id": stmt.id,
        "raw_transactions": parsed_txs,
        "normalized_transactions": [],
        "flagged_transactions": [],
        "approved_transactions": [],
        "existing_signatures": existing_signatures,
        "current_step": "START",
        "requires_hitl": False
    }

    final_state = reconcile_graph.invoke(initial_state)

    # Persist the transaction
    for tx in final_state.get("normalized_transactions", []):
        tx_status = "PENDING"
        if tx["status"] == "FLAGGED":
            tx_status = "FLAGGED"
        elif tx["status"] == "APPROVED":
            tx_status = "APPROVED"

        from datetime import datetime
        try:
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

    stmt.status = "PAUSED_HITL" if final_state.get("requires_hitl") else "COMPLETED"
    await db.commit()

    return {
        "message": "Manual transaction processed successfully.",
        "statement_id": stmt.id,
        "requires_hitl": final_state.get("requires_hitl", False)
    }


@router.post("/chat")
async def upload_chat_transaction(
    request: ChatTransactionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Parses a natural language chat string and converts it to a manual transaction."""
    from backend.app.services.llm_factory import LLMFactory
    from langchain_core.prompts import ChatPromptTemplate
    from datetime import datetime
    
    # Initialize LLM with structured output using a faster model to avoid rate limits
    llm = LLMFactory.get_llm(temperature=0.0, model_name="llama-3.1-8b-instant")
    structured_llm = llm.with_structured_output(ExtractedTransaction)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are a financial assistant. Extract the amount, a short description (merchant/item), transaction_type (income or expense), and a broad category (e.g. Salary, Groceries, Dining) from the user's text. If they specify a date, convert it to YYYY-MM-DD format. Today's date is {today_str}. If no date is specified, return None for date."),
        ("user", "{text}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        res: ExtractedTransaction = chain.invoke({"text": request.text})
    except Exception as e:
        print(f"NLP PARSING ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to parse transaction from text: {str(e)}")
        
    # Default to today if date is missing
    tx_date = res.date if res.date else today_str
    # Convert amount to negative if it's an expense
    amount = -abs(res.amount) if res.transaction_type == "expense" else abs(res.amount)
        
    manual_req = ManualTransactionRequest(
        date=tx_date,
        description=res.description,
        amount=amount,
        category=res.category
    )
    
    return await upload_manual_transaction(manual_req, db)
