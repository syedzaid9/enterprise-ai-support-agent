"""
Customer context service for ResolveAI.
Retrieves and aggregates real-time customer profile, subscription, payment history,
and support tickets from PostgreSQL to inject into dashboards and AI resolution workflows.
"""

from typing import Optional, Dict, Any, List
from app.db.database import get_db
from app.db.models import Customer, Subscription, Payment, Ticket, Approval, AuditLog


def get_customer_context(user_id: int, company_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve comprehensive customer context for an authenticated user.
    Strictly tenant-scoped and uses only real database records.
    """
    with get_db() as db:
        query = db.query(Customer).filter(Customer.user_id == user_id)
        if company_id:
            query = query.filter(Customer.company_id == company_id)
        customer = query.first()
        if not customer:
            return None

        # Real Active / Latest Subscription
        sub = (
            db.query(Subscription)
            .filter(Subscription.customer_id == customer.id)
            .order_by(Subscription.id.desc())
            .first()
        )

        sub_data = None
        if sub:
            next_bill = sub.next_billing_date.strftime("%d %b %Y") if sub.next_billing_date else "N/A"
            sub_data = {
                "id": sub.id,
                "plan": sub.plan,
                "amount": sub.amount,
                "currency": sub.currency,
                "status": sub.status,
                "external_subscription_id": sub.external_subscription_id or f"SUB-{sub.id}",
                "provider": sub.provider,
                "next_billing_date": next_bill,
            }

        # Real Payment Records
        payments = (
            db.query(Payment)
            .filter(Payment.customer_id == customer.id)
            .order_by(Payment.created_at.desc())
            .limit(20)
            .all()
        )
        payment_list = []
        for p in payments:
            payment_list.append({
                "id": p.id,
                "payment_id": p.external_payment_id or f"PAY-{p.id}",
                "order_id": p.order_id or f"ORD-{p.id}",
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "payment_method": p.payment_method or "Cards / UPI",
                "date": p.created_at.strftime("%d %b %Y, %I:%M %p") if p.created_at else "N/A",
            })

        # Real Support Tickets
        tickets = (
            db.query(Ticket)
            .filter(Ticket.customer_id == customer.id)
            .order_by(Ticket.created_at.desc())
            .all()
        )
        ticket_list = []
        for t in tickets:
            ticket_list.append({
                "id": t.id,
                "ticket_number": t.ticket_number,
                "title": t.title,
                "description": t.description,
                "priority": t.priority,
                "status": t.status,
                "assigned_to": t.assigned_to or "Unassigned",
                "resolution": t.resolution,
                "date": t.created_at.strftime("%d %b %Y") if t.created_at else "N/A",
            })

        # Real Pending Approvals
        approvals = (
            db.query(Approval)
            .filter(Approval.customer_id == customer.id, Approval.status == "pending")
            .all()
        )
        approval_list = []
        for a in approvals:
            approval_list.append({
                "id": a.id,
                "action_type": a.action_type,
                "action_data": a.action_data,
                "reason": a.reason,
                "status": a.status,
                "date": a.created_at.strftime("%d %b %Y, %I:%M %p") if a.created_at else "N/A",
            })

        return {
            "customer_id": customer.id,
            "company_id": customer.company_id,
            "user_id": customer.user_id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone or "Not provided",
            "external_customer_id": customer.external_customer_id,
            "status": customer.status,
            "subscription": sub_data,
            "payments": payment_list,
            "tickets": ticket_list,
            "pending_approvals": approval_list,
        }


def create_customer_ticket(
    customer_id: int,
    title: str,
    description: str,
    priority: str = "normal",
    conversation_id: Optional[int] = None,
) -> Ticket:
    """
    Create a new support ticket in PostgreSQL for a customer.
    """
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found.")

        ticket_count = db.query(Ticket).filter(Ticket.company_id == customer.company_id).count()
        ticket_num = f"TK-{1000 + ticket_count + 1}"

        ticket = Ticket(
            ticket_number=ticket_num,
            company_id=customer.company_id,
            customer_id=customer.id,
            conversation_id=conversation_id,
            title=title.strip(),
            description=description.strip(),
            priority=priority.lower(),
            status="open",
        )
        db.add(ticket)
        db.flush()

        audit = AuditLog(
            company_id=customer.company_id,
            customer_id=customer.id,
            actor_type="customer",
            action="TICKET_CREATED",
            target_type="ticket",
            target_id=ticket.ticket_number,
            details=f"Ticket {ticket.ticket_number} opened: '{title}'",
            status="SUCCESS",
        )
        db.add(audit)
        db.flush()

        db.refresh(ticket)
        return ticket
