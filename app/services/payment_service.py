"""
Payment Service for ResolveAI.
Orchestrates payment operations, database persistence, Cashfree Sandbox integration,
and refund management.
"""

import uuid
import json
import datetime
from typing import Optional, Dict, Any, List

from app.db.database import get_db
from app.db.models import Payment, Customer, AuditLog
from app.integrations.payment.cashfree import CashfreePaymentProvider
from app.integrations.subscription.cashfree import CashfreeSubscriptionProvider

_payment_provider = CashfreePaymentProvider()
_subscription_provider = CashfreeSubscriptionProvider()


def create_customer_payment_order(
    customer_id: int,
    amount: float,
    currency: str = "INR",
    payment_method: str = "UPI / Cards (Cashfree Sandbox)",
    return_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Initialize a real Cashfree Sandbox payment order:
    1. Creates order with Cashfree Sandbox API
    2. Persists payment record in PostgreSQL with status 'INITIALIZED'
    3. Records audit log
    4. Returns checkout details / payment_link
    """
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found.")

        order_id = f"ord_cf_{customer.id}_{uuid.uuid4().hex[:8]}"

        try:
            cf_order = _payment_provider.create_payment_order(
                order_id=order_id,
                amount=amount,
                currency=currency,
                customer_id=str(customer.external_customer_id or customer.id),
                customer_email=customer.email,
                customer_phone=customer.phone,
                return_url=return_url,
            )
            cf_session_id = cf_order.get("payment_session_id")
            cf_status = cf_order.get("order_status", "INITIALIZED").upper()
            provider_resp = json.dumps(cf_order)
            checkout_link = cf_order.get("payment_link")
        except Exception as e:
            # If provider is not reachable/configured, raise explicit error rather than inventing success
            raise RuntimeError(f"Could not initialize Cashfree Sandbox payment: {str(e)}")

        payment = Payment(
            company_id=customer.company_id,
            customer_id=customer.id,
            provider="cashfree",
            external_payment_id=cf_session_id or f"pay_sess_{uuid.uuid4().hex[:8]}",
            order_id=order_id,
            amount=amount,
            currency=currency,
            status=cf_status,  # Stored as actual provider status (e.g. INITIALIZED)
            payment_method=payment_method,
            provider_response=provider_resp,
        )
        db.add(payment)
        db.flush()

        audit = AuditLog(
            company_id=customer.company_id,
            customer_id=customer.id,
            actor_type="customer",
            action="PAYMENT_SESSION_CREATED",
            target_type="payment",
            target_id=str(payment.id),
            details=f"Initiated sandbox payment order {order_id} for ₹{amount} {currency} (Status: {cf_status})",
            status="SUCCESS",
        )
        db.add(audit)
        db.flush()

        return {
            "payment_id": payment.id,
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "status": payment.status,
            "payment_session_id": cf_session_id,
            "payment_link": checkout_link,
        }


def get_payment(payment_id: str, company_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Retrieve payment information from PostgreSQL and/or Cashfree Sandbox.
    """
    pid = str(payment_id).strip()
    if not pid:
        raise ValueError("Payment ID must not be empty.")

    with get_db() as db:
        # Search by external_payment_id, order_id, or database primary key
        query = db.query(Payment)
        if company_id:
            query = query.filter(Payment.company_id == company_id)

        payment = (
            query.filter(
                (Payment.external_payment_id == pid)
                | (Payment.order_id == pid)
                | (Payment.id == (int(pid) if pid.isdigit() else -1))
            )
            .first()
        )

        if payment:
            # Optionally query live status if order_id exists
            live_status = payment.status
            try:
                if payment.order_id and not payment.order_id.startswith("local_"):
                    payments_info = _payment_provider.get_order_payments(payment.order_id)
                    if isinstance(payments_info, list) and payments_info:
                        latest = payments_info[0]
                        live_status = latest.get("payment_status", payment.status).upper()
                        payment.status = live_status
                        db.commit()
            except Exception:
                pass

            return {
                "id": payment.id,
                "payment_id": payment.external_payment_id or str(payment.id),
                "order_id": payment.order_id,
                "customer_id": payment.customer_id,
                "company_id": payment.company_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "payment_method": payment.payment_method,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
            }

    # Fallback to direct provider query if not in local DB
    try:
        cf_payment = _payment_provider.get_payment_status(pid)
        return {
            "payment_id": cf_payment.get("cf_payment_id") or pid,
            "order_id": cf_payment.get("order_id", "N/A"),
            "amount": cf_payment.get("payment_amount", 0.0),
            "currency": cf_payment.get("payment_currency", "INR"),
            "status": cf_payment.get("payment_status", "UNKNOWN"),
            "payment_method": cf_payment.get("payment_method", "N/A"),
            "created_at": cf_payment.get("payment_time"),
        }
    except Exception as e:
        raise ValueError(f"Payment '{pid}' not found in database or Cashfree: {str(e)}")


def get_subscription(subscription_id: str, company_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Retrieve subscription information from Cashfree Sandbox or database.
    """
    sid = str(subscription_id).strip()
    if not sid:
        raise ValueError("Subscription ID must not be empty.")

    try:
        return _subscription_provider.get_subscription_status(sid)
    except Exception as e:
        # Check local DB
        with get_db() as db:
            from app.db.models import Subscription
            query = db.query(Subscription)
            if company_id:
                query = query.filter(Subscription.company_id == company_id)
            sub = query.filter(
                (Subscription.external_subscription_id == sid)
                | (Subscription.id == (int(sid) if sid.isdigit() else -1))
            ).first()

            if sub:
                return {
                    "subscription_id": sub.external_subscription_id or str(sub.id),
                    "subscription_status": sub.status,
                    "plan_details": {
                        "plan_name": sub.plan,
                        "plan_recurring_amount": sub.amount,
                        "plan_currency": sub.currency,
                    },
                    "next_schedule_date": sub.next_billing_date.isoformat() if sub.next_billing_date else None,
                }

        raise ValueError(f"Subscription '{sid}' not found in Cashfree Sandbox or database: {str(e)}")


def create_refund(
    payment_id: str,
    amount: Optional[float] = None,
    reason: Optional[str] = None,
    order_id: Optional[str] = None,
    admin_user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a refund for a payment via Cashfree Refund API and update PostgreSQL.
    """
    pid = str(payment_id).strip()
    if not pid:
        raise ValueError("Payment ID must not be empty.")

    with get_db() as db:
        payment = (
            db.query(Payment)
            .filter(
                (Payment.external_payment_id == pid)
                | (Payment.order_id == pid)
                | (Payment.id == (int(pid) if pid.isdigit() else -1))
            )
            .first()
        )

        target_order = order_id or (payment.order_id if payment else pid)
        refund_amount = amount or (payment.amount if payment else None)

        try:
            cf_refund = _payment_provider.request_refund(
                payment_id=pid,
                order_id=target_order,
                amount=refund_amount,
                reason=reason,
            )
        except Exception as e:
            raise RuntimeError(f"Cashfree Sandbox refund execution failed: {str(e)}")

        # Update DB if record exists
        if payment:
            payment.status = "REFUNDED"
            db.flush()

            audit = AuditLog(
                company_id=payment.company_id,
                customer_id=payment.customer_id,
                user_id=admin_user_id,
                actor_type="admin" if admin_user_id else "ai_agent",
                action="REFUND_EXECUTED",
                target_type="payment",
                target_id=str(payment.id),
                details=f"Refund of ₹{refund_amount} executed for payment '{pid}'. Reason: {reason}",
                status="SUCCESS",
            )
            db.add(audit)
            db.flush()

        return cf_refund