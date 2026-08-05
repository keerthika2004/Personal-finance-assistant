# Personal Finance Assistant

An intelligent, AI-powered personal finance manager that automatically parses bank statements (PDF, CSV, and Images), categorizes transactions, detects anomalies, and provides deep AI-driven financial insights. 

Built using a full-stack architecture with **Streamlit** (Frontend), **FastAPI** (Backend), **PostgreSQL** (Database), and **LangGraph** (AI Agents powered by Groq Llama 3).

## Features
- **Multi-format Statement Parsing**: Upload bank statements in PDF, CSV, or Image (JPEG/PNG) formats. Images are parsed via Tesseract OCR and Llama-3.
- **AI Transaction Categorization**: Automatically normalizes merchant names and categorizes transactions (Groceries, Dining, etc.) using AI.
- **Human-in-the-Loop (HITL) Review**: Suspicious transactions (e.g. unusually large amounts) and potential duplicates are flagged by the AI for human review before being approved.
- **Interactive Dashboard**: View category breakdowns, monthly cash flow trends, and net savings.
- **AI Financial Insights**: Get a customized, auto-generated financial report analyzing your spending habits and savings rate.
- **Goal Tracking**: Create and track specific financial savings goals.
- **Chatbot Assistant**: Ask questions about your finances and get AI-driven answers based on your transaction history.

## Architecture

- **Frontend**: Streamlit (Python) - Located in `/frontend`
- **Backend**: FastAPI (Python) - Located in `/backend`
- **Database**: PostgreSQL (via SQLAlchemy & asyncpg)
- **AI/LLM Engine**: Groq (Llama-3-70b-versatile) & LangGraph for agentic workflows.

## Prerequisites
- **Python 3.9+**
- **Docker & Docker Compose** (For running Postgres locally)
- **Tesseract OCR** (For image parsing)
  - *Mac*: `brew install tesseract`
  - *Ubuntu*: `sudo apt-get install tesseract-ocr`

## Quick Start

### 1. Environment Setup
Create a `.env` file in the `backend/` directory with the following variables:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/finance_db
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### 2. Start the Database
Start the local PostgreSQL database using Docker Compose:
```bash
docker-compose up -d
```

### 3. Run the Backend (FastAPI)
```bash
# Create a virtual environment and install requirements
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Start the FastAPI server
python -m uvicorn backend.app.main:app --reload --reload-dir backend --port 8000
```

### 4. Run the Frontend (Streamlit)
In a new terminal window:
```bash
source venv/bin/activate
pip install -r frontend/requirements.txt

# Start the Streamlit app
python -m streamlit run frontend/app.py
```
The app will open in your browser at `http://localhost:8501`.

## Documentation
- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)

---
*Created by Keerthika.*
