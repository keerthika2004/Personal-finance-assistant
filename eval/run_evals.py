import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / "backend" / ".env")



import pandas as pd
import numpy as np
from sklearn.metrics import (f1_score, accuracy_score, classification_report, confusion_matrix, precision_score, recall_score, mean_absolute_error,)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

from backend.app.services.anomaly_detector import HybridAnomalyDetector
from scripts.forecasting_backtest import generate_mock_cashflow_data

CATEGORIES = [
    "Groceries", "Dining", "Transportation", "Utilities", "Shopping", "Entertainment", "Income", "Transfer", "Healthcare", "Subscriptions", "Housing", "Uncategorized",
]

# Metricc helpers (honest forecasting metrics)
def smape(actual, pred):
    """Symmetric MAPE - bounded 0-200%, safe when values cross zero."""
    actual, pred = np.asarray(actual, float), np.asarray(pred, float)
    denom = np.abs(actual) + np.abs(pred)
    mask = denom != 0
    return float(np.mean(2*np.abs(pred-actual)[mask]/denom[mask])*100)

def mase(actual, pred, train_series, m=7):
    """Mean Absolute Scaled Error vs a Seasonal-naive baseline.
    MASE < 1 => the model beats 'just repeat last week'. > 1 => it's worse."""
    actual,pred = np.asarray(actual, float),np.asarray(pred, float)
    train = np.asarray(train_series,float)
    scale = np.mean(np.abs(train[m:] - train[:-m]))
    if scale == 0:
        return float("nan")
    return float(np.mean(np.abs(actual - pred))/ scale)

def evaluate_categorization():
    print("\n--- Evaluating Categorization (held-out test set) ---")
    df = pd.read_csv("data/training.csv")
    X_train, X_test, y_train, y_test = train_test_split(
        df["description"], df["category"],
        test_size=0.25, random_state=42, stratify=df["category"],
    )
    model = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
("clf", LogisticRegression(class_weight="balanced", max_iter=1000)),
    ])
    model.fit(X_train, y_train) # ‹-- trained ONLY on the train split
    y_pred = model.predict(X_test)
    acc= accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")
    print(f"TF-IDF+LogReg Accuracy: {acc:.4f}")
    print(f"Macro-F1: {f1:.4f}")
    print ("\nPer-class report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    labels = sorted(y_test.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    print("Confusion matrix (rows-true, cols-pred):")
    print("labels:", labels)
    print(cm)
    llm_f1 = evaluate_11m_categorization(list(X_test), list(y_test))
    print ("\n== Categorization summary ==")
    print(f"Local ML Macro-F1: {f1: .4f}")
    print (f"LLM Macro-F1: {llm_f1 if llm_f1 is not None else 'skipped (no GROQ key)'}")
    return f1, llm_f1
   
    
def evaluate_11m_categorization(descriptions, truths, sample_cap=40):
    """Fills in the LLM baseline the old harness skipped. Capped for cost."""
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
        return None
    try:
        from pydantic import BaseModel, Field
        from backend.app.services.llm_factory import LLMFactory 
        from langchain_core.prompts import ChatPromptTemplate
        class CategoryPrediction(BaseModel):
            category: str = Field(description=f"Exactly one of: {', '.join(CATEGORIES)}")
        llm = LLMFactory.get_llm(temperature=0.0).with_structured_output(CategoryPrediction)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a transaction categorizer. Assign exactly one category "
                    f"from this list: {', '.join(CATEGORIES)}."),
            ("user", "Transaction description: {desc}"),
        ])
        chain = prompt | llm
        n = min(sample_cap, len(descriptions))
        preds = []
        for desc in descriptions[:n]:
            try:
                out = chain.invoke({"desc": desc})
                preds.append(out.category if out.category in CATEGORIES else "Uncategorized")
            except Exception:
                preds.append ("Uncategorized")
        return round(f1_score(truths[:n], preds, average="macro", labels=CATEGORIES), 4)
    except Exception as e:
        print(f"LLM categorization eval failed: {e}")
        return None

def evaluate_forecasting():
    print("\n--- Evaluating Forecasting ---")
    try:
        from prophet import Prophet # type: ignore
        import logging
        logging.getLogger("prophet").setLevel(logging.ERROR)
        df = generate_mock_cashflow_data()
        train = df.iloc[:-30]
        test = df.iloc[-30:]
        
        m = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
        m.fit(train)
        forecast = m.predict(m.make_future_dataframe(periods=30))
        pred = forecast.iloc[-30:]["yhat"].values
        actual = test['y'].values
        
        model_mae = mean_absolute_error(actual, pred)
        model_smape = smape(actual,pred)
        model_mase = mase(actual,pred, train["y"].values, m=7)
        
        #seasonal-naive baseline: "next week looks like last week"
        # naive_pred = train["y"].values[-30:]
        # naive_mae = mean_absolute_error(actual, naive_pred)
        n = len(df)
        naive_pred = df["y"].values[n-37:n-7] # the 7-days prior values aligned to the test window
        naive_mae = mean_absolute_error(actual, naive_pred)
        
        print(f"Prophet MAE: ${model_mae: .2f} SMAPE: {model_smape:.1f}% MASE: {model_mase:.2f}")
        print(f"Naive MAE: ${naive_mae:.2f}")
        print(f"=> Prophet is {'BETTER' if model_mase < 1 else 'WORSE'} than seasonal_naive (MASE {model_mase:.2f})")
        print("Note: MAPE dropped - it's meaningless here (series crosses zero). SMAPE/MASE are honest.")
        return model_mae, model_smape, model_mase
    except ImportError:
        print("Prophet not installed. Skipping.")
        return None, None, None

def make_labeled_anomaly_set(seed=42):
    rng = np.random.default_rng(seed)
    txs, labels = [], []
    #Normal transactions around per-category medians -> label 0
    medians = {"Dining": 400, "Groceries": 800, "Transportation": 200, "Shopping": 1500}
    for cat, med in medians.items():
        for _ in range(10):
            txs.append({"amount": -round(float(rng.normal(med, med*0.15)), 2),
            "category": cat, "is_duplicate": False, "is_suspicious": False, "status": "PENDING"})
            labels.append(0)
    # Injected anomalies: large spikes (>2x median AND >2000) -> label 1
    for cat,med in medians.items():
        for _ in range(2):
            txs.append({"amount": -round(float(med * rng.uniform(6,12)), 2), "category": cat, "is_duplicate": False, "is_suspicious": False, "status": "PENDING"})
            labels.append(1)
    return txs, labels

def evaluate_anomaly_flagging():
    print("\n--- Evaluating Anomaly Flagging (synthetic labeled set) ---")
    txs, y_true = make_labeled_anomaly_set()
    scored = HybridAnomalyDetector.detect_and_score([dict(t) for t in txs])
    y_pred = [1 if t["status"] == "FLAGGED" else 0 for t in scored]

    print(f"n={len(y_true)} positives(true)={sum(y_true)}")
    print(f"Precision: {precision_score(y_true, y_pred, zero_division=0):.2f}   "
    f"Recall: {recall_score(y_true, y_pred, zero_division=0):.2f}   "
    f"F1: {f1_score(y_true, y_pred, zero_division=0):.2f}")
    print(confusion_matrix(y_true, y_pred))
    print("Note: SYNTHETIC data. Replace with hand-labeled real transactions for a defensible number.")

import re
def _numeric_hit(expected, ans):
    """True if expected's numeric value appears in ans, ignoring $, commas, trailing zeroes."""
    target = float(expected)
    for token in re.findall(r"-?\d[\d,]*\.?\d*", ans):
        try:
            if abs(float(token.replace(",","")) - target) < 0.01:
                return True
        except ValueError:
            continue
    return False 

def evaluate_chatbot():
    print("\n--- Evaluating Chatbot QA (tool-calling agent) ---")
    from datetime import date
    from langchain_core.messages import HumanMessage
    from backend.app.agents.chat_graph import build_chat_agent
    from backend.app.agents.finance_tools import build_finance_tools

    txs = [
        {"date": "2024-01-01", "normalized_merchant": "Starbucks", "amount": -5.50, "category": "Dining"},
        {"date": "2024-01-01", "normalized_merchant": "Starbucks", "amount": -4.50, "category": "Dining"},
        {"date": "2024-01-02", "normalized_merchant": "Target", "amount": -150.00, "category": "Shopping"}
    ]

    agent = build_chat_agent(
        build_finance_tools(txs, []),
        f"You are a precise finance assistant. Today is {date.today().isoformat()}. "
        f"Always call a tool for exact numbers; never invent numbers.",
    )

    cases = [
        ("How much did I spend at Starbucks in total?", "10.00"),
        ("What was my single largest expense?", "150.00"),
        ("How many transactions do I have?", "3"),
    ]
    correct = 0
    for q, expected in cases:
        try:
            res = agent.invoke({"messages": [HumanMessage(content=q)]})
            ans = res["messages"][-1].content
            hit = _numeric_hit(expected, ans)
            correct += hit
            print(f"[{'PASS' if hit else 'FAIL'}] {q} (expected {expected})\n   -> {ans[:160]}")
        except Exception as e:
            print(f"[{'ERROR'}] {q} {e}")
    print(f"Chatbot accuracy: {correct}/{len(cases)}")

if __name__ == "__main__":
    evaluate_categorization()
    evaluate_forecasting()
    evaluate_anomaly_flagging()
    evaluate_chatbot()
    print("\nEval complete. All calls traced in Langfuse if configured.")
