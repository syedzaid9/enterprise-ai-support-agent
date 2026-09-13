"""
Payment and Cashfree REST API endpoints for ResolveAI.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends

from app.api.auth import get_current_user
from app.services.payment_service import (
    create_customer_payment_order,
    get_payment,
    create_refund,
)
from app.services.customer_service import get_customer_by_user_id

router = APIRouter(prefix="/payments", tags=["Payment & Cashfree Gateway"])


class PaymentOrderRequest(BaseModel):
    amount: float
    currency: str = "INR"
    return_url: Optional[str] = None


class RefundRequest(BaseModel):
    payment_id: str
    amount: Optional[float] = None
    reason: Optional[str] = None


@router.post("/session")
def api_create_payment_order(req: PaymentOrderRequest, current_user=Depends(get_current_user)):
    cust = get_customer_by_user_id(current_user.id, company_id=current_user.company_id)
    if not cust:
        raise HTTPException(status_code=400, detail="No customer account associated with current user.")

    try:
        order = create_customer_payment_order(
            customer_id=cust["id"],
            amount=req.amount,
            currency=req.currency,
            return_url=req.return_url,
        )
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{payment_id}")
def api_get_payment(payment_id: str, current_user=Depends(get_current_user)):
    try:
        return get_payment(payment_id=payment_id, company_id=current_user.company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refund")
def api_create_refund(req: RefundRequest, current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Supervisor Admin authorization required to process refunds.")

    try:
        res = create_refund(
            payment_id=req.payment_id,
            amount=req.amount,
            reason=req.reason,
            admin_user_id=current_user.id,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
