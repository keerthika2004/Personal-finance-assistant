import logging
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from backend.app.services.llm_factory import LLMFactory

logger = logging.getLogger(__name__)

class InsightsState(TypedDict):
    transactions: List[Dict[str, Any]]
    goals: List[Dict[str, Any]]
    category_summary: Dict[str, float]
    total_income: float
    total_expenses: float
    savings_rate: float
    insights_report: str
    goal_coaching: Dict[str, str]


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


from pydantic import BaseModel, Field

class InsightsResponse(BaseModel):
    general_insights: str = Field(description="3 clear actionable bullet points analyzing spending behavior and progress toward financial goals.")
    goal_advice: Dict[str, str] = Field(description="Dictionary mapping EXACT goal_name to a 1-sentence personalized actionable advice on how to reach that specific goal based on current spending categories.")

def generate_llm_insights_node(state: InsightsState) -> InsightsState:
    try:
        llm = LLMFactory.get_llm(temperature=0.3)
        structured_llm = llm.with_structured_output(InsightsResponse)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert personal financial advisor. Generate insights and specific goal advice based on the provided data."),
            ("user", "Income: ₹{income}\nExpenses: ₹{expenses}\nSavings Rate: {rate}%\nCategory Spend: {categories}\nUser Goals: {goals}")
        ])
        chain = prompt | structured_llm
        
        res = chain.invoke({
            "income": state["total_income"],
            "expenses": state["total_expenses"],
            "rate": state["savings_rate"],
            "categories": str(state["category_summary"]),
            "goals": str(state.get("goals", []))
        })
        
        if hasattr(res, 'general_insights'):
            state["insights_report"] = res.general_insights
            state["goal_coaching"] = res.goal_advice
        else:
            # Fallback if structured output fails
            state["insights_report"] = "Unable to generate detailed insights."
            state["goal_coaching"] = {}
            
    except Exception as e:
        logger.error(f"Insights Generation Error: {str(e)}")
        state["insights_report"] = f"Monthly Summary: Total Income: ₹{state['total_income']}, Total Expenses: ₹{state['total_expenses']}, Savings Rate: {state['savings_rate']}%. (Error: {str(e)})"
        state["goal_coaching"] = {}

    return state


def build_insights_graph():
    workflow = StateGraph(InsightsState)

    workflow.add_node("metrics", calculate_metrics_node)
    workflow.add_node("generate_insights", generate_llm_insights_node)

    workflow.set_entry_point("metrics")
    workflow.add_edge("metrics", "generate_insights")
    workflow.add_edge("generate_insights", END)

    return workflow.compile()

_INSIGHTS_GRAPH = None

def get_insights_graph():
    """Compile once and reuse."""
    global _INSIGHTS_GRAPH
    if _INSIGHTS_GRAPH is None:
        _INSIGHTS_GRAPH = build_insights_graph()
    return _INSIGHTS_GRAPH
