from langgraph.errors import GraphRecursionError
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from langchain_core.messages import HumanMessage

from backend.app.db.database import get_db
from backend.app.db.models import Transaction, UserGoal
from backend.app.api.auth import get_current_user_id
from backend.app.agents.chat_graph import build_chat_agent
from backend.app.agents.finance_tools import build_finance_tools
from backend.app.services.pii_redactor import PIIRedactor

router = APIRouter(prefix="/api/v1/chat", tags=["Financial Chat Agent"])


class ChatQueryRequest(BaseModel):
    message: str

SYSTEM_TEMPLATE = (
    "You are a precise AI personal finance assistant. Today's date is {today}.\n"
    "You have tools that query the user's ACTUAL transaction data.\n"
    "ALWAYS call a tool to get exact figures - NEVER estimate or invent numbers.\n"
    "If a tool returns no data, tell the user you don't have that information.\n"
    "Only answer questions about the user's personal finances; politely decline anything else.\n"
    "Amounts are in Indian Rupees (Rs). Be concise."
)

@router.post("")
async def query_financial_agent(
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")

    # Load all of the users transactions
    tx_query = await db.execute(
        select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.date.desc())
    )
    txs = tx_query.scalars().all()
    goals = (await db.execute(select(UserGoal).where(UserGoal.user_id == user_id))).scalars().all()

    tx_dicts = [
        {
            "date": t.date, "amount": t.amount, "category": t.category, "normalized_merchant": t.normalized_merchant or t.raw_description, "raw_description": t.raw_description
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

    tools = build_finance_tools(tx_dicts, goal_dicts)
    agent = build_chat_agent(tools, SYSTEM_TEMPLATE.format(today=date.today().isoformat()))

    safe_query = PIIRedactor.redact(request.message)
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=safe_query)]},config = {"recursion_limit": 8},
        )
        response = result["messages"][-1].content or "I couldn't find an answer to that."
    except GraphRecursionError:
        response = "I had trouble answering that reliably. Could you rephrase or be more specific?"

    return {"user_query": request.message, "response": response}


