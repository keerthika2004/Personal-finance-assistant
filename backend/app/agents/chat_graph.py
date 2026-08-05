from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from backend.app.services.llm_factory import LLMFactory


class ChatAgentState(TypedDict):
    user_query: str
    transaction_context: List[Dict[str, Any]]
    goals_context: List[Dict[str, Any]]
    response: str


def format_context_node(state: ChatAgentState) -> ChatAgentState:
    # Truncate to most recent / relevant records if large
    txs = state.get("transaction_context", [])[:50]
    formatted_txs = []
    for t in txs:
        formatted_txs.append(
            f"- Date: {t.get('date')}, Merchant: {t.get('normalized_merchant') or t.get('raw_description')}, "
            f"Amount: ${t.get('amount')}, Category: {t.get('category')}"
        )
    state["transaction_context"] = formatted_txs
    return state


def generate_chat_response_node(state: ChatAgentState) -> ChatAgentState:
    query = state["user_query"]
    txs = state["transaction_context"]
    goals = state.get("goals_context", [])

    try:
        llm = LLMFactory.get_llm(temperature=0.2)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent AI Personal Finance Assistant. Answer the user's question using their actual transaction history and financial goals provided below. Be precise, helpful, and concise."),
            ("user", "User Query: {query}\n\nRecent Transactions:\n{txs}\n\nUser Goals:\n{goals}")
        ])
        chain = prompt | llm

        res = chain.invoke({
            "query": query,
            "txs": "\n".join(txs) if txs else "No transactions recorded yet.",
            "goals": str(goals) if goals else "No explicit goals set yet."
        })
        state["response"] = str(res.content).strip()
    except Exception as e:
        state["response"] = f"I'm sorry, I ran into an error processing your query: {str(e)}"

    return state


def build_chat_graph():
    workflow = StateGraph(ChatAgentState)

    workflow.add_node("format_context", format_context_node)
    workflow.add_node("generate_response", generate_chat_response_node)

    workflow.set_entry_point("format_context")
    workflow.add_edge("format_context", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()
