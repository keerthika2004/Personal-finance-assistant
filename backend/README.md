# Finance Assistant Backend

A FastAPI backend implementing the intelligence, orchestration, and data persistence layers for the Personal Finance Assistant.

## Folder Structure

```text
backend/
├── app/
│   ├── agents/      # LangGraph workflows (reconciliation, insights, chat) and the chat agent's tools
│   ├── api/         # FastAPI routers (auth, upload, reconcile, analytics, chat, bank sync)
│   ├── db/          # SQLAlchemy async models, session management, startup migrations and demo seed data
│   ├── models/      # Pickled scikit-learn categorizer
│   ├── services/    # Statement parser, categorizer, anomaly detector, forecasting, PII redactor, LLM factory, money helpers
│   └── main.py      # App entry point, CORS and router registration
├── tests/           # Pytest unit tests
├── .env.example     # Template for environment variables
└── requirements.txt # Python dependencies
```

## API Overview
All endpoints are prefixed with `/api/v1`. Every endpoint except `auth/*` and the health check requires an `Authorization: Bearer <token>` header, and only ever reads or writes the token owner's data.

| Area | Endpoints |
|---|---|
| Auth | `POST auth/register`, `POST auth/login`, `POST auth/demo` |
| Upload | `POST upload` (CSV / PDF / image), `POST upload/manual`, `POST upload/chat` (natural-language Quick Add) |
| Review queue | `GET reconcile/pending`, `POST reconcile/decision` |
| Analytics | `GET analytics/summary`, `POST analytics/goals`, `PUT analytics/goals/{id}/add`, `DELETE analytics/goals/{id}`, `PUT/DELETE analytics/transaction/{id}` |
| Chat | `POST chat` |
| Bank sync (simulated AA) | `POST bank-sync/initiate`, `POST bank-sync/verify-otp`, `POST bank-sync/sync` |

> [!IMPORTANT]
> The authoritative API documentation is the auto-generated Swagger UI. With the server running, visit **`http://localhost:8000/docs`** to explore and test every route.

## Architecture Highlights

- **FastAPI Core**: REST endpoints in `app/api/` with Pydantic validation. Blocking work (LLM calls, OCR, Prophet) runs in a threadpool so it never stalls the event loop.
- **LangGraph Orchestration** (`app/agents/`):
 - **Reconciliation Graph**: normalize & categorize → deduplicate (against the batch and the user's existing transactions) → anomaly-score against the user's history → route flagged items to the HITL queue or auto-approve the rest.
 - **Insights Graph**: computes income, expenses, savings rate and category totals, then asks the LLM for spending insights and per-goal coaching. Results are cached per user in a bounded LRU cache keyed on the user's transactions and goals.
 - **Chat Agent**: a tool-calling loop (agent → tools → agent) over the user's transactions. Tools such as `sum_spending`, `category_breakdown` and `top_transactions` compute exact figures in pandas, so the model never does arithmetic.
- **Statement Parsing** (`app/services/pdf_parser.py`): CSV, PDF tables, text-layout PDFs, and images (Tesseract OCR + LLM extraction). Column headers are classified by whole words, so Indian bank formats like `Withdrawal Amt.`, `Deposit Amt.` and `Value Dt` are read correctly. Re-uploading the same file is rejected with a 409.
- **Two-Tier LLM Routing** (`app/services/llm_factory.py`): two Groq models balance cost and capability:
 - `GROQ_FAST_MODEL` (default `openai/gpt-oss-20b`) for categorization fallback and Quick Add parsing.
 - `GROQ_MODEL` (default `openai/gpt-oss-120b`) for insights, the chat agent, and image extraction.
- **Hybrid Categorization Engine** (`app/services/categorizer.py`):
 1. Whole-word keyword rules for well-known merchants.
 2. A TF-IDF (word + char n-gram) + Logistic Regression pipeline; its prediction is kept only when confidence is ≥ 0.35.
 3. Otherwise, a zero-shot LLM fallback constrained to the category taxonomy via structured output.

 On 120 held-out transactions from unseen merchants this handles 47% of rows locally (98% accurate on those, ~0.85 ms per call) and reaches 0.94 Macro-F1 end to end. See [`eval/benchmark.txt`](../eval/benchmark.txt).
- **Anomaly Detection** (`app/services/anomaly_detector.py`): per-category median/IQR rules plus an Isolation Forest score. Duplicates, uncategorized items and composite scores ≥ 40 go to the review queue.
- **Cash Flow Forecasting** (`app/services/forecasting.py`): Prophet projects a 30-day cumulative balance, anchored to the user's current balance.
- **Data Privacy** (`app/services/pii_redactor.py`): regex redaction of card numbers, Aadhaar, PAN, UPI IDs, emails, Indian and US phone numbers, and long account/reference numbers before any text (transaction descriptions, OCR output, chat messages) is sent to an external LLM.
- **Money**: amounts are stored as `NUMERIC(14,2)` and converted through `to_money()` (`app/services/money.py`), never stored as binary floats.
- **Security**:
 - JWT auth with a required secret and 24-hour tokens.
 - Every query scoped to the token's `user_id`, including ownership checks on by-ID endpoints.
 - CORS restricted to `ALLOWED_ORIGINS`.
 - Simulated AA sessions bound to the user, with a 10-minute expiry and a 5-attempt OTP limit.
- **Observability**: optional `Langfuse` tracing of LangChain and LangGraph runs (set the Langfuse keys to enable).
- **Database**: PostgreSQL via `asyncpg`. On startup, `init_db()` creates tables, applies small idempotent column migrations, and seeds the demo account.

## Local Development

All commands below run from the **repository root**, because imports use the `backend.app...` package path and `.env` is loaded from `backend/.env`.

1. Create a Python virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

2. Create `backend/.env` from `backend/.env.example`:

| Variable | Required | Description | Example |
|---|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL connection string (use port `5433` with the repo's docker-compose) | `postgresql+asyncpg://postgres:postgrespassword@localhost:5433/financial_ai_db` |
| `GROQ_API_KEY` | yes | Groq API key for LLM inference | `gsk_...` |
| `JWT_SECRET_KEY` | yes | Secret for signing JWTs. The app refuses to start without it or with the placeholder value. Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` | — |
| `ALLOWED_ORIGINS` | no | Comma-separated CORS origins | `http://localhost:5173` |
| `GROQ_MODEL` | no | Reasoning model | `openai/gpt-oss-120b` |
| `GROQ_FAST_MODEL` | no | Fast classification model | `openai/gpt-oss-20b` |
| `USE_ML_CATEGORIZER` | no | Set to `false` to skip the local model and always use the LLM | `true` |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | no | Enable Langfuse tracing | — |
| `REDIS_URL` | no | Reserved; not used by the app yet | `redis://localhost:6379/0` |

3. Start the databases (optional, if you don't have Postgres installed):
```bash
docker-compose up -d
```

4. Run the API:
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```

## ML Workflow (Data & Evaluation)

The ML pipeline is self-contained and reproducible:

1. **Generate synthetic data**: `python scripts/generate_data.py` creates training transactions and a held-out test split of unseen merchants in `data/`.
2. **Train the categorizer**: `python scripts/train_model.py` trains the TF-IDF feature union + Logistic Regression on `data/training.csv` only and writes `backend/app/models/categorizer.pkl`.
3. **Run evaluations**: `PYTHONPATH=. python eval/run_evals.py > eval/eval_results.txt` evaluates categorization (local, LLM-only and the hybrid production path), forecasting, anomaly flagging, and a 50-question chat-agent eval. The LLM-based evals need `GROQ_API_KEY` and are skipped without it.

## Running Tests

```bash
PYTHONPATH=. pytest backend/tests
```
 