import sys
import os
from pathlib import Path
import time
import statistics

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
from sklearn.pipeline import Pipeline, FeatureUnion
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
    train_df = pd.read_csv("data/training.csv")
    test_path = Path("data/test.csv")
    if test_path.exists():
        test_df = pd.read_csv(test_path)
        X_train, y_train = train_df["description"], train_df["category"]
        X_test, y_test = test_df["description"], test_df["category"]
        print(f"Held-out test set: data/test.csv (n={len(test_df)})")
    else:
        print("data/test.csv not found - falling back to a split of training.csv")
        X_train, X_test, y_train, y_test = train_test_split(
            train_df["description"], train_df["category"], test_size=0.25, random_state=42, stratify=train_df["category"],
        )
        
    
    model = Pipeline([
        ('features', FeatureUnion([
            ('word', TfidfVectorizer(analyzer='word', ngram_range=(1,2))),('char', TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5))),
        ])),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000))
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

    llm_f1 = evaluate_llm_categorization(list(X_test), list(y_test))
    print ("\n== Categorization summary ==")
    print(f"Local ML Macro-F1: {f1: .4f}")
    print (f"LLM Macro-F1: {llm_f1 if llm_f1 is not None else 'skipped (no GROQ key)'}")
    return f1, llm_f1
   
    
def evaluate_llm_categorization(descriptions, truths, sample_cap=40):
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

def evaluate_hybrid_categorization():
    """Runs the production categorizer path over the held-out set of unseen merchants:
    PII redaction -> keyword rules -> shipped categorizer.pkl (0.35 confidence threshold) -> LLM fallback"""
    print("\n--- Evaluating Hybrid Categorizer (production path, held-out set) ---")
    from backend.app.services.categorizer import MLCategorizer, normalize_category
    from backend.app.services.pii_redactor import PIIRedactor

    test_df = pd.read_csv("data/test.csv")
    descs = [PIIRedactor.redact(d) for d in test_df["description"]]
    truths = list(test_df["category"])
    n = len(descs)

    #Warm-up call loads the pickle so it isn't counted in latency
    MLCategorizer.predict_category(descs[0])

    local_preds, latencies_ms = [], []
    for d in descs:
        start = time.perf_counter()
        local_preds.append(normalize_category(MLCategorizer.predict_category(d)))
        latencies_ms.append(1000*(time.perf_counter() - start))
    #same rule as normalize_and_categorize_node: "Uncategorized" from the local path triggers the LLM
    fallback = {i for i, p in enumerate(local_preds) if p == "Uncategorized"}
    handled = [i for i in range(n) if i not in fallback]
    
    print(f"n={n} handled locally: {len(handled)} sent to LLM: {len(fallback)}")
    print(f"LLM calls avoided vs LLM-only: {len(handled)/n*100:.1f}%")
    print(f"Local latency per call: median {statistics.median(latencies_ms):.3f} ms, p95={np.percentile(latencies_ms,95):.3f} ms")
    if handled:
        acc = sum(local_preds[i] == truths[i] for i in handled)/len(handled)
        print(f"Accuracy on locally-handled rows: {acc:.4f}")
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
        print("Hybrid Macro-F1: skipped (no GROQ key)")
        return
    
    from backend.app.agents.reconciliation_graph import build_normalizer_chain, _llm_normalize
    chain = build_normalizer_chain()
    hybrid_preds = list(local_preds)
    for i in sorted(fallback):
        _, hybrid_preds[i] = _llm_normalize(chain, descs[i])
    hybrid_f1 = f1_score(truths, hybrid_preds, average="macro", labels=CATEGORIES, zero_division=0)
    print(f"Hybrid Macro F1 (all {n} rows): {hybrid_f1:.4f}")


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


# Fixed dataset for the chat eval. Expected answers below were worked out by hand from this table,
# not computed with the same pandas code the tools use.
CHAT_EVAL_TXS = [
   {"date": "2024-01-01", "normalized_merchant": "Acme Corp Salary", "amount": 50000.00, "category": "Income"},
   {"date": "2024-01-03", "normalized_merchant": "Swiggy", "amount": -450.00, "category": "Dining"},
   {"date": "2024-01-05", "normalized_merchant": "BigBasket", "amount": -2200.00, "category": "Groceries"},
   {"date": "2024-01-08", "normalized_merchant": "Uber", "amount": -300.00, "category": "Transportation"},
   {"date": "2024-01-10", "normalized_merchant": "Netflix", "amount": -649.00, "category": "Subscriptions"},
   {"date": "2024-01-15", "normalized_merchant": "Landlord Rent", "amount": -15000.00, "category": "Housing"},
   {"date": "2024-01-20", "normalized_merchant": "Swiggy", "amount": -550.00, "category": "Dining"},
   {"date": "2024-01-25", "normalized_merchant": "Amazon", "amount": -3200.00, "category": "Shopping"},
   {"date": "2024-02-01", "normalized_merchant": "Acme Corp Salary", "amount": 50000.00, "category": "Income"},
   {"date": "2024-02-04", "normalized_merchant": "Zomato", "amount": -800.00, "category": "Dining"},
   {"date": "2024-02-07", "normalized_merchant": "BigBasket", "amount": -1800.00, "category": "Groceries"},
   {"date": "2024-02-10", "normalized_merchant": "Netflix", "amount": -649.00, "category": "Subscriptions"},
   {"date": "2024-02-12", "normalized_merchant": "Uber", "amount": -250.00, "category": "Transportation"},
   {"date": "2024-02-15", "normalized_merchant": "Landlord Rent", "amount": -15000.00, "category": "Housing"},
   {"date": "2024-02-18", "normalized_merchant": "Apollo Pharmacy", "amount": -1200.00, "category": "Healthcare"},
   {"date": "2024-02-22", "normalized_merchant": "Freelance Project", "amount": 12000.00, "category": "Income"},
   {"date": "2024-03-01", "normalized_merchant": "Acme Corp Salary", "amount": 50000.00, "category": "Income"},
   {"date": "2024-03-03", "normalized_merchant": "Swiggy", "amount": -700.00, "category": "Dining"},
   {"date": "2024-03-06", "normalized_merchant": "BigBasket", "amount": -2500.00, "category": "Groceries"},
   {"date": "2024-03-10", "normalized_merchant": "Netflix", "amount": -649.00, "category": "Subscriptions"},
   {"date": "2024-03-15", "normalized_merchant": "Landlord Rent", "amount": -15000.00, "category": "Housing"},
   {"date": "2024-03-20", "normalized_merchant": "Amazon", "amount": -5400.00, "category": "Shopping"},
   {"date": "2024-03-25", "normalized_merchant": "BESCOM Electricity", "amount": -1850.00, "category": "Utilities"},
   {"date": "2024-03-28", "normalized_merchant": "Uber", "amount": -420.00, "category": "Transportation"},
]
CHAT_EVAL_GOALS = [
   {"goal_name": "Emergency Fund", "target_amount": 100000.0, "current_amount": 25000.0},
   {"goal_name": "Goa Trip", "target_amount": 30000.0, "current_amount": 8000.0},
]
# Every expected item must appear in the answer. Numbers are matched numerically, words as substrings.
# Only single-tool questions: anything needing the LLM to add/subtract results is excluded on purpose.
CHAT_EVAL_CASES = [
   # Spending totals
   ("How much did I spend in total?", ["68567"]),
   ("How much have I spent on Dining overall?", ["2500"]),
   ("What's my total Groceries spending?", ["6500"]),
   ("How much did I spend on Transportation?", ["970"]),
   ("How much went to Subscriptions?", ["1947"]),
   ("How much have I spent on Housing?", ["45000"]),
   ("What's my total Shopping spend?", ["8600"]),
   ("How much did I spend on Healthcare?", ["1200"]),
   ("How much did I spend on Utilities?", ["1850"]),
   ("How much did I spend at Swiggy?", ["1700"]),
   ("How much have I spent on Uber?", ["970"]),
   ("How much did I spend at Amazon?", ["8600"]),
   ("How much have I paid Netflix in total?", ["1947"]),
   ("How much did I spend at BigBasket?", ["6500"]),
   ("How much did I spend at Zomato?", ["800"]),
   ("How much did I spend at Apollo Pharmacy?", ["1200"]),
   # Date-scoped spending
   ("What was my total spending in January 2024?", ["22349"]),
   ("What was my total spending in February 2024?", ["19699"]),
   ("What was my total spending in March 2024?", ["26519"]),
   ("How much did I spend on Dining in January 2024?", ["1000"]),
   ("How much did I spend on Groceries in March 2024?", ["2500"]),
   ("How much did I spend on Shopping in March 2024?", ["5400"]),
   ("How much did I spend at Swiggy in March 2024?", ["700"]),
   ("How much did I spend between 2024-01-01 and 2024-01-15?", ["18599"]),
   ("How much did I spend on Transportation in February 2024?", ["250"]),
   # Income
   ("What is my total income?", ["162000"]),
   ("How much income did I receive in February 2024?", ["62000"]),
   ("How much income did I receive in January 2024?", ["50000"]),
   ("How much income did I get in March 2024?", ["50000"]),
   ("How much income did I receive between 2024-02-10 and 2024-02-28?", ["12000"]),
   # Counts
   ("How many transactions do I have?", ["24"]),
   ("How many Dining transactions do I have?", ["4"]),
   ("How many times did I order from Swiggy?", ["3"]),
   ("How many transactions did I make in February 2024?", ["8"]),
   ("How many Uber rides did I take?", ["3"]),
   ("How many income transactions do I have?", ["4"]),
   ("How many Shopping transactions do I have?", ["2"]),
   # Largest / top-N
   ("What was my single largest expense?", ["15000"]),
   ("What was my largest Shopping expense?", ["5400"]),
   ("What are my top 2 Shopping expenses?", ["5400", "3200"]),
   ("What are my top 3 Groceries expenses?", ["2500", "2200", "1800"]),
   ("What was my largest Dining expense?", ["800"]),
   ("What was my largest income transaction?", ["50000"]),
   ("What was my largest Transportation expense?", ["420"]),
   ("What are my top 2 Dining expenses?", ["800", "700"]),
   # Breakdowns
   ("Give me my spending breakdown by category for February 2024.", ["15000", "1800", "1200", "800", "649", "250"]),
   ("Give me my spending breakdown by category for March 2024.", ["15000", "5400", "2500", "1850", "700", "649", "420"]),
   ("Which category did I spend the most on overall?", ["Housing"]),
   # Goals
   ("How much have I saved toward my Emergency Fund goal?", ["25000"]),
   ("What is the target amount for my Goa Trip goal?", ["30000"]),
]


def _expected_hit(expected, ans):
   try:
       float(expected)
   except ValueError:
       return expected.lower() in ans.lower()
   return _numeric_hit(expected, ans)


def evaluate_chatbot(pause_s=2.0):
   print(f"\n--- Evaluating Chatbot QA (tool-calling agent, {len(CHAT_EVAL_CASES)} hand-labelled questions) ---")
   if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
       print("Skipped (no GROQ key)")
       return
   from datetime import date
   from langchain_core.messages import HumanMessage
   from backend.app.agents.chat_graph import build_chat_agent, SYSTEM_TEMPLATE
   from backend.app.agents.finance_tools import build_finance_tools

   # Same system prompt as the /chat endpoint
   agent = build_chat_agent(
       build_finance_tools(CHAT_EVAL_TXS, CHAT_EVAL_GOALS),
       SYSTEM_TEMPLATE.format(today=date.today().isoformat()),
   )

   correct, errors = 0, 0
   for q, expected in CHAT_EVAL_CASES:
       try:
           res = agent.invoke({"messages": [HumanMessage(content=q)]}, config={"recursion_limit": 8})
           ans = res["messages"][-1].content or ""
           hit = all(_expected_hit(e, ans) for e in expected)
           correct += hit
           print(f"[{'PASS' if hit else 'FAIL'}] {q} (expected {', '.join(expected)})\n   -> {ans[:200]}")
       except Exception as e:
           errors += 1
           print(f"[ERROR] {q} {type(e).__name__}: {e}")
       time.sleep(pause_s)  # stay under Groq's free-tier rate limit
   print(f"Chatbot accuracy: {correct}/{len(CHAT_EVAL_CASES)} (errors: {errors})")
 


if __name__ == "__main__":
   evaluate_categorization()
   evaluate_hybrid_categorization()
   evaluate_forecasting()
   evaluate_anomaly_flagging()
   evaluate_chatbot()
   print("\nEval complete. All calls traced in Langfuse if configured.")
