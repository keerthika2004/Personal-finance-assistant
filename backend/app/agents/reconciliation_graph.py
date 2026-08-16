import math
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from backend.app.services.llm_factory import LLMFactory
from backend.app.services.categorizer import MLCategorizer
from backend.app.services.pii_redactor import PIIRedactor
from backend.app.services.anomaly_detector import HybridAnomalyDetector
import os


class TransactionItem(TypedDict):
    id: Optional[str]
    date: str
    raw_description: str
    amount: float
    normalized_merchant: Optional[str]
    category: Optional[str]
    is_duplicate: bool
    duplicate_of_id: Optional[str]
    is_suspicious: bool
    anomaly_score: float
    anomaly_reason: Optional[str]
    status: str  # PENDING, APPROVED, REJECTED, FLAGGED


class ReconciliationState(TypedDict):
    statement_id: str
    raw_transactions: List[Dict[str, Any]]
    normalized_transactions: List[TransactionItem]
    flagged_transactions: List[TransactionItem]
    approved_transactions: List[TransactionItem]
    existing_signatures: List[str]
    current_step: str
    requires_hitl: bool


# Node 1: Normalization & Category Classification
def normalize_and_categorize_node(state: ReconciliationState) -> ReconciliationState:
    raw_txs = state["raw_transactions"]
    normalized: List[TransactionItem] = []
    
    use_ml = os.environ.get("USE_ML_CATEGORIZER", "true").lower() == "true"
    chain = None
    
    # Always initialize LLM chain as fallback
    try:
        llm = LLMFactory.get_llm(temperature=0.0, fast=True)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a financial transaction normalizer. For the given raw transaction description, return the clean Merchant Name and assign one of the following Categories: [Groceries, Dining, Transportation, Utilities, Shopping, Entertainment, Income, Transfer, Healthcare, Subscriptions, Housing, Uncategorized]. Format response as: Merchant | Category"),
            ("user", "{description}")
        ])
        chain = prompt | llm
    except Exception as e:
        print(f"Failed to initialize LLM chain: {e}")

    for item in raw_txs:
        desc = PIIRedactor.redact(item.get("raw_description", ""))
        merchant = desc
        category = item.get("category", "Uncategorized")
        if not category:
            category = "Uncategorized"

        if desc and category == "Uncategorized":
            if use_ml:
                category = MLCategorizer.predict_category(desc)
                merchant = desc
                # Fallback to LLM if ML is unconfident or OOV
                if category == "Uncategorized" and chain:
                    try:
                        res = chain.invoke({"description": desc})
                        content = str(res.content).strip()
                        if "|" in content:
                            parts = content.split("|")
                            merchant = parts[0].strip()
                            category = parts[1].strip()
                    except Exception:
                        pass
            elif chain:
                try:
                    res = chain.invoke({"description": desc})
                    content = str(res.content).strip()
                    if "|" in content:
                        parts = content.split("|")
                        merchant = parts[0].strip()
                        category = parts[1].strip()
                except Exception:
                    pass

        normalized.append({
            "id": item.get("id"),
            "date": str(item.get("date")),
            "raw_description": desc,
            "amount": float(item.get("amount", 0.0)),
            "normalized_merchant": merchant,
            "category": category,
            "is_duplicate": False,
            "duplicate_of_id": None,
            "is_suspicious": False,
            "anomaly_score": 0.0,
            "anomaly_reason": None,
            "status": "PENDING"
        })

    state["normalized_transactions"] = normalized
    state["current_step"] = "NORMALIZED"
    return state


# Node 2: Deduplication Detection
def deduplication_node(state: ReconciliationState) -> ReconciliationState:
    txs = state["normalized_transactions"]
    existing_sigs = state.get("existing_signatures", [])
    seen = {}

    for tx in txs:
        # Match key: date + amount + normalized_merchant (case-insensitive and stripped)
        merchant_clean = str(tx['normalized_merchant']).strip().lower()
        key = f"{tx['date']}_{tx['amount']}_{merchant_clean}"
        is_db_dup = key in existing_sigs

        if key in seen or is_db_dup:
            tx["is_duplicate"] = True
            tx["duplicate_of_id"] = seen.get(key, "existing_db_tx")
            tx["status"] = "FLAGGED"
        else:
            seen[key] = tx.get("id", key)

    state["normalized_transactions"] = txs
    state["current_step"] = "DEDUPLICATED"
    return state


# Node 3: Anomaly & Suspicious Activity Scoring
def anomaly_scoring_node(state: ReconciliationState) -> ReconciliationState:
    txs = state["normalized_transactions"]
    if not txs:
        state["current_step"] = "SCORED"
        return state

    historical_txs = state.get("existing_historical_txs", [])

    # Pass transactions to the Hybrid ML Anomaly Detector (Isolation Forest + Category Z-score)
    scored_txs = HybridAnomalyDetector.detect_and_score(txs, historical_txs)
    flagged = [t for t in scored_txs if t.get("status") == "FLAGGED"]

    state["normalized_transactions"] = scored_txs
    state["flagged_transactions"] = flagged
    state["requires_hitl"] = len(flagged) > 0
    state["current_step"] = "SCORED"
    return state


# Conditional Router Node for HITL Check
def hitl_router(state: ReconciliationState) -> str:
    if state.get("requires_hitl", False):
        return "hitl_review_pause"
    return "commit_node"


# Node 4: HITL Pause Marker Node
def hitl_review_pause_node(state: ReconciliationState) -> ReconciliationState:
    state["current_step"] = "PAUSED_FOR_HITL"
    return state


# Node 5: Commit Approved Node
def commit_node(state: ReconciliationState) -> ReconciliationState:
    approved = [t for t in state["normalized_transactions"] if t["status"] != "REJECTED"]
    for t in approved:
        if t["status"] == "PENDING":
            t["status"] = "APPROVED"
            
    state["approved_transactions"] = approved
    state["current_step"] = "COMPLETED"
    return state


# Build LangGraph StateGraph Workflow
def build_reconciliation_graph():
    workflow = StateGraph(ReconciliationState)

    workflow.add_node("normalize", normalize_and_categorize_node)
    workflow.add_node("deduplicate", deduplication_node)
    workflow.add_node("anomaly_score", anomaly_scoring_node)
    workflow.add_node("hitl_review_pause", hitl_review_pause_node)
    workflow.add_node("commit_node", commit_node)

    workflow.set_entry_point("normalize")
    workflow.add_edge("normalize", "deduplicate")
    workflow.add_edge("deduplicate", "anomaly_score")
    
    workflow.add_conditional_edges(
        "anomaly_score",
        hitl_router,
        {
            "hitl_review_pause": "hitl_review_pause",
            "commit_node": "commit_node"
        }
    )
    
    workflow.add_edge("hitl_review_pause", END)
    workflow.add_edge("commit_node", END)

    return workflow.compile()
