import pytest
from backend.app.services.anomaly_detector import HybridAnomalyDetector


def test_anomaly_detector_normal_vs_spike():
    hist = [
        {"amount": -350.0, "category": "Dining", "raw_description": "Swiggy"},
        {"amount": -450.0, "category": "Dining", "raw_description": "McDonalds"},
        {"amount": -200.0, "category": "Dining", "raw_description": "Cafe"}
    ]

    new_txs = [
        {"amount": -300.0, "category": "Dining", "raw_description": "Coffee Shop", "is_duplicate": False},
        {"amount": -12000.0, "category": "Dining", "raw_description": "Extreme Fine Dining", "is_duplicate": False}
    ]

    results = HybridAnomalyDetector.detect_and_score(new_txs, hist)

    # Normal coffee transaction should be PENDING
    assert results[0]["status"] == "PENDING"
    assert results[0]["is_suspicious"] is False

    # Extreme fine dining transaction should be FLAGGED
    assert results[1]["status"] == "FLAGGED"
    assert results[1]["is_suspicious"] is True
    assert "higher than your median Dining expense" in results[1]["anomaly_reason"]


def test_anomaly_detector_uncategorized_flag():
    txs = [
        {"amount": -500.0, "category": "Uncategorized", "raw_description": "Unknown Store", "is_duplicate": False}
    ]

    results = HybridAnomalyDetector.detect_and_score(txs)
    assert results[0]["status"] == "FLAGGED"
    assert "Uncategorized transaction requires manual review" in results[0]["anomaly_reason"]
