# Finance Assistant Backend

A robust, FastAPI-powered backend implementing the core intelligence, orchestration, and data persistence layers for the Personal Finance Assistant.

## Folder Structure

```text
backend/
├── app/
│   ├── agents/      # LangGraph workflows (chat, reconcile, parsing)
│   ├── api/         # FastAPI REST routers (auth, chat, upload, etc.)
│   ├── core/        # App configs and security
│   ├── db/          # SQLAlchemy asyncpg models and session management
│   ├── models/      # Pickled scikit-learn models
│   └── services/    # Business logic (LLM Factory, ML Categorizer, PII Redactor)
├── tests/           # Pytest unit and integration tests
├── .env.example     # Template for environment variables
└── requirements.txt # Python dependencies
```

## API Overview
The backend exposes RESTful endpoints prefixed with `/api/v1`. 
> [!IMPORTANT]
> The authoritative source for API documentation is the auto-generated Swagger UI. When the server is running, visit **`http://localhost:8000/docs`** to explore, test, and view schemas for all available routes.

## Architecture Highlights

- **FastAPI Core**: High-performance REST endpoints defined in `app/api/`, utilizing Pydantic for strict schema validation and serialization.
- **LangGraph Orchestration**: Located in `app/agents/`. Manages complex, stateful multi-step AI workflows:
  - **Parsing Graph**: Orchestrates Tesseract OCR and LLM-based data extraction from unstructured PDFs and images.
  - **Reconciliation Graph**: Handles transaction deduplication and routes uncertain/anomalous transactions to the HITL (Human-in-the-Loop) queue.
  - **Chat Graph**: A RAG-style interactive agent that queries the database to answer natural language questions about the user's finances.
- **Two-Tier LLM Routing (`app/services/llm_factory.py`)**: To balance cost, speed, and reasoning capability, the system utilizes two Groq models:
  - `GROQ_FAST_MODEL` (e.g. Llama 3.1 8B) for fast, structured tasks like classification, routing, and tool-calling.
  - `GROQ_MODEL` (e.g. Llama 3.1 70B) for deep reasoning and insight generation.
- **Hybrid Categorization Engine**: 
  - Uses a Scikit-Learn TF-IDF (Word + Char n-grams) + Logistic Regression pipeline (`app/services/categorizer.py`) for ultra-fast, low-latency transaction categorization.
  - Falls back to a zero-shot LLM categorizer using strict JSON Structured Outputs when the ML model confidence is below a defined threshold (0.35).
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

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:pass@localhost:5432/db` |
| `REDIS_URL` | Redis connection string for caching/rate-limits | `redis://localhost:6379/0` |
| `GROQ_API_KEY` | Groq API Key for LLM inference | `gsk_...` |
| `GROQ_MODEL` | Heavy reasoning model | `openai/gpt-oss-120b` |
| `GROQ_FAST_MODEL` | Fast classification model | `openai/gpt-oss-20b` |
| `JWT_SECRET_KEY` | Secret key for JWT signing | `change-me-to-a-long-random-string` |

3. Run the application:
**Option A: Local Uvicorn**
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Option B: Docker Compose**
*(From the project root)*
```bash
docker-compose up --build backend
```

## ML Workflow (Data & Evaluation)

Our Machine Learning pipeline is entirely self-contained and reproducible. To experiment with the models:

1. **Generate Synthetic Data**: 
   `python scripts/generate_data.py` (Creates diverse, randomized transactions with specific category distributions and test-split holdouts in `data/`).
2. **Train the ML Model**: 
   `python scripts/train_model.py` (Trains the TF-IDF feature union and Logistic Regression model, outputting a pickled file to `backend/app/models/categorizer.pkl`).
3. **Run Evaluations**: 
   `python eval/run_evals.py` (Evaluates the models on unseen data and outputs benchmarks like F1 scores and MASE to `eval/eval_results.txt`).

## Running Tests

Unit and integration tests are located in `tests/`. Ensure your `PYTHONPATH` is set correctly:

```bash
PYTHONPATH=.. pytest tests/
```
