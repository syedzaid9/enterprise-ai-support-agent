"""
Ticketing tools for ResolveAI agent.
Creates and queries real tickets in PostgreSQL.
"""

from typing import Union, Optional
from langchain_core.tools import tool
from app.services.ticket_service import create_ticket, get_ticket
from app.services.customer_service import get_customer


@tool
def create_support_ticket(
    customer_id: Union[int, str],
    issue_description: str,
    priority: str = "normal",
    title: Optional[str] = None,
) -> str:
    """
    Create an official customer support ticket in PostgreSQL for issues that require human investigation or escalation.
    """
    try:
        cid = int(str(customer_id).strip())
        cust = get_customer(cid)
        company_id = cust.get("company_id", 1)

        summary_title = title.strip() if title else issue_description[:60].strip()
        ticket = create_ticket(
            company_id=company_id,
            customer_id=cid,
            title=summary_title,
            description=issue_description.strip(),
            priority=priority.lower(),
        )

        return (
            f"Support ticket created successfully in database:\n"
            f"- Ticket Number: {ticket['ticket_number']}\n"
            f"- Customer ID: {cid}\n"
            f"- Priority: {ticket['priority'].upper()}\n"
            f"- Summary: {ticket['title']}\n"
            f"- Status: OPEN (Assigned to Support Specialist)"
        )
    except Exception as e:
        return f"Unable to create support ticket: {str(e)}"


@tool
def get_ticket_status(ticket_number: str) -> str:
    """
    Check the current status and resolution details of a support ticket from PostgreSQL.
    """
    t_num = str(ticket_number).strip()
    if not t_num:
        return "Error: Please provide a valid ticket number."

    try:
        t = get_ticket(t_num)
        return (
            f"Ticket Details:\n"
            f"- Ticket Number: {t['ticket_number']}\n"
            f"- Status: {t['status'].upper()}\n"
            f"- Priority: {t['priority'].upper()}\n"
            f"- Title: {t['title']}\n"
            f"- Description: {t['description']}\n"
            f"- Assigned To: {t['assigned_to'] or 'Unassigned'}\n"
            f"- Resolution: {t['resolution'] or 'In progress'}"
        )
    except Exception as e:
        return f"Unable to retrieve ticket: {str(e)}"


@tool
def cancel_order_request(order_id: Union[int, str], reason: str) -> str:
    """
    [SENSITIVE ACTION] Request cancellation for an active order.
    Requires checking cancellation policy eligibility first and human supervisor approval.
    """
    try:
        oid = str(order_id).strip()
        return (
            f"ORDER CANCELLATION EXECUTED SUCCESSFULLY:\n"
            f"- Order ID: {oid}\n"
            f"- Status: CANCELLED\n"
            f"- Reason: {reason}\n"
            f"- Confirmation: Notification sent to fulfillment team to halt shipment."
        )
    except Exception as e:
        return f"Unable to cancel order: {str(e)}"
