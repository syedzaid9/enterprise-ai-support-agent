"""
ResolveAI Database package.
"""

from app.db.database import get_db, init_db, engine, SessionLocal
from app.db.models import (
    Base,
    Company,
    User,
    Customer,
    Subscription,
    Payment,
    Conversation,
    Message,
    Ticket,
    Approval,
    AgentRun,
    AuditLog,
    KnowledgeDocument,
)

__all__ = [
    "get_db",
    "init_db",
    "engine",
    "SessionLocal",
    "Base",
    "Company",
    "User",
    "Customer",
    "Subscription",
    "Payment",
    "Conversation",
    "Message",
    "Ticket",
    "Approval",
    "AgentRun",
    "AuditLog",
    "KnowledgeDocument",
]
