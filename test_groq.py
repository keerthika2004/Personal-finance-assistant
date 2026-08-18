import sys
import os
import logging
logging.basicConfig(level=logging.ERROR)
sys.path.append("/Users/keerthika/Desktop/Personal finance analyzer")

from backend.app.agents.insights_graph import InsightsState, generate_llm_insights_node
from dotenv import load_dotenv

load_dotenv("/Users/keerthika/Desktop/Personal finance analyzer/backend/.env")

state = {
    "transactions": [],
    "goals": [],
    "category_summary": {"Groceries": 100},
    "total_income": 1000,
    "total_expenses": 100,
    "savings_rate": 90,
    "insights_report": "",
    "goal_coaching": {}
}

try:
    state = generate_llm_insights_node(state)
    print("Report:", state["insights_report"])
except Exception as e:
    print("Error:", e)
