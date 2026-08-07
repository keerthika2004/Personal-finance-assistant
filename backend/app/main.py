import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.db.database import init_db
from backend.app.api.routes_upload import router as upload_router
from backend.app.api.routes_reconcile import router as reconcile_router
from backend.app.api.routes_analytics import router as analytics_router
from backend.app.api.routes_chat import router as chat_router
from backend.app.api.routes_bank_sync import router as bank_sync_router
from backend.app.api.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize database tables on startup."""
    try:
        await init_db()
    except Exception as e:
        print(f"Database initialization warning: {e}")
    yield


app = FastAPI(
    title="Unified Financial AI Assistant API",
    description="Backend microservice featuring LangGraph multi-agent reconciliation, HITL approval queues, and Groq RAG analytics.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router Modules
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(reconcile_router)
app.include_router(analytics_router)
app.include_router(chat_router)
app.include_router(bank_sync_router)


@app.get("/", tags=["Health"])
@app.head("/", tags=["Health"])
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Unified Financial AI Assistant Backend",
        "llm_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
