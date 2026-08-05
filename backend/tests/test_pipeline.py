import pytest
from datetime import datetime
from backend.app.services.pdf_parser import StatementParser
from backend.app.agents.reconciliation_graph import build_reconciliation_graph
from backend.app.agents.insights_graph import build_insights_graph


def test_statement_csv_parser():
    sample_csv = b"Date,Description,Amount\n2026-08-01,Starbucks Coffee,-5.50\n2026-08-02,Salary Deposit,2500.00\n"
    txs = StatementParser.parse_file(sample_csv, "sample.csv")
    
    assert len(txs) == 2
    assert txs[0]["raw_description"] == "Starbucks Coffee"
    assert txs[0]["amount"] == -5.50
    assert txs[1]["amount"] == 2500.00


def test_reconciliation_graph_anomaly_and_dedup():
    reconcile_graph = build_reconciliation_graph()
    
    raw_txs = [
        {"raw_description": "Starbucks Coffee", "amount": -5.50, "date": "2026-08-01"},
        {"raw_description": "Starbucks Coffee", "amount": -5.50, "date": "2026-08-01"},  # Duplicate
        {"raw_description": "Luxury Watch Store", "amount": -4500.00, "date": "2026-08-02"},  # Suspicious high amount
    ]

    initial_state = {
        "statement_id": "test_stmt_123",
        "raw_transactions": raw_txs,
        "normalized_transactions": [],
        "flagged_transactions": [],
        "approved_transactions": [],
        "current_step": "START",
        "requires_hitl": False
    }

    final_state = reconcile_graph.invoke(initial_state)

    assert final_state["current_step"] in ["PAUSED_FOR_HITL", "SCORED"]
    assert final_state["requires_hitl"] is True
    assert len(final_state["flagged_transactions"]) >= 1

    # Check duplicate detection
    dup_txs = [t for t in final_state["normalized_transactions"] if t["is_duplicate"]]
    assert len(dup_txs) == 1

    # Check suspicious activity flagging
    suspicious_txs = [t for t in final_state["normalized_transactions"] if t["is_suspicious"]]
    assert len(suspicious_txs) >= 1


def test_insights_graph_metrics():
    insights_graph = build_insights_graph()
    
    sample_txs = [
        {"amount": 3000.00, "category": "Income"},
        {"amount": -500.00, "category": "Rent"},
        {"amount": -200.00, "category": "Groceries"}
    ]

    state = {
        "transactions": sample_txs,
        "goals": [],
        "category_summary": {},
        "total_income": 0.0,
        "total_expenses": 0.0,
        "savings_rate": 0.0,
        "insights_report": ""
    }

    final_state = insights_graph.invoke(state)

    assert final_state["total_income"] == 3000.00
    assert final_state["total_expenses"] == 700.00
    assert final_state["savings_rate"] > 0
