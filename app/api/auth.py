"""
Authentication REST API endpoints for ResolveAI.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException, Depends, Header
from app.auth.service import register_customer, register_admin, authenticate_user, get_user_by_id
from app.auth.security import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


class CustomerRegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    phone: Optional[str] = None
    external_customer_id: Optional[str] = None
    company_id: Optional[int] = None


class AdminRegisterRequest(BaseModel):
    company_name: str
    admin_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = None


def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency to extract authenticated user from Bearer JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")

    user = get_user_by_id(int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User account not found or inactive.")
    return user


@router.post("/register")
def api_register_customer(req: CustomerRegisterRequest):
    try:
        cust = register_customer(
            full_name=req.full_name,
            email=req.email,
            password=req.password,
            phone=req.phone,
            external_customer_id=req.external_customer_id,
            company_id=req.company_id,
        )
        token = create_access_token({"sub": str(cust.user_id), "role": "customer", "company_id": cust.company_id})
        return {
            "status": "success",
            "message": "Customer registered successfully.",
            "customer_id": cust.id,
            "access_token": token,
            "token_type": "bearer",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/register-admin")
def api_register_admin(req: AdminRegisterRequest):
    try:
        user = register_admin(
            company_name=req.company_name,
            admin_name=req.admin_name,
            email=req.email,
            password=req.password,
        )
        token = create_access_token({"sub": str(user.id), "role": "admin", "company_id": user.company_id})
        return {
            "status": "success",
            "message": "Admin registered successfully.",
            "user_id": user.id,
            "access_token": token,
            "token_type": "bearer",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Admin registration failed: {str(e)}")


@router.post("/login")
def api_login(req: LoginRequest):
    user, err = authenticate_user(email=req.email, password=req.password, expected_role=req.role)
    if not user:
        raise HTTPException(status_code=401, detail=err or "Invalid credentials.")

    token = create_access_token({"sub": str(user.id), "role": user.role, "company_id": user.company_id})
    return {
        "status": "success",
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "company_id": user.company_id,
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me")
def api_get_me(current_user=Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "company_id": current_user.company_id,
    }
