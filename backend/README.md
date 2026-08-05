# Finance Assistant Backend

FastAPI-powered backend implementing the core intelligence and data storage for the Personal Finance Assistant.

## Architecture Highlights
- **FastAPI**: REST endpoints located in `app/api/`.
- **LangGraph Agents**: Located in `app/agents/`. Handles orchestration for multi-step AI tasks like parsing statements, reconciling transactions, and providing chat Q&A.
- **ML Services**: Custom ML models and PII redaction utilities are found in `app/services/`.
- **Database**: PostgreSQL with `asyncpg` async SQLAlchemy sessions.

## Local Development
Ensure dependencies are installed from `requirements.txt`.
Create a `.env` with `DATABASE_URL`, `GROQ_API_KEY`, and optional `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`.

Run the dev server:
```bash
uvicorn backend.app.main:app --reload --port 8000
```

## Running Tests
Tests are located in `backend/tests/`. Ensure you set the python path:
```bash
PYTHONPATH=.. pytest tests/
```
