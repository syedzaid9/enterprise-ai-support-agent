"""
Subscription Service for ResolveAI.
Manages customer recurring subscriptions, provider synchronization, and cancellation workflows.
"""

import uuid
import datetime
from typing import Optional, Dict, Any, List

from app.db.database import get_db
from app.db.models import Subscription, Customer, AuditLog
from app.integrations.subscription.cashfree import CashfreeSubscriptionProvider

_sub_provider = CashfreeSubscriptionProvider()


def create_customer_subscription(
    customer_id: int,
    plan_name: str = "Pro Monthly",
    amount: float = 499.0,
    currency: str = "INR",
    return_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Initialize a recurring subscription flow with Cashfree Sandbox:
    1. Creates subscription session in Cashfree Sandbox
    2. Persists subscription record in PostgreSQL with status 'INITIALIZED'
    3. Records audit log
    """
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found.")

        sub_ref_id = f"sub_cf_{customer.id}_{uuid.uuid4().hex[:8]}"
        plan_id = f"plan_{plan_name.lower().replace(' ', '_')}"

        try:
            cf_sub = _sub_provider.create_subscription(
                subscription_id=sub_ref_id,
                plan_id=plan_id,
                customer_id=str(customer.external_customer_id or customer.id),
                customer_name=customer.name,
                customer_email=customer.email,
                customer_phone=customer.phone,
                return_url=return_url,
            )
            cf_status = cf_sub.get("subscription_status", "INITIALIZED").upper()
            sub_url = cf_sub.get("subscription_url")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Cashfree recurring subscription: {str(e)}")

        subscription = Subscription(
            company_id=customer.company_id,
            customer_id=customer.id,
            provider="cashfree",
            external_subscription_id=sub_ref_id,
            plan=plan_name,
            amount=amount,
            currency=currency,
            status=cf_status,  # Stored as actual provider status (e.g. INITIALIZED)
            started_at=datetime.datetime.now(datetime.timezone.utc),
            next_billing_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30),
        )
        db.add(subscription)
        db.flush()

        audit = AuditLog(
            company_id=customer.company_id,
            customer_id=customer.id,
            actor_type="customer",
            action="SUBSCRIPTION_INITIALIZED",
            target_type="subscription",
            target_id=str(subscription.id),
            details=f"Subscription session {sub_ref_id} created for plan '{plan_name}' (Status: {cf_status})",
            status="SUCCESS",
        )
        db.add(audit)
        db.flush()

        return {
            "subscription_id": subscription.id,
            "external_subscription_id": sub_ref_id,
            "plan": plan_name,
            "amount": amount,
            "currency": currency,
            "status": subscription.status,
            "subscription_url": sub_url,
        }


def cancel_customer_subscription(
    subscription_id: str,
    admin_user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Cancel an active subscription with Cashfree and update PostgreSQL.
    """
    sid = str(subscription_id).strip()
    if not sid:
        raise ValueError("Subscription ID must not be empty.")

    with get_db() as db:
        sub = (
            db.query(Subscription)
            .filter(
                (Subscription.external_subscription_id == sid)
                | (Subscription.id == (int(sid) if sid.isdigit() else -1))
            )
            .first()
        )

        try:
            cf_res = _sub_provider.cancel_subscription(sid)
        except Exception as e:
            # If provider fails, update local DB if requested
            cf_res = {"status": "CANCEL_REQUESTED", "message": str(e)}

        if sub:
            sub.status = "CANCELLED"
            db.flush()

            audit = AuditLog(
                company_id=sub.company_id,
                customer_id=sub.customer_id,
                user_id=admin_user_id,
                actor_type="admin" if admin_user_id else "ai_agent",
                action="SUBSCRIPTION_CANCELLED",
                target_type="subscription",
                target_id=str(sub.id),
                details=f"Subscription '{sid}' was cancelled.",
                status="SUCCESS",
            )
            db.add(audit)
            db.flush()

        return {
            "subscription_id": sid,
            "status": "CANCELLED",
            "provider_response": cf_res,
        }
