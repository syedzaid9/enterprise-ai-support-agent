"""
Admin REST API endpoints for ResolveAI.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import Company, Customer, Ticket, Approval, Subscription, Payment, KnowledgeDocument
from app.services.customer_service import list_customers_by_company
from app.services.ticket_service import list_tickets_by_company
from app.services.audit_service import list_audit_logs
from app.services.knowledge_service import list_knowledge_documents, save_and_index_document, delete_knowledge_document
from app.config import get_integration_health

router = APIRouter(prefix="/admin", tags=["Admin Console"])


def verify_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Supervisor Admin authorization required.")
    return current_user


@router.get("/overview")
def get_admin_overview(admin_user=Depends(verify_admin)):
    company_id = admin_user.company_id
    with get_db() as db:
        company = db.query(Company).filter(Company.id == company_id).first()
        total_customers = db.query(Customer).filter(Customer.company_id == company_id).count()
        open_tickets = db.query(Ticket).filter(Ticket.company_id == company_id, Ticket.status.in_(["open", "in_progress"])).count()
        resolved_tickets = db.query(Ticket).filter(Ticket.company_id == company_id, Ticket.status == "resolved").count()
        pending_approvals = db.query(Approval).filter(Approval.company_id == company_id, Approval.status == "pending").count()
        active_subscriptions = db.query(Subscription).filter(Subscription.company_id == company_id, Subscription.status == "ACTIVE").count()

        return {
            "company_name": company.name if company else "ResolveAI Enterprise",
            "total_customers": total_customers,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "pending_approvals": pending_approvals,
            "active_subscriptions": active_subscriptions,
        }


@router.get("/customers")
def get_customers(admin_user=Depends(verify_admin)):
    return list_customers_by_company(company_id=admin_user.company_id)


@router.get("/tickets")
def get_tickets(status: Optional[str] = None, admin_user=Depends(verify_admin)):
    return list_tickets_by_company(company_id=admin_user.company_id, status=status)


@router.get("/approvals")
def get_pending_approvals(admin_user=Depends(verify_admin)):
    with get_db() as db:
        approvals = (
            db.query(Approval)
            .filter(Approval.company_id == admin_user.company_id)
            .order_by(Approval.created_at.desc())
            .all()
        )
        return [
            {
                "id": a.id,
                "customer_id": a.customer_id,
                "action_type": a.action_type,
                "target_id": a.target_id,
                "action_data": a.action_data,
                "reason": a.reason,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in approvals
        ]


@router.get("/knowledge")
def get_knowledge_documents(admin_user=Depends(verify_admin)):
    return list_knowledge_documents(company_id=admin_user.company_id)


class KnowledgeUploadRequest(BaseModel):
    filename: str
    content: str
    doc_type: str = "policy"


@router.post("/knowledge")
def upload_knowledge_document(req: KnowledgeUploadRequest, admin_user=Depends(verify_admin)):
    try:
        return save_and_index_document(
            company_id=admin_user.company_id,
            filename=req.filename,
            content=req.content,
            uploaded_by_user_id=admin_user.id,
            doc_type=req.doc_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/{doc_id}")
def delete_knowledge(doc_id: int, admin_user=Depends(verify_admin)):
    ok = delete_knowledge_document(company_id=admin_user.company_id, doc_id=doc_id, admin_user_id=admin_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Knowledge document not found.")
    return {"status": "success", "message": "Document deleted."}


@router.get("/audit-logs")
def get_audit_logs(limit: int = 50, action: Optional[str] = None, admin_user=Depends(verify_admin)):
    return list_audit_logs(company_id=admin_user.company_id, limit=limit, action_filter=action)


@router.get("/integrations")
def get_integrations(admin_user=Depends(verify_admin)):
    return get_integration_health()
