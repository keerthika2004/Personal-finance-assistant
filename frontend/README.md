# Finance Assistant Frontend

Streamlit-based frontend for the Personal Finance Assistant. 

## Features
- **File Uploads**: Supports CSV, PDF, and Images for financial statement parsing.
- **Dashboard**: Visualizes cash-flow, spending breakdown, Prophet AI forecasting, and goal tracking using Plotly.
- **Reconciliation HITL**: A Human-In-The-Loop review screen to approve/reject flagged or anomalous transactions before committing them to the database.
- **AI Chat**: An interactive chat interface to query the financial state using natural language.

## Local Development
Ensure dependencies are installed from `requirements.txt`.
Create a `.env` with `BACKEND_URL=http://localhost:8000` (or the appropriate backend URL).

Run the app:
```bash
streamlit run app.py
```
