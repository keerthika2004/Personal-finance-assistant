import pickle
from pathlib import Path
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Intelligent Keyword Heuristic Mapping for instant categorization
KEYWORD_MAPPINGS: Dict[str, str] = {
    # Dining & Food
    "dining": "Dining",
    "food": "Dining",
    "starbucks": "Dining",
    "mcdonalds": "Dining",
    "mcdonald": "Dining",
    "swiggy": "Dining",
    "zomato": "Dining",
    "cafe": "Dining",
    "burger": "Dining",
    "pizza": "Dining",
    "kfc": "Dining",
    "dominos": "Dining",
    "subway": "Dining",
    "restaurant": "Dining",
    "tea": "Dining",

    # Groceries
    "groceries": "Groceries",
    "grocery": "Groceries",
    "zepto": "Groceries",
    "blinkit": "Groceries",
    "instamart": "Groceries",
    "supermarket": "Groceries",
    "bigbasket": "Groceries",
    "candy": "Groceries",
    "milk": "Groceries",
    "nature basket": "Groceries",

    # Shopping
    "shopping": "Shopping",
    "nykaa": "Online Shopping",
    "amazon": "Online Shopping",
    "flipkart": "Online Shopping",
    "myntra": "Online Shopping",
    "zara": "Shopping",
    "h&m": "Shopping",
    "ajio": "Online Shopping",
    "clothes": "Shopping",

    # Income & Earnings
    "salary": "Income",
    "paycheck": "Income",
    "payroll": "Income",
    "cashback": "Income",
    "dividend": "Income",
    "interest": "Income",

    # Transfer & Peer-to-Peer
    "friend": "Transfer",
    "friend transfer": "Transfer",
    "transfer": "Transfer",
    "gpay transfer": "Transfer",
    "phonepe": "Transfer",

    # Transportation & Travel
    "transportation": "Transportation",
    "uber": "Transportation",
    "ola": "Transportation",
    "rapido": "Transportation",
    "cab": "Transportation",
    "petrol": "Transportation",
    "fuel": "Transportation",
    "metro": "Transportation",
    "auto": "Transportation",
    "taxi": "Transportation",

    # Subscriptions & Fitness
    "subscriptions": "Subscriptions",
    "netflix": "Subscriptions",
    "spotify": "Subscriptions",
    "prime": "Subscriptions",
    "youtube": "Subscriptions",
    "hotstar": "Subscriptions",
    "gym": "Subscriptions",
    "cult fit": "Subscriptions",

    # Utilities
    "utilities": "Utilities",
    "electricity": "Utilities",
    "water bill": "Utilities",
    "gas bill": "Utilities",
    "wifi": "Utilities",
    "broadband": "Utilities",
    "jio": "Utilities",
    "airtel": "Utilities",
}


class MLCategorizer:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            model_path = Path(__file__).parent.parent / "models" / "categorizer.pkl"
            if not model_path.exists():
                logger.warning(f"ML categorizer model not found at {model_path}. Fallback to LLM required.")
                return None
            try:
                with open(model_path, "rb") as f:
                    cls._model = pickle.load(f)
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                return None
        return cls._model

    @classmethod
    def predict_category(cls, description: str) -> str:
        if not description:
            return "Uncategorized"

        desc_lower = description.strip().lower()

        # 1. Check direct keyword heuristic dictionary
        for kw, cat in KEYWORD_MAPPINGS.items():
            if kw in desc_lower:
                return cat

        # 2. Check Scikit-Learn TF-IDF + Logistic Regression Model
        model = cls.get_model()
        if not model:
            return "Uncategorized"

        try:
            tfidf = model.named_steps['tfidf']
            clf = model.named_steps['clf']
            
            vec = tfidf.transform([description])
            if vec.nnz == 0:
                # Completely out of vocabulary
                return "Uncategorized"
                
            probs = clf.predict_proba(vec)[0]
            if max(probs) < 0.35: # Low confidence threshold
                return "Uncategorized"
                
            return clf.predict(vec)[0]
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return "Uncategorized"
