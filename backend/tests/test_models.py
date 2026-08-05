import pytest
from datetime import datetime
from backend.app.db.models import Statement, Transaction, UserGoal

def test_statement_model_initialization():
    stmt = Statement(file_name="test.pdf", file_hash="abc", file_type="pdf", status="RECONCILING")
    assert stmt.file_name == "test.pdf"
    assert stmt.status == "RECONCILING"
    assert stmt.file_type == "pdf"

def test_transaction_model_initialization():
    tx = Transaction(
        amount=-100.50,
        raw_description="UBER TRIP",
        normalized_merchant="Uber",
        category="Transportation",
        status="PENDING",
        date=datetime(2024, 1, 1)
    )
    assert tx.amount == -100.50
    assert tx.category == "Transportation"
    assert tx.status == "PENDING"

def test_user_goal_initialization():
    goal = UserGoal(goal_name="Vacation", target_amount=5000, current_amount=1000)
    assert goal.goal_name == "Vacation"
    assert goal.target_amount == 5000
    assert goal.current_amount == 1000
