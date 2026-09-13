"""
Billing and payment resolution tools for ResolveAI agent.
Interacts with Cashfree Sandbox and PostgreSQL records.
"""

from typing import Optional, Union
from langchain_core.tools import tool
from app.services.payment_service import (
    get_subscription,
    get_payment,
    create_refund,
    create_customer_payment_order,
)
from app.services.subscription_service import cancel_customer_subscription


@tool
def check_subscription(subscription_id: str) -> str:
    """
    Retrieve real-time subscription details from Cashfree Sandbox and PostgreSQL database using the subscription ID.
    Use this tool whenever a customer asks about their subscription status, authorization status, recurring plan details, or renewal schedule.
    """
    sid = str(subscription_id).strip()
    if not sid:
        return "Error: Please provide a valid Subscription ID."

    try:
        sub = get_subscription(sid)

        status = sub.get("subscription_status", "UNKNOWN")
        auth_status = sub.get("authorization_status", "N/A")
        customer_details = sub.get("customer_details", {})
        plan_details = sub.get("plan_details", {})

        customer_name = customer_details.get("customer_name", "N/A")
        customer_email = customer_details.get("customer_email", "N/A")
        customer_phone = customer_details.get("customer_phone", "N/A")

        plan_id = plan_details.get("plan_id", "N/A")
        plan_name = plan_details.get("plan_name", "N/A")
        plan_type = plan_details.get("plan_type", "N/A")
        recurring_amount = plan_details.get("plan_recurring_amount", "N/A")
        currency = plan_details.get("plan_currency", "INR")

        return (
            f"Verified Subscription Details:\n"
            f"- Subscription ID: {sub.get('subscription_id', sid)}\n"
            f"- Subscription Status: {status}\n"
            f"- Authorization Status: {auth_status}\n"
            f"- Plan: {plan_name} (ID: {plan_id}, Type: {plan_type})\n"
            f"- Recurring Amount: {recurring_amount} {currency}\n"
            f"- Customer Name: {customer_name}\n"
            f"- Customer Email: {customer_email}\n"
            f"- Customer Phone: {customer_phone}\n"
            f"- Next Renewal Date: {sub.get('next_schedule_date', 'N/A')}\n"
            f"- Provider: Cashfree Recurring Sandbox"
        )
    except Exception as e:
        return f"Unable to retrieve subscription details: {str(e)}"


@tool
def check_payment(payment_id: str) -> str:
    """
    Retrieve real-time payment transaction details from Cashfree Sandbox and PostgreSQL using the Payment ID or Order ID.
    Use this tool whenever a customer asks about a payment status, transaction confirmation, amount paid, or payment date.
    """
    pid = str(payment_id).strip()
    if not pid:
        return "Error: Please provide a valid Payment ID or Order ID."

    try:
        pay = get_payment(pid)

        status = pay.get("status", pay.get("payment_status", "UNKNOWN"))
        amount = pay.get("amount", pay.get("payment_amount", 0.0))
        currency = pay.get("currency", pay.get("payment_currency", "INR"))
        payment_time = pay.get("created_at", pay.get("payment_time", "N/A"))
        order_id = pay.get("order_id", "N/A")
        payment_method = pay.get("payment_method", "N/A")

        return (
            f"Verified Payment Transaction Details:\n"
            f"- Payment ID: {pay.get('payment_id', pid)}\n"
            f"- Order ID: {order_id}\n"
            f"- Payment Status: {status}\n"
            f"- Amount: {amount} {currency}\n"
            f"- Payment Time: {payment_time}\n"
            f"- Payment Method: {payment_method}\n"
            f"- Provider: Cashfree Sandbox"
        )
    except Exception as e:
        return f"Unable to retrieve payment details: {str(e)}"


@tool
def refund_payment(
    payment_id: str,
    amount: Optional[float] = None,
    reason: Optional[str] = None
) -> str:
    """
    [SENSITIVE ACTION] Execute a financial refund for a Cashfree payment.
    This operation executes a real refund through the Cashfree Refund API and records it in the database.
    CRITICAL: Must ONLY be called after verifying policy eligibility and MUST pass through Human Supervisor Approval before execution.
    """
    pid = str(payment_id).strip()
    if not pid:
        return "Error: Please provide a valid Payment ID."

    try:
        refund_resp = create_refund(
            payment_id=pid,
            amount=amount,
            reason=reason or "Customer resolution refund"
        )
        return (
            f"CASHFREE REFUND EXECUTED SUCCESSFULLY:\n"
            f"- Refund ID: {refund_resp.get('cf_refund_id', refund_resp.get('refund_id', 'N/A'))}\n"
            f"- Status: {refund_resp.get('refund_status', 'SUCCESS')}\n"
            f"- Amount: {refund_resp.get('refund_amount', amount)} INR\n"
            f"- Note: {refund_resp.get('refund_note', reason)}"
        )
    except Exception as e:
        return f"Failed to execute Cashfree refund: {str(e)}"


@tool
def cancel_subscription_tool(
    subscription_id: str,
    reason: Optional[str] = None
) -> str:
    """
    [SENSITIVE ACTION] Cancel an active recurring subscription.
    CRITICAL: This operation requires Human Supervisor Approval before execution.
    """
    sid = str(subscription_id).strip()
    if not sid:
        return "Error: Please provide a valid Subscription ID."

    try:
        res = cancel_customer_subscription(subscription_id=sid)
        return (
            f"SUBSCRIPTION CANCELLATION EXECUTED SUCCESSFULLY:\n"
            f"- Subscription ID: {res.get('subscription_id')}\n"
            f"- Status: {res.get('status')}\n"
            f"- Reason: {reason or 'Customer requested cancellation'}"
        )
    except Exception as e:
        return f"Failed to cancel subscription: {str(e)}"


@tool
def create_payment_order_session(
    customer_id: Union[int, str],
    amount: float,
    currency: str = "INR"
) -> str:
    """
    Generate a new Cashfree Sandbox payment order session and checkout link for a customer.
    """
    try:
        cid = int(str(customer_id).strip())
        res = create_customer_payment_order(
            customer_id=cid,
            amount=amount,
            currency=currency,
        )
        return (
            f"Payment Order Initialized in Cashfree Sandbox:\n"
            f"- Order ID: {res.get('order_id')}\n"
            f"- Amount: {res.get('amount')} {res.get('currency')}\n"
            f"- Status: {res.get('status')}\n"
            f"- Checkout Link: {res.get('payment_link')}"
        )
    except Exception as e:
        return f"Failed to create payment order: {str(e)}"
