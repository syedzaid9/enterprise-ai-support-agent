"""
Agent Run Tracking Service for ResolveAI.
Records every LangGraph workflow execution, intent classification, and resolution status in PostgreSQL.
"""

import datetime
from typing import Optional, Dict, Any, List
from app.db.database import get_db
from app.db.models import AgentRun


def start_agent_run(
    company_id: int,
    customer_id: int,
    conversation_id: Optional[int] = None,
    workflow_name: str = "resolve_support_flow",
    intent: Optional[str] = None,
) -> int:
    """
    Log the initiation of an agent workflow run.
    Returns agent_run.id.
    """
    with get_db() as db:
        run = AgentRun(
            company_id=company_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            workflow_name=workflow_name,
            intent=intent,
            status="running",
            started_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(run)
        db.flush()
        return run.id


def finish_agent_run(
    agent_run_id: int,
    status: str = "completed",  # "completed", "interrupted", "failed"
    error: Optional[str] = None,
    metadata_json: Optional[str] = None,
):
    """
    Mark an agent run as finished.
    """
    with get_db() as db:
        run = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
        if run:
            run.status = status
            run.completed_at = datetime.datetime.now(datetime.timezone.utc)
            if error:
                run.error = error
            if metadata_json:
                run.metadata_json = metadata_json
            db.flush()


def list_agent_runs_by_company(company_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    List real agent runs for admin monitoring.
    """
    with get_db() as db:
        runs = (
            db.query(AgentRun)
            .filter(AgentRun.company_id == company_id)
            .order_by(AgentRun.started_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "customer_id": r.customer_id,
                "workflow_name": r.workflow_name,
                "intent": r.intent or "general_inquiry",
                "status": r.status,
                "started_at": r.started_at.strftime("%d %b %Y, %I:%M:%S %p") if r.started_at else "N/A",
                "completed_at": r.completed_at.strftime("%d %b %Y, %I:%M:%S %p") if r.completed_at else "N/A",
                "error": r.error,
            }
            for r in runs
        ]
