import random
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.db.database import get_db
from backend.app.db.models import Statement, Transaction
from backend.app.agents.reconciliation_graph import build_reconciliation_graph

router = APIRouter(prefix="/api/v1/bank-sync", tags=["Bank Sync"])

# In-memory session store for AA Sandbox sessions
sessions = {}


class InitiateSyncRequest(BaseModel):
    bank_id: str
    bank_name: str
    phone_number: str


class VerifyOTPRequest(BaseModel):
    session_id: str
    otp: str


class TriggerSyncRequest(BaseModel):
    session_id: str


# Pre-configured mock transaction templates per bank for realistic AA payload simulation
MOCK_BANK_PAYLOADS = {
    "hdfc": [
        {"description": "HDFC SALARY CREDIT INFOSYS LTD", "amount": 85000.0, "days_ago": 1},
        {"description": "SWIGGY BANGALORE", "amount": -450.0, "days_ago": 2},
        {"description": "AMAZON PAY INDIA PVT LTD", "amount": -1299.0, "days_ago": 3},
        {"description": "NETFLIX ENTERTAINMENT", "amount": -649.0, "days_ago": 5},
        {"description": "DIVIDEND TATA MOTORS LTD", "amount": 3500.0, "days_ago": 7},
        {"description": "BESCOM ELECTRICITY BILL", "amount": -1850.0, "days_ago": 8},
        {"description": "UBER INDIA RIDES", "amount": -320.0, "days_ago": 10},
        {"description": "NIPPON INDIA MUTUAL FUND SIP", "amount": -5000.0, "days_ago": 12},
        {"description": "CULT FIT FITNESS CENTRE", "amount": -1499.0, "days_ago": 15},
        {"description": "ZOMATO RESTAURANT ORDER", "amount": -780.0, "days_ago": 18},
        {"description": "FRESH DIRECT GROCERIES", "amount": -1120.0, "days_ago": 20},
        {"description": "RELIANCE RETAIL MART", "amount": -2450.0, "days_ago": 25},
    ],
    "sbi": [
        {"description": "SBI INB SALARY TCS LTD", "amount": 78000.0, "days_ago": 1},
        {"description": "DMART RETAIL STORE", "amount": -3250.0, "days_ago": 2},
        {"description": "INDIAN OIL PETROL PUMP", "amount": -2000.0, "days_ago": 4},
        {"description": "ZEPTO DAILY GROCERIES", "amount": -680.0, "days_ago": 6},
        {"description": "APOLLO PHARMACY MEDICAL", "amount": -890.0, "days_ago": 9},
        {"description": "MUTUAL FUND SIP ZERODHA", "amount": -10000.0, "days_ago": 11},
        {"description": "AIRTEL BROADBAND BILL", "amount": -999.0, "days_ago": 14},
        {"description": "BOOKMYSHOW MOVIE TICKETS", "amount": -600.0, "days_ago": 16},
        {"description": "BLINKIT QUICK COMMERCE", "amount": -430.0, "days_ago": 19},
        {"description": "INTEREST CREDIT SBI SAVINGS", "amount": 1250.0, "days_ago": 22},
    ],
    "icici": [
        {"description": "ICICI DIRECT STOCK DIVIDEND", "amount": 5400.0, "days_ago": 1},
        {"description": "MAKE MY TRIP FLIGHTS", "amount": -8900.0, "days_ago": 3},
        {"description": "STARBUCKS COFFEE", "amount": -420.0, "days_ago": 4},
        {"description": "ZOMATO ONLINE ORDER", "amount": -390.0, "days_ago": 5},
        {"description": "ICICI PRUDENTIAL LIFE INS", "amount": -4500.0, "days_ago": 9},
        {"description": "DECATHLON SPORTS INDIA", "amount": -2100.0, "days_ago": 13},
        {"description": "SWIGGY INSTAMART", "amount": -540.0, "days_ago": 15},
        {"description": "SHELL PETROL STATION", "amount": -1800.0, "days_ago": 18},
        {"description": "FREELANCE CONSULTING INCOME", "amount": 25000.0, "days_ago": 21},
    ],
    "axis": [
        {"description": "AXIS BANK CREDIT CARD REWARD CASHBACK", "amount": 1200.0, "days_ago": 1},
        {"description": "UBER INDIA RIDES", "amount": -340.0, "days_ago": 2},
        {"description": "CULT FIT GYM SUBSCRIPTION", "amount": -1999.0, "days_ago": 5},
        {"description": "BOOKMYSHOW MOVIE TICKETS", "amount": -750.0, "days_ago": 6},
        {"description": "APPLE MUSIC MONTHLY", "amount": -149.0, "days_ago": 10},
        {"description": "NYKAA BEAUTY STORE", "amount": -1850.0, "days_ago": 12},
        {"description": "CREDIT CARD BILL PAYMENT", "amount": -12400.0, "days_ago": 15},
        {"description": "TATA 1MG MEDICINES", "amount": -720.0, "days_ago": 17},
    ]
}


@router.post("/initiate")
async def initiate_consent(req: InitiateSyncRequest):
    """Initiates an Account Aggregator (AA) consent request for the selected bank."""
    if len(req.phone_number) < 10:
        raise HTTPException(status_code=400, detail="Invalid 10-digit Indian phone number.")

    session_id = f"aa_session_{uuid.uuid4().hex[:8]}"
    generated_otp = str(random.randint(100000, 999999))
    
    sessions[session_id] = {
        "bank_id": req.bank_id,
        "bank_name": req.bank_name,
        "phone_number": req.phone_number,
        "otp": generated_otp,
        "verified": False,
        "created_at": datetime.utcnow()
    }

    return {
        "status": "success",
        "message": f"Consent request initiated with {req.bank_name} via RBI Account Aggregator.",
        "session_id": session_id,
        "preview_otp": generated_otp,
        "phone_number": req.phone_number
    }


@router.post("/verify-otp")
async def verify_otp(req: VerifyOTPRequest):
    """Verifies the Account Aggregator consent OTP."""
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid or expired sync session.")

    # Accept either generated OTP or universal testing OTP '123456'
    if req.otp != session["otp"] and req.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP code. Please try again.")

    session["verified"] = True
    return {
        "status": "success",
        "message": f"Account Aggregator consent approved for {session['bank_name']}.",
        "session_id": req.session_id
    }


@router.post("/sync")
async def sync_bank_data(req: TriggerSyncRequest, db: AsyncSession = Depends(get_db)):
    """Fetches live transactions from the bank via Account Aggregator and runs them through the Reconciliation pipeline."""
    session = sessions.get(req.session_id)
    if not session or not session.get("verified"):
        raise HTTPException(status_code=400, detail="Unapproved or invalid Account Aggregator session.")

    bank_id = session["bank_id"].lower()
    bank_name = session["bank_name"]
    raw_templates = MOCK_BANK_PAYLOADS.get(bank_id, MOCK_BANK_PAYLOADS["hdfc"])

    # Build raw transaction payloads matching statement parser format
    now = datetime.now()
    raw_txs = []
    for item in raw_templates:
        tx_date = (now - timedelta(days=item["days_ago"])).strftime("%Y-%m-%d %H:%M:%S")
        raw_txs.append({
            "date": tx_date,
            "raw_description": item["description"],
            "amount": item["amount"]
        })

    # Create Statement record
    stmt = Statement(
        file_name=f"AA_LiveSync_{bank_name}_{session['phone_number'][-4:]}.json",
        file_hash=f"aa_{uuid.uuid4().hex[:12]}",
        file_type="api_sync"
    )
    db.add(stmt)
    await db.commit()
    await db.refresh(stmt)

    # Fetch existing DB signatures for deduplication
    result = await db.execute(select(Transaction))
    existing_db_txs = result.scalars().all()

    existing_signatures = []
    for t in existing_db_txs:
        date_str = str(t.date)
        merchant_clean = str(t.normalized_merchant).strip().lower() if t.normalized_merchant else ""
        existing_signatures.append(f"{date_str}_{t.amount}_{merchant_clean}")

    # Run LangGraph Reconciliation Graph
    reconcile_graph = build_reconciliation_graph()
    initial_state = {
        "statement_id": stmt.id,
        "raw_transactions": raw_txs,
        "normalized_transactions": [],
        "flagged_transactions": [],
        "approved_transactions": [],
        "existing_signatures": existing_signatures,
        "current_step": "START",
        "requires_hitl": False
    }

    try:
        final_state = reconcile_graph.invoke(initial_state)
    except Exception as e:
        print("BANK_SYNC_RECON_GRAPH_EXCEPTION:", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Reconciliation error during bank sync: {str(e)}")

    # Persist all normalized/flagged transactions into DB
    auto_approved = 0
    review_queue = 0
    for tx in final_state.get("normalized_transactions", []):
        tx_status = "PENDING"
        if tx["status"] == "FLAGGED":
            tx_status = "FLAGGED"
            review_queue += 1
        elif tx["status"] == "APPROVED":
            tx_status = "APPROVED"
            auto_approved += 1
        else:
            auto_approved += 1

        try:
            dt = datetime.strptime(str(tx["date"]).split(".")[0], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.utcnow()

        db_tx = Transaction(
            statement_id=stmt.id,
            date=dt,
            amount=tx["amount"],
            raw_description=tx["raw_description"],
            normalized_merchant=str(tx["normalized_merchant"])[:150] if tx.get("normalized_merchant") else None,
            category=str(tx["category"])[:100] if tx.get("category") else "Uncategorized",
            is_duplicate=tx.get("is_duplicate", False),
            is_suspicious=tx.get("is_suspicious", False),
            anomaly_score=tx.get("anomaly_score", 0.0),
            anomaly_reason=tx.get("anomaly_reason"),
            status=tx_status
        )
        db.add(db_tx)

    stmt.status = "PAUSED_HITL" if final_state.get("requires_hitl") else "COMPLETED"
    await db.commit()

    # Clean up session
    del sessions[req.session_id]

    return {
        "status": "success",
        "message": f"Successfully synced transactions from {bank_name}.",
        "bank_name": bank_name,
        "auto_approved_count": auto_approved,
        "review_queue_count": review_queue
    }
