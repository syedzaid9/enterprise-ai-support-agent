"""
Audit Logging Service for ResolveAI.
Provides immutable, tenant-scoped audit logging for security, compliance, and dispute resolution.
"""

import datetime
from typing import Optional, Dict, Any, List
from app.db.database import get_db
from app.db.models import AuditLog


def log_audit_event(
    company_id: int,
    action: str,
    actor_type: str = "user",  # "user", "admin", "ai_agent", "system"
    user_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[str] = None,
    status: str = "SUCCESS",
):
    """
    Record an immutable audit log entry in PostgreSQL.
    """
    with get_db() as db:
        log = AuditLog(
            company_id=company_id,
            user_id=user_id,
            customer_id=customer_id,
            actor_type=actor_type,
            action=action.upper(),
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            details=details,
            status=status.upper(),
        )
        db.add(log)
        db.flush()


def list_audit_logs(
    company_id: int,
    limit: int = 50,
    action_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List audit logs for a company tenant.
    """
    with get_db() as db:
        query = db.query(AuditLog).filter(AuditLog.company_id == company_id)
        if action_filter:
            query = query.filter(AuditLog.action == action_filter.upper())
        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

        return [
            {
                "id": l.id,
                "timestamp": l.created_at.strftime("%d %b %Y, %I:%M:%S %p") if l.created_at else "N/A",
                "actor_type": l.actor_type,
                "action": l.action,
                "target_type": l.target_type or "-",
                "target_id": l.target_id or "-",
                "status": l.status,
                "details": l.details or "-",
            }
            for l in logs
        ]
