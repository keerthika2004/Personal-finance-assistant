from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from backend.app.services.llm_factory import LLMFactory


class InsightsState(TypedDict):
    transactions: List[Dict[str, Any]]
    goals: List[Dict[str, Any]]
    category_summary: Dict[str, float]
    total_income: float
    total_expenses: float
    savings_rate: float
    insights_report: str


def calculate_metrics_node(state: InsightsState) -> InsightsState:
    txs = state.get("transactions", [])
    goals = state.get("goals", [])

    category_sum: Dict[str, float] = {}
    income = 0.0
    expenses = 0.0

    for t in txs:
        amt = float(t.get("amount", 0.0))
        cat = t.get("category", "Uncategorized")

        if amt > 0:
            income += amt
        else:
            abs_amt = abs(amt)
            expenses += abs_amt
            category_sum[cat] = category_sum.get(cat, 0.0) + abs_amt

    savings = income - expenses
    savings_rate = (savings / income * 100) if income > 0 else 0.0

    state["category_summary"] = category_sum
    state["total_income"] = round(income, 2)
    state["total_expenses"] = round(expenses, 2)
    state["savings_rate"] = round(savings_rate, 2)
    return state


def generate_llm_insights_node(state: InsightsState) -> InsightsState:
    try:
        llm = LLMFactory.get_llm(temperature=0.3)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert personal financial advisor. Given the monthly financial breakdown, generate 3 clear, actionable bullet points analyzing spending behavior and progress toward financial goals."),
            ("user", "Income: ₹{income}\nExpenses: ₹{expenses}\nSavings Rate: {rate}%\nCategory Spend: {categories}\nUser Goals: {goals}")
        ])
        chain = prompt | llm
        
        res = chain.invoke({
            "income": state["total_income"],
            "expenses": state["total_expenses"],
            "rate": state["savings_rate"],
            "categories": str(state["category_summary"]),
            "goals": str(state.get("goals", []))
        })
        state["insights_report"] = str(res.content).strip()
    except Exception:
        state["insights_report"] = (
            f"Monthly Summary: Total Income: ₹{state['total_income']}, "
            f"Total Expenses: ₹{state['total_expenses']}, "
            f"Savings Rate: {state['savings_rate']}%."
        )

    return state


def build_insights_graph():
    workflow = StateGraph(InsightsState)

    workflow.add_node("metrics", calculate_metrics_node)
    workflow.add_node("generate_insights", generate_llm_insights_node)

    workflow.set_entry_point("metrics")
    workflow.add_edge("metrics", "generate_insights")
    workflow.add_edge("generate_insights", END)

    return workflow.compile()
