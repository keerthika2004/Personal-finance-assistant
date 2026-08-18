# FinAI Assistant — Full-Stack AI/ML Personal Finance Platform

<div align="center">

[![CI/CD Pipeline](https://github.com/keerthika2004/Personal-finance-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/keerthika2004/Personal-finance-assistant/actions)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
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

When designing FinAI Assistant, I wanted to go beyond simple API wrappers and build a production-grade enterprise system:

1. **Why LangGraph for Agent Workflows?**  
   Standard linear LLM chains fail when dealing with messy real-world bank statements. I built 3 stateful **LangGraph DAGs** (Parsing, Reconciliation, and Chat) so the assistant can branch dynamically, retry parsing failures, and maintain conversation state.

2. **Why a Hybrid Anomaly Detector (Isolation Forest + Median Z-Scores)?**  
   Rule-based thresholds break when a user's income or habits change. I combined **Scikit-Learn Isolation Forest** with **Category Median & Interquartile Range (IQR)** profiling. Using the *Median* instead of the *Mean* ensures one large ₹10,000 fine dining bill doesn't skew future baseline calculations.

3. **Privacy-First PII Redaction Layer:**  
   Sending raw bank descriptions containing credit card numbers or phone numbers to third-party cloud LLMs is a massive security risk. I built a dedicated `PIIRedactor` service that sanitizes 16-digit card numbers, SSNs, and phone numbers via regex before any text crosses external API boundaries.

4. **Human-in-the-Loop (HITL) Queue:**  
   AI models shouldn't blindly make assumptions with a user's money. When the anomaly score exceeds 70% or a transaction is uncategorized, the system places it in a dedicated HITL Review Queue for one-click user confirmation.

---

## Key Features

- **Multi-Tenant User Authentication**: Full JWT authentication with isolated PostgreSQL data access (`user_id` scoped) and a **1-Click Recruiter Demo Login** for instant portfolio evaluation.
- **RBI Account Aggregator (AA) Bank Sync**: Simulated Indian Open Banking framework (HDFC, SBI, ICICI, Axis Bank) with 6-digit OTP consent verification.
- **LangGraph Multi-Agent Workflows**:
  - **Parsing Agent**: Multi-modal statement parsing for CSVs, PDFs, and image receipts using `Tesseract OCR`.
  - **Reconciliation Agent**: Deduplicates entries across accounts and runs hybrid anomaly detection.
  - **Insights & Chat Agent**: Natural language financial Q&A and spending health coaching.
- **Hybrid ML Anomaly & Fraud Engine**: Catches high-value outliers, duplicate charges, and uncategorized entries.
- **Cash Flow Forecasting**: 30-day income and expense time-series forecasting using **Meta Prophet**.
- **PII Regex Redaction Layer**: Sanitizes credit cards, SSNs, and phone numbers before cloud LLM inference (Groq Llama-3).
- **GitHub Actions CI/CD Pipeline**: Automated workflow (`.github/workflows/ci.yml`) running `pytest` unit tests, evaluation benchmarks, and TypeScript typechecking on every commit.

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

## Evaluation Benchmarks & The Hybrid Model Story

I ran extensive evaluations on synthetic held-out test data (`eval/run_evals.py`) to measure the performance of various models.

**The Disjoint-Merchant Categorization Story**
Categorizing transactions from *known* merchants is easy, but what happens when you visit a new cafe or use a new app? I built a hybrid ML + LLM categorizer to solve this:
1. **Local ML Model (TF-IDF Word Features)**: Overfit to known merchants. On completely unseen merchants, it plummeted to a **0.36** Macro-F1.
2. **Local ML Model (Word + Character n-grams)**: Adding character-level features to catch partial matches improved the score to **0.45** Macro-F1.
3. **Zero-Shot LLM (Llama-3.1-70b-versatile)**: The clear winner. It achieved an astounding **0.97** Macro-F1 on completely unseen merchants by reasoning about the merchant name contextually.

**Conclusion**: Our system uses the ultra-fast Local ML model as a first pass, and automatically falls back to the high-accuracy Zero-Shot LLM for low-confidence or unseen merchants.

**Cashflow Forecasting (Meta Prophet)**
- **MASE: 0.64** (Meaning the Prophet model significantly beats a seasonal naive baseline!)

**Anomaly Detection & Chatbot QA**
- **Anomaly Flagging (Synthetic Data)**: F1-Score **1.00**
- **Chatbot Tool-Calling Accuracy**: **3/3**

---

## Architecture & System Design

```mermaid
graph TD
    %% User Interfaces & Auth
    User([User]) -->|Register / Sign In / Demo| Auth[JWT Auth & Session]
    Auth --> UI[React + TypeScript Frontend]
    User -->|OTP Consent & Bank Linking| AA[RBI Account Aggregator API]
    
    %% Backend APIs
    AA -->|Encrypted Payload| API[FastAPI Backend]
    UI -->|Bearer Token REST Calls| API
    
    %% Parsing & Processing
    API --> ParseGraph[LangGraph: Parsing Agent]
    ParseGraph --> OCR[Tesseract OCR]
    ParseGraph --> ParseLLM[Llama-3 LLM via Groq]
    
    %% Reconciliation & ML
    API --> ReconGraph[LangGraph: Reconciliation Agent]
    ReconGraph --> PII[PII Redactor Layer]
    PII --> ML[Scikit-Learn Isolation Forest & Classifier]
    PII -.-> LLMCat[Zero-Shot LLM Categorizer Fallback]
    ReconGraph --> Anomaly[Anomaly Scorer & Deduplication]
    
    %% Analytics & Forecasting
    API --> Analytics[Analytics Engine]
    Analytics --> Prophet[Meta Prophet Time-Series Forecaster]
    
    %% Chat 
    API --> ChatGraph[LangGraph: Chat Agent]
    
    %% Storage & CI/CD
    ReconGraph --> DB[(Multi-Tenant PostgreSQL + asyncpg)]
    Analytics --> DB
    ChatGraph --> DB
    API -.-> CI[GitHub Actions CI/CD Pipeline]
```

---

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2.0 Async (asyncpg), PostgreSQL, Pydantic, Python 3.11
- **Frontend**: React, TypeScript, Vite, Recharts, Lucide Icons, React Hot Toast
- **Banking Integration**: RBI Account Aggregator Framework (Setu / Open Banking APIs)
- **AI/ML**: LangGraph, LangChain, Scikit-Learn (Isolation Forest & Logistic Regression), Meta Prophet, Tesseract OCR, Groq API (Llama 3.1 models)
- **DevOps & CI/CD**: GitHub Actions (`.github/workflows/ci.yml`), Docker, Docker Compose, Pytest
- **Observability**: Langfuse Tracing

---

## Monorepo Layout

```text
.
├── backend/            # FastAPI, LangGraph agents, ML services
├── frontend/           # React + Vite dashboard SPA
├── eval/               # Evaluation benchmarking scripts and results
├── scripts/            # Synthetic data generation and model training scripts
├── data/               # Output directory for CSV datasets
├── assets/             # README images
└── docker-compose.yml  # Local stack orchestration
```

---

## Running Locally

### Quickstart with Docker Compose

If you have Docker installed, you can spin up the entire stack (Postgres + Redis) instantly:
```bash
docker-compose up -d
```
*(You will still need to run the backend and frontend separately for full development mode, but Docker handles the databases).*

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (if not using Docker)
- Tesseract OCR (`brew install tesseract` or `apt-get install tesseract-ocr`)

### 2. Environment Setup
Create a `.env` file in `backend/` using the `.env.example` file:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgrespassword@localhost:5432/financial_ai_db
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_FAST_MODEL=llama-3.1-8b-instant
JWT_SECRET_KEY=change-me-to-a-long-random-string
```

### 3. Backend Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

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

Run evaluation benchmarking suite:
```bash
PYTHONPATH=. python eval/run_evals.py
```

---

## Roadmap & Known Limitations
- **Data Integrations**: Currently simulates RBI Account Aggregator. Production requires a live Setu/Finvu sandbox key.
- **Multi-currency**: Currently assumes a base currency (INR/USD) globally. No live FX conversions yet.
- **Budgeting**: Alert triggers for crossing custom budget thresholds are planned.

---

## About the Author
Built by **Keerthika**. I'm passionate about the intersection of AI, agentic architectures, and personal finance. Feel free to explore the repository, run the evals yourself, or test the live demo!

## License
MIT License
