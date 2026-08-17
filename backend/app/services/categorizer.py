import pickle
from pathlib import Path
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

#The one canonical taxonomy for the whole app.
CATEGORIES = [
    "Groceries", "Dining", "Transportation", "Utilities", "Shopping", "Entertainment", "Income", "Transfer", "Healthcare", "Subscriptions", "Housing", "Uncategorized",
]

#Map legacy / near-miss labels onto the canonical set.
_CATEGORY_ALIASES = {"online shopping": "Shopping"}

def normalize_category(cat: str) -> str:
    """Force any category string into the canonical taxonomy. Unknown -> 'Uncategorized'."""
    if not cat:
        return "Uncategorized"
    c = cat.strip()
    if c in CATEGORIES:
        return c
    return _CATEGORY_ALIASES.get(c.lower(), "Uncategorized")

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
    "nykaa": "Shopping",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",
    "zara": "Shopping",
    "h&m": "Shopping",
    "ajio": "Shopping",
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
            #Full pipeline: word + char n-gram features -> classifier
            probs = model.predict_proba([description])[0]
            if max(probs)<0.35:
                return "Uncategorized"
            return model.predict([description])[0]
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return "Uncategorized"
