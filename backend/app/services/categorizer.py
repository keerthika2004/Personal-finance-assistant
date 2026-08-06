import pickle
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

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
