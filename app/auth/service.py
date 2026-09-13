"""
Authentication and identity service for ResolveAI.
Manages customer and admin registration, password authentication, and role/tenant authorization.
Adheres strictly to the Pure Real Data principle: No simulated billing records are generated on signup.
"""

import datetime
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Company, User, Customer, AuditLog
from app.auth.security import hash_password, verify_password, create_access_token


def get_default_company(db: Session) -> Company:
    """
    Retrieve or create the primary default enterprise company.
    """
    company = db.query(Company).filter(Company.name == "ResolveAI Enterprise Corp").first()
    if not company:
        company = Company(name="ResolveAI Enterprise Corp", slug="resolveai-enterprise", status="ACTIVE")
        db.add(company)
        db.flush()
    return company


def register_customer(
    full_name: str,
    email: str,
    password: str,
    phone: Optional[str] = None,
    external_customer_id: Optional[str] = None,
    company_id: Optional[int] = None,
) -> Customer:
    """
    Register a new customer:
    1. Creates User with role='customer'
    2. Creates Customer profile attached to company
    3. Records audit log

    NOTE: Does NOT create fake subscriptions, payments, or tickets.
    """
    clean_email = email.strip().lower()
    clean_name = full_name.strip()

    if not clean_name:
        raise ValueError("Full name is required.")
    if not clean_email or "@" not in clean_email:
        raise ValueError("A valid email address is required.")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    with get_db() as db:
        existing_user = db.query(User).filter(User.email == clean_email).first()
        if existing_user:
            raise ValueError(f"An account with email '{clean_email}' already exists.")

        target_company_id = company_id
        if not target_company_id:
            company = get_default_company(db)
            target_company_id = company.id

        # 1. Create User
        user = User(
            company_id=target_company_id,
            email=clean_email,
            password_hash=hash_password(password),
            role="customer",
            is_active=True,
        )
        db.add(user)
        db.flush()

        # 2. Create Customer Profile
        customer = Customer(
            user_id=user.id,
            company_id=target_company_id,
            external_customer_id=external_customer_id.strip() if external_customer_id else None,
            name=clean_name,
            email=clean_email,
            phone=phone.strip() if phone else None,
            status="ACTIVE",
        )
        db.add(customer)
        db.flush()

        # 3. Record Audit Log
        audit = AuditLog(
            company_id=target_company_id,
            customer_id=customer.id,
            user_id=user.id,
            actor_type="user",
            action="CUSTOMER_REGISTERED",
            target_type="auth",
            target_id=str(user.id),
            details=f"New customer registered: {clean_name} ({clean_email})",
            status="SUCCESS",
        )
        db.add(audit)
        db.flush()

        db.refresh(customer)
        db.refresh(user)
        return customer


def register_admin(
    company_name: str,
    admin_name: str,
    email: str,
    password: str,
) -> User:
    """
    Register a new admin user and associate/create their company.
    """
    clean_company = company_name.strip()
    clean_admin = admin_name.strip()
    clean_email = email.strip().lower()

    if not clean_company:
        raise ValueError("Company name is required.")
    if not clean_admin:
        raise ValueError("Admin name is required.")
    if not clean_email or "@" not in clean_email:
        raise ValueError("A valid email address is required.")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    with get_db() as db:
        existing_user = db.query(User).filter(User.email == clean_email).first()
        if existing_user:
            raise ValueError(f"An account with email '{clean_email}' already exists.")

        company = db.query(Company).filter(Company.name == clean_company).first()
        if not company:
            slug = clean_company.lower().replace(" ", "-")[:50]
            company = Company(name=clean_company, slug=slug, status="ACTIVE")
            db.add(company)
            db.flush()

        user = User(
            company_id=company.id,
            email=clean_email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.flush()

        audit = AuditLog(
            company_id=company.id,
            user_id=user.id,
            actor_type="admin",
            action="ADMIN_REGISTERED",
            target_type="auth",
            target_id=str(user.id),
            details=f"Admin account created for {clean_admin} at company '{clean_company}'",
            status="SUCCESS",
        )
        db.add(audit)
        db.flush()

        db.refresh(user)
        return user


def authenticate_user(
    email: str,
    password: str,
    expected_role: Optional[str] = None,
) -> Tuple[Optional[User], Optional[str]]:
    """
    Authenticate a user by email, password, and optional expected role.
    Returns (User, None) on success, or (None, error_message) on failure.
    """
    clean_email = email.strip().lower()
    if not clean_email or not password:
        return None, "Email and password are required."

    with get_db() as db:
        user = db.query(User).filter(User.email == clean_email).first()
        if not user:
            return None, "Invalid email or password."

        if not user.is_active:
            return None, "This account is inactive. Please contact support."

        if not verify_password(password, user.password_hash):
            return None, "Invalid email or password."

        if expected_role and user.role != expected_role:
            return None, f"Access denied: Account role is '{user.role}', not '{expected_role}'."

        # Audit login
        if user.company_id:
            audit = AuditLog(
                company_id=user.company_id,
                user_id=user.id,
                actor_type=user.role,
                action="USER_LOGIN",
                target_type="auth",
                target_id=str(user.id),
                details=f"User {user.email} logged in with role '{user.role}'",
                status="SUCCESS",
            )
            db.add(audit)

        return user, None


def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Retrieve user by primary key ID.
    """
    with get_db() as db:
        return db.query(User).filter(User.id == user_id).first()


def get_customer_by_user_id(user_id: int) -> Optional[Customer]:
    """
    Retrieve Customer record associated with a User ID.
    """
    with get_db() as db:
        return db.query(Customer).filter(Customer.user_id == user_id).first()
