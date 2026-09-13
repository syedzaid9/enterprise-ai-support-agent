"""
Ticket Service for ResolveAI.
Manages enterprise customer support tickets, status updates, and automatic escalation.
"""

from typing import Optional, Dict, Any, List
from app.db.database import get_db
from app.db.models import Ticket, Customer, AuditLog


def create_ticket(
    company_id: int,
    customer_id: int,
    title: str,
    description: str,
    priority: str = "normal",
    conversation_id: Optional[int] = None,
    assigned_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new support ticket in PostgreSQL.
    """
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == customer_id, Customer.company_id == company_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found for company {company_id}.")

        ticket_count = db.query(Ticket).filter(Ticket.company_id == company_id).count()
        ticket_number = f"TK-{1000 + ticket_count + 1}"

        ticket = Ticket(
            ticket_number=ticket_number,
            company_id=company_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            title=title.strip(),
            description=description.strip(),
            priority=priority.lower(),
            status="open",
            assigned_to=assigned_to,
        )
        db.add(ticket)
        db.flush()

        audit = AuditLog(
            company_id=company_id,
            customer_id=customer_id,
            actor_type="system",
            action="TICKET_CREATED",
            target_type="ticket",
            target_id=ticket_number,
            details=f"Created ticket {ticket_number}: {title}",
            status="SUCCESS",
        )
        db.add(audit)
        db.flush()

        return {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "description": ticket.description,
            "priority": ticket.priority,
            "status": ticket.status,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }


def get_ticket(ticket_number_or_id: str, company_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Retrieve single ticket by ticket number or database ID.
    """
    with get_db() as db:
        query = db.query(Ticket)
        if company_id:
            query = query.filter(Ticket.company_id == company_id)

        t = (
            query.filter(
                (Ticket.ticket_number == str(ticket_number_or_id))
                | (Ticket.id == (int(ticket_number_or_id) if str(ticket_number_or_id).isdigit() else -1))
            )
            .first()
        )

        if not t:
            raise ValueError(f"Ticket '{ticket_number_or_id}' not found.")

        return {
            "id": t.id,
            "ticket_number": t.ticket_number,
            "company_id": t.company_id,
            "customer_id": t.customer_id,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "assigned_to": t.assigned_to,
            "resolution": t.resolution,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }


def update_ticket_status(
    ticket_id: int,
    status: str,
    resolution: Optional[str] = None,
    admin_user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update ticket status and optional resolution note.
    """
    with get_db() as db:
        query = db.query(Ticket).filter(Ticket.id == ticket_id)
        if company_id:
            query = query.filter(Ticket.company_id == company_id)
        t = query.first()

        if not t:
            raise ValueError(f"Ticket ID {ticket_id} not found.")

        old_status = t.status
        t.status = status.lower()
        if resolution:
            t.resolution = resolution
        db.flush()

        audit = AuditLog(
            company_id=t.company_id,
            customer_id=t.customer_id,
            user_id=admin_user_id,
            actor_type="admin" if admin_user_id else "system",
            action="TICKET_UPDATED",
            target_type="ticket",
            target_id=t.ticket_number,
            details=f"Ticket {t.ticket_number} status changed from '{old_status}' to '{status}'",
            status="SUCCESS",
        )
        db.add(audit)
        db.flush()

        return {"ticket_number": t.ticket_number, "status": t.status, "resolution": t.resolution}


def list_tickets_for_customer(customer_id: int, company_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    List tickets for a specific customer with optional tenant isolation.
    """
    with get_db() as db:
        query = db.query(Ticket).filter(Ticket.customer_id == customer_id)
        if company_id:
            query = query.filter(Ticket.company_id == company_id)
        tickets = query.order_by(Ticket.created_at.desc()).all()

        return [
            {
                "id": t.id,
                "ticket_number": t.ticket_number,
                "customer_id": t.customer_id,
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "status": t.status,
                "assigned_to": t.assigned_to,
                "resolution": t.resolution,
                "date": t.created_at.strftime("%d %b %Y, %I:%M %p") if t.created_at else "N/A",
            }
            for t in tickets
        ]


def list_tickets_by_company(company_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List tickets for a company with optional status filter.
    """
    with get_db() as db:
        query = db.query(Ticket).filter(Ticket.company_id == company_id)
        if status:
            query = query.filter(Ticket.status == status.lower())
        tickets = query.order_by(Ticket.created_at.desc()).all()

        return [
            {
                "id": t.id,
                "ticket_number": t.ticket_number,
                "customer_id": t.customer_id,
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "status": t.status,
                "assigned_to": t.assigned_to,
                "resolution": t.resolution,
                "date": t.created_at.strftime("%d %b %Y, %I:%M %p") if t.created_at else "N/A",
            }
            for t in tickets
        ]

