import numpy as np
from typing import List, Dict, Any
from sklearn.ensemble import IsolationForest
import logging

logger = logging.getLogger(__name__)

class HybridAnomalyDetector:
    """Hybrid Machine Learning Anomaly Detection Service for Financial Transactions.
    
    Combines Scikit-Learn's unsupervised Isolation Forest algorithm with robust
    category Median & Interquartile Range (IQR) Z-Score profiling to prevent outlier skewing.
    """

    @classmethod
    def detect_and_score(cls, transactions: List[Dict[str, Any]], historical_txs: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not transactions:
            return transactions

        all_pool = (historical_txs or []) + transactions

        # Extract amounts per category
        cat_amounts: Dict[str, List[float]] = {}
        for tx in all_pool:
            cat = tx.get("category", "Uncategorized")
            amt = abs(float(tx.get("amount", 0.0)))
            if cat not in cat_amounts:
                cat_amounts[cat] = []
            cat_amounts[cat].append(amt)

        # Compute robust Median & IQR stats per category (immune to outlier skewing)
        cat_stats = {}
        for cat, val_list in cat_amounts.items():
            arr = np.array(val_list)
            med_val = float(np.median(arr))
            q75, q25 = np.percentile(arr, [75, 25])
            iqr_val = float(q75 - q25)
            cat_stats[cat] = {
                "median": med_val,
                "iqr": iqr_val if iqr_val > 0 else (med_val * 0.2 + 1.0),
                "count": len(arr)
            }

        # Build feature matrix X for Isolation Forest
        feature_rows = []
        for tx in all_pool:
            amt = abs(float(tx.get("amount", 0.0)))
            cat = tx.get("category", "Uncategorized")
            log_amt = np.log1p(amt)

            stats = cat_stats.get(cat, {"median": amt, "iqr": 1.0})
            med_val = stats["median"]
            iqr_val = stats["iqr"]
            
            z_score = abs(amt - med_val) / iqr_val
            cat_code = float(hash(cat) % 100)

            feature_rows.append([log_amt, cat_code, z_score])

        X = np.array(feature_rows)

        # Train Isolation Forest on combined pool
        iso_scores = np.zeros(len(all_pool))
        if len(all_pool) >= 3:
            try:
                iso_forest = IsolationForest(
                    n_estimators=100,
                    max_samples=min(256, len(all_pool)),
                    contamination=0.10,
                    random_state=42
                )
                iso_forest.fit(X)
                raw_scores = iso_forest.score_samples(X)
                min_s, max_s = np.min(raw_scores), np.max(raw_scores)
                if max_s > min_s:
                    iso_scores = ((max_s - raw_scores) / (max_s - min_s)) * 100.0
            except Exception as e:
                logger.warning("Isolation Forest fit warning: %s", e)

        # Slice scores back to incoming batch
        batch_offset = len(historical_txs or [])

        for idx, tx in enumerate(transactions):
            amt = abs(float(tx.get("amount", 0.0)))
            cat = tx.get("category", "Uncategorized")
            is_dup = tx.get("is_duplicate", False)

            stats = cat_stats.get(cat, {"median": amt, "iqr": 1.0})
            med_val = stats["median"]
            iqr_val = stats["iqr"]
            z_score = abs(amt - med_val) / iqr_val

            iso_score = iso_scores[batch_offset + idx]
            reasons = []
            score_penalty = 0.0

            # 1. Duplicate check
            if is_dup:
                score_penalty += 45.0
                reasons.append("Identified as duplicate transaction across accounts")

            # 2. Uncategorized check (Needs manual review in HITL Queue)
            if cat == "Uncategorized":
                score_penalty += 35.0
                reasons.append("Uncategorized transaction requires manual review")

            # 3. Category Median Spike Check (> 2.0x median or z_score > 2.0)
            if med_val > 0 and amt > (2.0 * med_val) and amt > 2000:
                multiple = amt / med_val
                score_penalty += min(60.0, multiple * 15.0)
                reasons.append(f"Amount (₹{amt:,.2f}) is {multiple:.1f}x higher than your median {cat} expense (₹{med_val:,.2f})")
            elif z_score > 2.0 and amt > 2000:
                score_penalty += 35.0
                reasons.append(f"Statistically unusual amount for category '{cat}'")

            # 4. Absolute high value threshold for daily expenses (> ₹8,000 for Dining/Groceries/Shopping)
            if cat in ["Dining", "Groceries", "Shopping", "Online Shopping"] and amt >= 8000:
                score_penalty += 40.0
                if f"Amount (₹{amt:,.2f})" not in str(reasons):
                    reasons.append(f"Unusually high individual expense of ₹{amt:,.2f} in category '{cat}'")

            # 5. Isolation Forest ML Anomaly Score
            if iso_score > 60.0 and amt > 1000:
                reasons.append(f"Isolation Forest ML Anomaly Score: {iso_score:.1f}%")

            composite_score = min(100.0, (iso_score * 0.25) + score_penalty)
            tx["anomaly_score"] = round(composite_score, 1)

            if composite_score >= 40.0 or is_dup or cat == "Uncategorized":
                tx["is_suspicious"] = True
                tx["anomaly_reason"] = " • ".join(reasons) if reasons else "Multi-feature anomaly detected by ML model"
                tx["status"] = "FLAGGED"
            else:
                tx["is_suspicious"] = False
                tx["anomaly_reason"] = None
                if tx.get("status") != "APPROVED":
                    tx["status"] = "PENDING"

        return transactions
