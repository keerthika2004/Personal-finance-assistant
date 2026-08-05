# Backend API & AI Agents

The backend for the Personal Finance Assistant is built using **FastAPI** and uses **PostgreSQL** for data persistence. It heavily utilizes **LangGraph** to build autonomous AI agents that handle transaction reconciliation and insight generation.

## Directory Structure
- `/app/api`: FastAPI route handlers (`routes_upload.py`, `routes_analytics.py`, `routes_reconcile.py`, `routes_chat.py`).
- `/app/agents`: LangGraph workflows.
  - `reconciliation_graph.py`: Handles transaction normalization, deduplication, and anomaly scoring. Pauses for Human-in-the-Loop review if suspicious transactions are found.
  - `insights_graph.py`: Generates the personalized financial AI report.
  - `chat_graph.py`: Powers the conversational AI chatbot.
- `/app/db`: Database connection setup (`database.py`) and SQLAlchemy ORM models (`models.py`).
- `/app/services`: External services, like the `LLMFactory` for interacting with the Groq API and `pdf_parser.py` for parsing statements using Tesseract.

## Database Schema
The database uses `asyncpg` to communicate with Postgres asynchronously.
1. **Statement**: Tracks uploaded files (CSV/PDF/Image) and their processing status (`RECONCILING`, `PAUSED_HITL`, `COMPLETED`).
2. **Transaction**: Stores individual transactions parsed from statements. Includes fields for `amount`, `normalized_merchant`, `category`, and boolean flags for anomalies. Status can be `PENDING`, `FLAGGED`, or `APPROVED`.
3. **UserGoal**: Tracks user-defined financial savings goals.

## The Human-in-the-Loop (HITL) Workflow
When a statement is uploaded:
1. `pdf_parser.py` extracts raw transaction rows.
2. The LangGraph `reconciliation_graph` is invoked.
3. The LLM normalizes the merchant names and categorizes the transaction.
4. If a transaction amount is unusually large (> ₹1,000 or 4x average), it is marked as `is_suspicious=True` and `status="FLAGGED"`.
5. The LangGraph execution pauses and the remaining safe transactions are saved as `PENDING`.
6. The user reviews the flagged transactions on the frontend. Once the queue is clear, all `PENDING` transactions are automatically finalized as `APPROVED`.

## Environment Variables
The backend requires a `.env` file in this directory:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/finance_db
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
