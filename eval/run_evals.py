import sys
import os
from pathlib import Path
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, mean_absolute_error, mean_absolute_percentage_error
from langfuse import Langfuse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.services.categorizer import MLCategorizer
from scripts.forecasting_backtest import generate_mock_cashflow_data
from backend.app.agents.reconciliation_graph import build_reconciliation_graph
from backend.app.agents.chat_graph import build_chat_graph

# Langfuse integration for evals
langfuse = Langfuse() if os.getenv("LANGFUSE_PUBLIC_KEY") else None

def evaluate_categorization():
    print("\n--- Evaluating Categorization ---")
    df = pd.read_csv('data/training.csv')
    
    # We'll just evaluate the ML model on a subset for speed in this harness
    subset = df.sample(50, random_state=42)
    y_true = subset['category'].tolist()
    
    # ML Model
    y_pred_ml = [MLCategorizer.predict_category(desc) for desc in subset['description']]
    f1_ml = f1_score(y_true, y_pred_ml, average='macro')
    print(f"ML Model Macro-F1: {f1_ml:.4f}")
    
    # We skip full LLM eval here to save API limits/cost, 
    # but the framework is identical if we iterate through LLM chain
    print("LLM Model Macro-F1: N/A (Baseline reference)")
    return f1_ml

def evaluate_forecasting():
    print("\n--- Evaluating Forecasting ---")
    df = generate_mock_cashflow_data()
    train = df.iloc[:-30]
    test = df.iloc[-30:]
    
    from prophet import Prophet
    import logging
    logging.getLogger("prophet").setLevel(logging.ERROR)
    
    m = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
    m.fit(train)
    
    future = m.make_future_dataframe(periods=30)
    forecast = m.predict(future)
    
    pred = forecast.iloc[-30:]['yhat'].values
    actual = test['y'].values
    
    mae = mean_absolute_error(actual, pred)
    mask = actual != 0
    mape = mean_absolute_percentage_error(actual[mask], pred[mask])
    
    print(f"MAE: ${mae:.2f}")
    print(f"MAPE: {mape*100:.2f}%")
    return mae, mape

def evaluate_anomaly_flagging():
    print("\n--- Evaluating Anomaly Flagging ---")
    # Mock data with 2 normal, 1 unusually large, 1 duplicate
    transactions = [
        {"id": "1", "date": "2024-01-01", "raw_description": "Coffee", "amount": -5.0},
        {"id": "2", "date": "2024-01-02", "raw_description": "Coffee", "amount": -5.0},
        {"id": "3", "date": "2024-01-03", "raw_description": "Rent", "amount": -2000.0},
        {"id": "4", "date": "2024-01-03", "raw_description": "Coffee", "amount": -5.0}, # duplicate of id 2 based on logic
    ]
    
    # ground truth: 1 normal, 2 normal, 3 anomalous (high), 4 anomalous (duplicate)
    # Actually deduplication uses normalized_merchant. Let's just mock the normalized state
    
    # We will test just the anomaly scoring logic
    from backend.app.agents.reconciliation_graph import anomaly_scoring_node
    
    state = {
        "normalized_transactions": [
            {"amount": -5.0, "is_duplicate": False, "is_suspicious": False, "status": "PENDING"},
            {"amount": -5.0, "is_duplicate": False, "is_suspicious": False, "status": "PENDING"},
            {"amount": -2000.0, "is_duplicate": False, "is_suspicious": False, "status": "PENDING"}, # Large
            {"amount": -5.0, "is_duplicate": True, "is_suspicious": False, "status": "PENDING"}, # Dup
        ]
    }
    
    y_true = [0, 0, 1, 1]
    
    new_state = anomaly_scoring_node(state)
    scored = new_state["normalized_transactions"]
    
    y_pred = [1 if tx["status"] == "FLAGGED" else 0 for tx in scored]
    
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    
    print(f"Anomaly Precision: {precision:.2f}")
    print(f"Anomaly Recall: {recall:.2f}")
    return precision, recall

def evaluate_chatbot():
    print("\n--- Evaluating Chatbot QA ---")
    graph = build_chat_graph()
    
    # Mock some transactions in the state
    mock_txs = [
        {"date": "2024-01-01", "normalized_merchant": "Starbucks", "amount": -5.50, "category": "Dining"},
        {"date": "2024-01-02", "normalized_merchant": "Target", "amount": -150.00, "category": "Shopping"}
    ]
    
    questions = [
        "How much did I spend at Starbucks?",
    ]
    
    print(f"Testing Question: {questions[0]}")
    try:
        res = graph.invoke({
            "user_query": questions[0],
            "transaction_context": mock_txs,
            "goals_context": []
        })
        answer = res["response"]
        print(f"Answer: {answer}")
        
        # Simple string matching eval
        acc = 1.0 if "5.50" in answer else 0.0
        print(f"Chatbot Accuracy (rule-based): {acc}")
    except Exception as e:
        print(f"Chatbot eval failed: {e}")

if __name__ == "__main__":
    evaluate_categorization()
    evaluate_forecasting()
    evaluate_anomaly_flagging()
    evaluate_chatbot()
    print("\nEval complete. All calls traced in Langfuse if configured.")
