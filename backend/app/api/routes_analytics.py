from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.db.database import get_db
from backend.app.db.models import Transaction, TransactionStatus, UserGoal
from backend.app.api.auth import get_current_user_id
from backend.app.agents.insights_graph import get_insights_graph
from backend.app.services.forecasting import generate_forecast
from datetime import datetime

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


class TransactionUpdateRequest(BaseModel):
    date: Optional[str] = None
    normalized_merchant: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None


class GoalCreateRequest(BaseModel):
    goal_name: str
    target_amount: float
    current_amount: Optional[float] = 0.0
    category_target: Optional[str] = "Savings"


@router.get("/summary")
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Returns aggregated KPI summary metrics, category breakdowns, and LLM insights report for current user."""
    query = await db.execute(
        select(Transaction).where(
            Transaction.status == "APPROVED",
            Transaction.user_id == user_id
        )
    )
    approved_txs = query.scalars().all()

    goals_query = await db.execute(
        select(UserGoal).where(UserGoal.user_id == user_id)
    )
    goals = goals_query.scalars().all()

    tx_dicts = [
        {
            "id": t.id,
            "date": t.date.isoformat(),
            "amount": t.amount,
            "category": t.category,
            "normalized_merchant": t.normalized_merchant
        }
        for t in approved_txs
    ]

    goal_dicts = [
        {
            "id": g.id,
            "goal_name": g.goal_name,
            "target_amount": g.target_amount,
            "current_amount": g.current_amount,
            "category_target": g.category_target
        }
        for g in goals
    ]

    # Run Insights LangGraph Agent
    insights_graph = get_insights_graph()
    state = {
        "transactions": tx_dicts,
        "goals": goal_dicts,
        "category_summary": {},
        "total_income": 0.0,
        "total_expenses": 0.0,
        "savings_rate": 0.0,
        "insights_report": "",
        "goal_coaching": {}
    }

    final_state = insights_graph.invoke(state)

    # Compute monthly trends for charts
    monthly_trend = {}
    for t in approved_txs:
        month_key = t.date.strftime("%Y-%m")
        if month_key not in monthly_trend:
            monthly_trend[month_key] = {"income": 0.0, "expenses": 0.0}
        if t.amount > 0:
            monthly_trend[month_key]["income"] += t.amount
        else:
            monthly_trend[month_key]["expenses"] += abs(t.amount)

    # Generate 30-day forecast
    forecast = generate_forecast(tx_dicts, periods=30)
    
    # Calculate Advanced Health Score
    health_score = 50.0  # Base Score
    
    # 1. Savings Rate Factor (+/- 25 pts)
    # Target: 20%. Each 1% above/below adjusts score by 1.25 pts.
    savings_rate = final_state.get("savings_rate", 0.0)
    savings_factor = max(-25.0, min(25.0, (savings_rate - 20.0) * 1.25))
    health_score += savings_factor
    
    # 2. Essential vs Discretionary Factor (+/- 15 pts)
    # Essential (Housing, Utilities, Groceries, Healthcare, Transportation) vs Discretionary (Shopping, Entertainment, Dining)
    total_expenses = final_state.get("total_expenses", 0.0)
    discretionary_spend = 0.0
    for cat, amt in final_state.get("category_summary", {}).items():
        if cat in ["Shopping", "Entertainment", "Dining"]:
            discretionary_spend += amt
    
    if total_expenses > 0:
        discretionary_ratio = discretionary_spend / total_expenses
        # Ideal discretionary ratio is < 30% of total expenses. Every 1% difference adjusts score by 50 pts.
        disc_factor = max(-15.0, min(15.0, (0.30 - discretionary_ratio) * 50.0))
        health_score += disc_factor
    
    # 3. Goal Progress Factor (+/- 10 pts)
    goal_factor = 0.0
    if goal_dicts:
        avg_goal_progress = sum([g["current_amount"] / g["target_amount"] if g["target_amount"] > 0 else 0 for g in goal_dicts]) / len(goal_dicts)
        goal_factor = min(10.0, avg_goal_progress * 10.0)
    health_score += goal_factor
    
    final_health_score = int(max(0, min(100, health_score)))

    return {
        "health_score": final_health_score,
        "total_income": final_state.get("total_income", 0.0),
        "total_expenses": final_state.get("total_expenses", 0.0),
        "net_savings": round(final_state.get("total_income", 0.0) - final_state.get("total_expenses", 0.0), 2),
        "savings_rate": final_state.get("savings_rate", 0.0),
        "category_breakdown": final_state.get("category_summary", {}),
        "monthly_trend": monthly_trend,
        "insights_report": final_state.get("insights_report", ""),
        "goal_coaching": final_state.get("goal_coaching", {}),
        "goals": goal_dicts,
        "forecast": forecast,
        "transactions": tx_dicts
    }


@router.post("/goals")
async def create_user_goal(
    request: GoalCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Creates a new financial savings goal for the current user."""
    goal = UserGoal(
        user_id=user_id,
        goal_name=request.goal_name,
        target_amount=request.target_amount,
        current_amount=request.current_amount or 0.0,
        category_target=request.category_target or "Savings"
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)

    return {
        "message": "Goal created successfully",
        "goal_id": goal.id,
        "goal_name": goal.goal_name
    }

class AddFundsRequest(BaseModel):
    amount: float

@router.put("/goals/{goal_id}/add")
async def add_funds_to_goal(
    goal_id: str,
    request: AddFundsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Adds funds to an existing financial goal."""
    query = await db.execute(select(UserGoal).where(UserGoal.id == goal_id))
    goal = query.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
        
    goal.current_amount += request.amount
    await db.commit()
    
    return {"message": "Funds added successfully", "new_amount": goal.current_amount}

@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Deletes a specific financial goal."""
    query = await db.execute(select(UserGoal).where(UserGoal.id == goal_id))
    goal = query.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
        
    await db.delete(goal)
    await db.commit()
    
    return {"message": "Goal deleted successfully"}

@router.delete("/transaction/{transaction_id}")
async def delete_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Deletes a specific transaction by ID."""
    query = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = query.scalar_one_or_none()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    await db.delete(tx)
    await db.commit()
    
    return {"message": "Transaction deleted successfully"}


@router.put("/transaction/{transaction_id}")
async def update_transaction(transaction_id: str, request: TransactionUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Updates specific fields of a transaction."""
    query = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = query.scalar_one_or_none()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if request.date is not None:
        try:
            # Handle MM/DD/YYYY from frontend
            if "/" in request.date:
                dt = datetime.strptime(request.date, "%d/%m/%Y")
            else:
                dt = datetime.fromisoformat(request.date)
            tx.date = dt
        except ValueError:
            pass # Keep original date if parsing fails
            
    if request.normalized_merchant is not None:
        tx.normalized_merchant = request.normalized_merchant
        
    if request.category is not None:
        tx.category = request.category
        
    if request.amount is not None:
        # Amount from frontend might be positive even for expenses, but let's assume they provide the raw float.
        # Actually in data_editor they will see positive amounts with a "₹" symbol, but we can clean that in frontend before sending.
        tx.amount = request.amount
        
    await db.commit()
    
    return {"message": "Transaction updated successfully"}
