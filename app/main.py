"""
ResolveAI — Enterprise AI Customer Support & Resolution Platform.
Main FastAPI application backend and service coordinator.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db
from app.api.auth import router as auth_router
from app.api.customer import router as customer_router
from app.api.chat import router as chat_router
from app.api.payment import router as payment_router
from app.api.tickets import router as ticket_router
from app.api.admin import router as admin_router
from app.api.webhook import router as webhook_router
from app.config import get_integration_health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure PostgreSQL tables are initialized
    init_db()
    yield


app = FastAPI(
    title="ResolveAI — Enterprise AI Resolution Platform API",
    description="Multi-tenant AI customer-support resolution platform combining authenticated context, PostgreSQL, Cashfree Sandbox, RAG, and LangGraph.",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(customer_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(ticket_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")


@app.get("/")
def root():
    return {
        "platform": "ResolveAI",
        "description": "Multi-Tenant Enterprise AI Resolution Platform",
        "status": "online",
        "version": "2.0.0",
        "documentation": "/docs",
    }


@app.get("/health")
def health_check():
    return get_integration_health()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
