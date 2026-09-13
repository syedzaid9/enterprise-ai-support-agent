"""
Cashfree Webhook Handler for ResolveAI.
Receives and processes asynchronous payment/subscription webhook events and updates PostgreSQL state.
"""

import json
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException

from app.db.database import get_db
from app.db.models import Payment, Subscription, AuditLog

router = APIRouter(prefix="/webhook", tags=["Webhooks"])


@router.post("/cashfree")
async def cashfree_webhook_handler(request: Request):
    """
    Handle Cashfree PG Webhook payloads.
    Verifies event type and synchronizes PostgreSQL payment and subscription statuses.
    """
    try:
        body = await request.body()
        payload: Dict[str, Any] = json.loads(body.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid webhook payload: {str(e)}")

    event_type = payload.get("type", "").upper()
    data = payload.get("data", {})

    with get_db() as db:
        if "PAYMENT" in event_type or "ORDER" in event_type:
            order_info = data.get("order", {})
            payment_info = data.get("payment", {})
            order_id = order_info.get("order_id") or data.get("order_id")
            payment_status = (payment_info.get("payment_status") or data.get("payment_status", "UNKNOWN")).upper()
            cf_payment_id = payment_info.get("cf_payment_id") or data.get("cf_payment_id")

            if order_id:
                payment = db.query(Payment).filter(Payment.order_id == order_id).first()
                if payment:
                    old_status = payment.status
                    payment.status = payment_status
                    if cf_payment_id:
                        payment.external_payment_id = str(cf_payment_id)
                    payment.provider_response = json.dumps(payload)
                    db.flush()

                    audit = AuditLog(
                        company_id=payment.company_id,
                        customer_id=payment.customer_id,
                        actor_type="system",
                        action="WEBHOOK_PAYMENT_SYNC",
                        target_type="payment",
                        target_id=str(payment.id),
                        details=f"Payment {payment.id} status synced to '{payment_status}' from webhook event '{event_type}'",
                        status="SUCCESS",
                    )
                    db.add(audit)
                    db.flush()

        elif "SUBSCRIPTION" in event_type:
            sub_info = data.get("subscription", {})
            sub_id = sub_info.get("subscription_id") or data.get("subscription_id")
            sub_status = (sub_info.get("subscription_status") or data.get("subscription_status", "UNKNOWN")).upper()

            if sub_id:
                sub = db.query(Subscription).filter(Subscription.external_subscription_id == sub_id).first()
                if sub:
                    sub.status = sub_status
                    db.flush()

                    audit = AuditLog(
                        company_id=sub.company_id,
                        customer_id=sub.customer_id,
                        actor_type="system",
                        action="WEBHOOK_SUBSCRIPTION_SYNC",
                        target_type="subscription",
                        target_id=str(sub.id),
                        details=f"Subscription {sub.id} status synced to '{sub_status}' from webhook",
                        status="SUCCESS",
                    )
                    db.add(audit)
                    db.flush()

    return {"status": "received", "event": event_type}
