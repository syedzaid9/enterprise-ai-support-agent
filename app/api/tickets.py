"""
Ticketing REST API endpoints for ResolveAI.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends

from app.api.auth import get_current_user
from app.services.ticket_service import create_ticket, get_ticket, list_tickets_by_company, update_ticket_status
from app.services.customer_service import get_customer_by_user_id

router = APIRouter(prefix="/tickets", tags=["Support Tickets"])


class CreateTicketRequest(BaseModel):
    title: str
    description: str
    priority: str = "normal"
    conversation_id: Optional[int] = None


class UpdateTicketRequest(BaseModel):
    status: str
    resolution: Optional[str] = None


@router.post("")
def api_create_ticket(req: CreateTicketRequest, current_user=Depends(get_current_user)):
    cust = get_customer_by_user_id(current_user.id, company_id=current_user.company_id)
    customer_id = cust["id"] if cust else 1
    company_id = current_user.company_id or 1

    try:
        t = create_ticket(
            company_id=company_id,
            customer_id=customer_id,
            title=req.title,
            description=req.description,
            priority=req.priority,
            conversation_id=req.conversation_id,
        )
        return t
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticket_number}")
def api_get_ticket(ticket_number: str, current_user=Depends(get_current_user)):
    try:
        return get_ticket(ticket_number_or_id=ticket_number, company_id=current_user.company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{ticket_id}")
def api_update_ticket(ticket_id: int, req: UpdateTicketRequest, current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required.")

    try:
        return update_ticket_status(
            ticket_id=ticket_id,
            status=req.status,
            resolution=req.resolution,
            admin_user_id=current_user.id,
            company_id=current_user.company_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
