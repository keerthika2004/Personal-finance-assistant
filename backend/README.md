# Finance Assistant Backend

A robust, FastAPI-powered backend implementing the core intelligence, orchestration, and data persistence layers for the Personal Finance Assistant.

## Architecture Highlights

- **FastAPI Core**: High-performance REST endpoints defined in `app/api/`, utilizing Pydantic for strict schema validation and serialization.
- **LangGraph Orchestration**: Located in `app/agents/`. Manages complex, stateful multi-step AI workflows:
  - **Parsing Graph**: Orchestrates Tesseract OCR and LLM-based data extraction from unstructured PDFs and images.
  - **Reconciliation Graph**: Handles transaction deduplication and routes uncertain/anomalous transactions to the HITL (Human-in-the-Loop) queue.
  - **Chat Graph**: A RAG-style interactive agent that queries the database to answer natural language questions about the user's finances.
- **Hybrid Categorization Engine**: 
  - Uses a Scikit-Learn TF-IDF + Logistic Regression pipeline (`app/services/ml_categorizer.py`) for ultra-fast, low-latency transaction categorization.
  - Falls back to a zero-shot LLM categorizer (Llama 3 via Groq) when the ML model confidence is below a defined threshold.
- **Cash Flow Forecasting**: Integrates Meta's `Prophet` time-series forecasting model to project 30-day cumulative balances based on historical trends (`app/services/forecasting.py`).
- **Data Privacy & Security**: Features a custom PII Redaction layer (`app/services/pii_redactor.py`) that strictly scrubs sensitive information (Credit Cards, SSNs, Phone Numbers) using Regex before any data is passed to external LLM APIs.
- **Observability**: Fully instrumented with `Langfuse` to trace, monitor, and debug complex LangChain and LangGraph execution paths.
- **Database**: PostgreSQL integration utilizing `asyncpg` for non-blocking SQLAlchemy session management.

## Local Development

1. Create a Python virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` file in this directory with the required variables:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/finance
GROQ_API_KEY=your_groq_api_key_here
LANGFUSE_PUBLIC_KEY=optional_langfuse_pk
LANGFUSE_SECRET_KEY=optional_langfuse_sk
USE_ML_CATEGORIZER=true
```

3. Run the Uvicorn development server:
```bash
uvicorn backend.app.main:app --reload --port 8000
```

## Running Tests

Unit and integration tests are located in `tests/`. Ensure your `PYTHONPATH` is set correctly:

```bash
PYTHONPATH=.. pytest tests/
```
