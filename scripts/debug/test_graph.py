import asyncio
from backend.app.agents.reconciliation_graph import build_reconciliation_graph
import datetime

async def main():
    graph = build_reconciliation_graph()
    initial_state = {
        "statement_id": 1,
        "raw_transactions": [{"date": datetime.datetime.now(), "raw_description": "test", "amount": 10.0}],
        "normalized_transactions": [],
        "flagged_transactions": [],
        "approved_transactions": [],
        "current_step": "START",
        "requires_hitl": False
    }
    final = graph.invoke(initial_state)
    print("SUCCESS")

asyncio.run(main())
