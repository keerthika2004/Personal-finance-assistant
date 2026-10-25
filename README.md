# FinAI Assistant — Full-Stack AI/ML Personal Finance Platform

<div align="center">

[![CI/CD Pipeline](https://github.com/keerthika2004/Personal-finance-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/keerthika2004/Personal-finance-assistant/actions)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00?style=flat&logo=langchain&logoColor=white)](https://langchain.com)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Isolation_Forest-F7931E?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

<br/>

> [!IMPORTANT]
> ### Live Interactive Demo
> **Try the platform live in your browser:** [**https://personal-finance-assistant-orcin.vercel.app**](https://personal-finance-assistant-orcin.vercel.app)
> 
>  **1-Click Recruiter Evaluation:** Click **"Demo Login"** on the sign-in modal to immediately test the populated financial dashboard, interactive cash flow forecasting, and live RBI Account Aggregator bank sync simulation with zero setup required!

<br/>

<div align="center">
 <img src="assets/dashboard1.png" alt="Financial Dashboard" width="800"/>
</div>

**[Backend Documentation](backend/README.md)** | **[Frontend Documentation](frontend/README.md)**

Hi there! I'm **Keerthika**, and welcome to **FinAI Assistant**!

I built this project to solve a real headache I faced every month: tracking expenses across multiple Indian bank accounts, credit cards, and random PDF/image receipts without spending hours typing numbers into spreadsheets.

I wanted an intelligent assistant that could automatically pull transactions via Open Banking (RBI Account Aggregator), categorize expenses with machine learning, flag duplicate charges or suspicious spending spikes, forecast my next month's cash flow, and answer natural language questions about my money—all while keeping my sensitive financial data completely private.

---

## Why I Built This & Engineering Challenges

When designing FinAI Assistant, I wanted to go beyond simple API wrappers and build a production-grade system:

1. **Why LangGraph for Agent Workflows?**  
  Standard linear LLM chains fail when dealing with messy real-world bank statements. I built 3 stateful **LangGraph** workflows: **Reconciliation** (normalize → deduplicate → anomaly-score → HITL branch), **Insights** (metrics → LLM coaching), and a **tool-calling Chat agent** that loops between the LLM and typed Python tools until it has an answer.

2. **Why the LLM never does the math.**  
  The chat agent answers questions by calling typed tools (`sum_spending`, `category_breakdown`, `top_transactions`, …) that compute exact figures in pandas over the user's own transactions. The model only chooses the tool and phrases the answer, so it can't invent or miscalculate a number.

3. **Why a Hybrid Anomaly Detector (Isolation Forest + Median/IQR)?**  
  Rule-based thresholds break when a user's income or habits change. I combined **Scikit-Learn Isolation Forest** with per-category **Median & Interquartile Range (IQR)** profiling against the user's history. Using the *Median* instead of the *Mean* ensures one large ₹10,000 fine dining bill doesn't skew future baselines.

4. **Privacy-First PII Redaction Layer:**  
  Sending raw bank descriptions to third-party cloud LLMs is a security risk. A dedicated `PIIRedactor` scrubs card numbers, Aadhaar, PAN, UPI IDs, emails, Indian and US phone numbers, and long account/reference numbers before any text (including OCR output and chat messages) crosses the external API boundary.

5. **Human-in-the-Loop (HITL) Queue:**  
  AI models shouldn't blindly make assumptions with a user's money. A transaction goes to the Review Queue for one-click confirmation when it's a likely duplicate, can't be categorized, or its composite anomaly score reaches 40/100.

---

## Key Features

- **Multi-Tenant Authentication**: Every data endpoint requires a signed JWT; all data access is scoped to the token's `user_id`, including ownership checks on every by-ID endpoint. A **1-Click Demo Login** issues a real demo token for instant portfolio evaluation.
- **RBI Account Aggregator (AA) Bank Sync (simulated)**: Indian Open Banking flow (HDFC, SBI, ICICI, Axis) with 6-digit OTP consent. Sessions are bound to the user, expire after 10 minutes, and lock after 5 wrong OTPs.
- **LangGraph Workflows**:
 - **Statement Parsing**: CSVs, PDFs (table and text layouts), and image receipts via `Tesseract OCR`, with word-based column detection for Indian bank formats (e.g. `Withdrawal Amt.`, `Value Dt`).
 - **Reconciliation Graph**: Hybrid categorization, deduplication across uploads and bank syncs, and hybrid anomaly scoring.
 - **Insights Graph & Chat Agent**: Spending health coaching and natural-language financial Q&A.
- **Hybrid Categorizer**: Keyword rules and a TF-IDF (word + char n-gram) classifier handle confident cases locally; an LLM fallback handles the rest.
- **Hybrid ML Anomaly & Fraud Engine**: Catches high-value outliers, duplicate charges, and uncategorized entries.
- **Cash Flow Forecasting**: 30-day balance forecasting using **Meta Prophet**.
- **Exact Money Handling**: Amounts are stored as `NUMERIC(14,2)`, not floats.
- **GitHub Actions CI/CD Pipeline**: `.github/workflows/ci.yml` runs `pytest`, the evaluation harness, and a type-checked frontend build (`tsc -b && vite build`) on every push.

---

## Screenshots & Workflow

### Dashboard & Financial Overview
| Dashboard & AI Quick Add | Cash Flow Trend & 30-Day Forecast |
| :---: | :---: |
| <img src="assets/dashboard2.png" width="400"/> | <img src="assets/dashboard3.png" width="400"/> |
| *Dashboard featuring health score, user account switcher, and Groq NLP Quick Add.* | *Monthly cash flow breakdown and Meta Prophet 30-day cash flow forecast.* |

| Custom Savings Targets | Category Distribution & AI Coaching |
| :---: | :---: |
| <img src="assets/dashboard4.png" width="400"/> | <img src="assets/dashboard5.png" width="400"/> |
| *Tracking progress against savings targets with dynamic progress indicators.* | *Category spending breakdown and AI-generated financial health coaching.* |

### Open Banking Sync & HITL Approval Queue
| Unified Bank Connect Hub | Bank Selection & Mobile Entry |
| :---: | :---: |
| <img src="assets/bank_connect_main.png" width="400"/> | <img src="assets/bank_modal_step1.png" width="400"/> |
| *Import options for RBI Account Aggregator sync, statement upload, and manual entry.* | *Selecting from Indian banks (HDFC, SBI, ICICI, Axis) and entering registered mobile numbers.* |

| Authorize AA Consent via OTP | Human-in-the-Loop (HITL) Queue |
| :---: | :---: |
| <img src="assets/bank_modal_step2.png" width="400"/> | <img src="assets/review_queue_hitl.png" width="400"/> |
| *Entering the 6-digit OTP to grant read-only statement access.* | *Review queue for approving or rejecting flagged duplicate charges and spending spikes.* |

---

## Evaluation Benchmarks

All numbers come from `eval/run_evals.py`, which runs in CI on every push. Full output: [`eval/eval_results.txt`](eval/eval_results.txt) and [`eval/benchmark.txt`](eval/benchmark.txt).

### Chat agent: 49/50 on a hand-labelled eval
50 questions (totals, date ranges, merchant filters, counts, top-N, category breakdowns, goals) over a fixed 24-transaction dataset, with expected answers worked out by hand. The agent uses the same system prompt as the `/chat` endpoint. The one miss: asked "How many income transactions do I have?", it didn't pass the `Income` category filter to the count tool.

### Hybrid categorizer on unseen merchants
The held-out test set (`data/test.csv`, 120 rows) contains only merchants that never appear in the training data.

| Approach | Macro-F1 | Notes |
|---|---|---|
| Local ML only (TF-IDF word + char n-grams) | 0.45 | Struggles on merchants it has never seen |
| Zero-shot LLM only (`openai/gpt-oss-120b`) | 0.97 | Measured on a 40-row subset to limit API cost |
| **Hybrid (production path)** | **0.94** | All 120 rows |

The hybrid path is exactly what the app runs: PII redaction → keyword rules → shipped `categorizer.pkl` (kept only when confidence ≥ 0.35) → LLM fallback for everything else.

- **47% fewer LLM calls** than LLM-only: 56 of 120 rows were handled locally, at **98.2% accuracy** on those rows.
- **Local latency:** 0.85 ms median, 1.76 ms p95 per call.

> Earlier iteration: a word-only TF-IDF model scored 0.36 Macro-F1 on unseen merchants; adding character n-grams raised it to 0.45, and adding the confidence-gated LLM fallback raised the end-to-end result to 0.94.

### Forecasting (Meta Prophet)
- **MASE 0.64** against a seasonal-naive baseline (below 1 means Prophet beats "next week looks like last week"). MAE 283 vs 415 for the baseline, on a synthetic daily cash-flow series. MAPE is not reported because the series crosses zero.

### Anomaly flagging (synthetic)
- **F1 1.00** on 48 synthetic transactions with 8 injected spikes (6–12× the category median). This is a sanity check that the rules fire as designed, not a measure of real-world fraud detection.

---

## Architecture & System Design

```mermaid
graph TD
   %% User Interfaces & Auth
   User([User]) -->|Register / Sign In / Demo| Auth[JWT Auth]
   Auth --> UI[React + TypeScript Frontend]
   User -->|OTP Consent & Bank Linking| AA[Simulated RBI Account Aggregator]

   %% Backend APIs
   AA -->|Mock bank payload| API[FastAPI Backend]
   UI -->|Bearer Token REST Calls| API

   %% Parsing
   API --> Parser[Statement Parser: CSV / PDF / Image]
   Parser --> OCR[Tesseract OCR]
   OCR --> PII1[PII Redactor]
   PII1 --> ParseLLM[gpt-oss via Groq]

   %% Reconciliation & ML
   API --> ReconGraph[LangGraph: Reconciliation]
   ReconGraph --> PII2[PII Redactor]
   PII2 --> ML[Keyword Rules + TF-IDF Classifier]
   ML -.->|low confidence| LLMCat[LLM Categorizer Fallback]
   ReconGraph --> Anomaly[Isolation Forest + Median/IQR Scorer & Dedup]
   Anomaly -->|flagged| HITL[HITL Review Queue]

   %% Analytics & Forecasting
   API --> Insights[LangGraph: Insights]
   API --> Prophet[Meta Prophet Forecaster]

   %% Chat
   API --> ChatGraph[LangGraph: Tool-Calling Chat Agent]
   ChatGraph --> Tools[Typed pandas tools]

   %% Storage
   ReconGraph --> DB[(PostgreSQL, user-scoped)]
   Insights --> DB
   ChatGraph --> DB
```

---

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2.0 Async (asyncpg), PostgreSQL, Pydantic, Python 3.11
- **Frontend**: React 19, TypeScript, Vite, Recharts, Lucide Icons, React Hot Toast
- **Banking Integration**: Simulated RBI Account Aggregator flow (production would use a Setu / Finvu sandbox)
- **AI/ML**: LangGraph, LangChain, Scikit-Learn (Isolation Forest & Logistic Regression), Meta Prophet, Tesseract OCR, Groq API (`openai/gpt-oss-120b` for reasoning, `openai/gpt-oss-20b` for fast tasks)
- **DevOps & CI/CD**: GitHub Actions (`.github/workflows/ci.yml`), Docker Compose, Pytest
- **Observability**: Langfuse Tracing (optional)

---

## Monorepo Layout

```text
.
├── backend/            # FastAPI, LangGraph agents, ML services
├── frontend/           # React + Vite dashboard SPA
├── eval/               # Evaluation harness and results
├── scripts/            # Synthetic data generation and model training scripts
├── data/               # Training and held-out test CSVs
├── assets/             # README images
└── docker-compose.yml  # Local Postgres + Redis
```

---

## Running Locally

### Quickstart with Docker Compose

Docker Compose starts the databases (Postgres, plus Redis, which is not used by the app yet):
```bash
docker-compose up -d
```
Compose exposes Postgres on host port **5433**, so set `DATABASE_URL` to use `localhost:5433` (see below). You still run the backend and frontend yourself.

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (if not using Docker)
- Tesseract OCR (`brew install tesseract` or `apt-get install tesseract-ocr`)

### 2. Environment Setup
Create `backend/.env` from `backend/.env.example`:
```env
# Use port 5433 with docker-compose, 5432 for a local Postgres install
DATABASE_URL=postgresql+asyncpg://postgres:postgrespassword@localhost:5433/financial_ai_db
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
GROQ_FAST_MODEL=openai/gpt-oss-20b
JWT_SECRET_KEY=<generate one, see below>
ALLOWED_ORIGINS=http://localhost:5173
```
`JWT_SECRET_KEY` is **required**: the backend refuses to start without it, or with the placeholder value. Generate one with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 3. Backend Setup
Run from the repository root:
```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```
API docs are served at `http://localhost:8000/docs`.

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Testing & Evaluation Harness

Run unit tests:
```bash
PYTHONPATH=. pytest backend/tests
```

Run the evaluation suite and save the results (the chat and LLM evals need `GROQ_API_KEY`; they are skipped without it):
```bash
PYTHONPATH=. python eval/run_evals.py > eval/eval_results.txt
```

---

## Roadmap & Known Limitations
- **Data Integrations**: The RBI Account Aggregator flow is simulated with mock bank payloads. Production requires a live Setu/Finvu sandbox key.
- **AA sessions are in memory**: Fine for a single server instance; multiple workers or restarts need a shared store such as Redis.
- **LLM fallback reliability**: In the latest eval, 2 of 64 fallback calls failed with a Groq structured-output error and were left as "Uncategorized" (they still count in the 0.94).
- **Chat is single-turn**: The agent doesn't remember earlier messages in a conversation.
- **Auth token storage**: The JWT lives in `localStorage`; moving it to an httpOnly cookie would harden it against XSS.
- **Multi-currency**: Assumes a single base currency (INR). No live FX conversions yet.
- **Budgeting**: Alert triggers for crossing custom budget thresholds are planned.

---

## About the Author
Built by **Keerthika**. I'm passionate about the intersection of AI, agentic architectures, and personal finance. Feel free to explore the repository, run the evals yourself, or test the live demo!

## License
MIT License
 