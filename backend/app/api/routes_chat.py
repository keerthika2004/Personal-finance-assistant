from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.db.database import get_db
from backend.app.db.models import Transaction, UserGoal
from backend.app.api.auth import get_current_user_id
from backend.app.agents.chat_graph import build_chat_graph

router = APIRouter(prefix="/api/v1/chat", tags=["Financial Chat Agent"])


class ChatQueryRequest(BaseModel):
    message: str


@router.post("")
async def query_financial_agent(
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Processes user natural language financial queries using the Groq-powered Chat Agent."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")

    # Fetch recent transactions for current user context
    tx_query = await db.execute(
        select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.date.desc()).limit(100)
    )
    txs = tx_query.scalars().all()

    # Fetch user goals for current user context
    goal_query = await db.execute(
        select(UserGoal).where(UserGoal.user_id == user_id)
    )
    goals = goal_query.scalars().all()

    tx_dicts = [
        {
            "date": t.date.strftime("%Y-%m-%d"),
            "amount": t.amount,
            "raw_description": t.raw_description,
            "normalized_merchant": t.normalized_merchant,
            "category": t.category
        }
        for t in txs
    ]

    goal_dicts = [
        {
            "goal_name": g.goal_name,
            "target_amount": g.target_amount,
            "current_amount": g.current_amount
        }
        for g in goals
    ]

    # Run LangGraph Chat Agent
    chat_graph = build_chat_graph()
    initial_state = {
        "user_query": request.message,
        "transaction_context": tx_dicts,
        "goals_context": goal_dicts,
        "response": ""
    }

    final_state = chat_graph.invoke(initial_state)

    return {
        "user_query": request.message,
        "response": final_state.get("response", "No response generated.")
    }
