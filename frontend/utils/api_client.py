import os
import requests
from typing import Dict, Any, Optional

API_BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")


class APIClient:
    """HTTP Client interfacing Streamlit UI with the FastAPI microservice backend."""

    @staticmethod
    def check_health() -> bool:
        try:
            res = requests.get(f"{API_BASE_URL}/health", timeout=3)
            return res.status_code == 200
        except Exception:
            return False

    @staticmethod
    def upload_statement(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        files = {"file": (filename, file_bytes)}
        res = requests.post(f"{API_BASE_URL}/api/v1/upload", files=files, timeout=60)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def submit_chat_transaction(text: str) -> Dict[str, Any]:
        payload = {"text": text}
        res = requests.post(f"{API_BASE_URL}/api/v1/upload/chat", json=payload, timeout=20)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def add_manual_transaction(date: str, description: str, amount: float) -> Dict[str, Any]:
        payload = {
            "date": date,
            "description": description,
            "amount": amount
        }
        res = requests.post(f"{API_BASE_URL}/api/v1/upload/manual", json=payload, timeout=60)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_pending_hitl_items() -> list:
        res = requests.get(f"{API_BASE_URL}/api/v1/reconcile/pending", timeout=10)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def submit_hitl_decision(tx_id: str, action: str, reason: str = "", category: str = None) -> Dict[str, Any]:
        payload = {"transaction_id": tx_id, "action": action, "reason": reason}
        if category:
            payload["category"] = category
        res = requests.post(f"{API_BASE_URL}/api/v1/reconcile/decision", json=payload, timeout=10)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_analytics_summary() -> Dict[str, Any]:
        res = requests.get(f"{API_BASE_URL}/api/v1/analytics/summary", timeout=15)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def create_goal(goal_name: str, target_amount: float, current_amount: float = 0.0, category_target: str = "Savings") -> Dict[str, Any]:
        payload = {
            "goal_name": goal_name,
            "target_amount": target_amount,
            "current_amount": current_amount,
            "category_target": category_target
        }
        res = requests.post(f"{API_BASE_URL}/api/v1/analytics/goals", json=payload, timeout=10)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def add_funds_to_goal(goal_id: str, amount: float) -> Dict[str, Any]:
        payload = {"amount": amount}
        res = requests.put(f"{API_BASE_URL}/api/v1/analytics/goals/{goal_id}/add", json=payload, timeout=10)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def delete_goal(goal_id: str) -> Dict[str, Any]:
        res = requests.delete(f"{API_BASE_URL}/api/v1/analytics/goals/{goal_id}", timeout=10)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def send_chat_message(message: str) -> Dict[str, Any]:
        payload = {"message": message}
        res = requests.post(f"{API_BASE_URL}/api/v1/chat", json=payload, timeout=30)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def update_transaction(tx_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        res = requests.put(f"{API_BASE_URL}/api/v1/analytics/transaction/{tx_id}", json=updates, timeout=20)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def delete_transaction(tx_id: str) -> Dict[str, Any]:
        res = requests.delete(f"{API_BASE_URL}/api/v1/analytics/transaction/{tx_id}", timeout=20)
        res.raise_for_status()
        return res.json()
