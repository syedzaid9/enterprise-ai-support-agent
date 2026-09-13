"""
Customer REST API endpoints for ResolveAI.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.api.auth import get_current_user
from app.services.customer_context import get_customer_context
from app.services.customer_service import get_customer_by_user_id

router = APIRouter(prefix="/customer", tags=["Customer Portal"])


@router.get("/profile")
def get_profile(current_user=Depends(get_current_user)):
    cust = get_customer_by_user_id(current_user.id, company_id=current_user.company_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer profile not found.")
    return cust


@router.get("/context")
def get_context(current_user=Depends(get_current_user)):
    ctx = get_customer_context(user_id=current_user.id, company_id=current_user.company_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Customer context not found.")
    return ctx
