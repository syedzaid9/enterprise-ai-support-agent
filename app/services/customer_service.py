"""
Customer Service for ResolveAI.
Provides database-backed customer retrieval and profile lookups using SQLAlchemy and PostgreSQL,
enforcing multi-tenant security boundaries.
"""

from typing import Optional, Dict, Any, List
from app.db.database import get_db
from app.db.models import Customer


def get_customer(customer_id: int, company_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Retrieve customer information from PostgreSQL database by customer ID.
    Enforces company_id boundary if specified.
    Raises ValueError if customer is not found.
    """
    with get_db() as db:
        query = db.query(Customer).filter(Customer.id == customer_id)
        if company_id:
            query = query.filter(Customer.company_id == company_id)
        customer = query.first()

        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found in database.")

        return {
            "id": customer.id,
            "user_id": customer.user_id,
            "company_id": customer.company_id,
            "external_customer_id": customer.external_customer_id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "status": customer.status,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
            "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
        }


def get_customer_by_user_id(user_id: int, company_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve customer information from PostgreSQL database by associated user ID.
    Returns None if no customer profile is linked to the user.
    """
    with get_db() as db:
        query = db.query(Customer).filter(Customer.user_id == user_id)
        if company_id:
            query = query.filter(Customer.company_id == company_id)
        customer = query.first()

        if not customer:
            return None

        return {
            "id": customer.id,
            "user_id": customer.user_id,
            "company_id": customer.company_id,
            "external_customer_id": customer.external_customer_id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "status": customer.status,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
            "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
        }


def list_customers_by_company(company_id: int) -> List[Dict[str, Any]]:
    """
    List all customer accounts belonging to a specific company tenant.
    """
    with get_db() as db:
        customers = db.query(Customer).filter(Customer.company_id == company_id).order_by(Customer.created_at.desc()).all()
        return [
            {
                "id": c.id,
                "user_id": c.user_id,
                "company_id": c.company_id,
                "external_customer_id": c.external_customer_id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in customers
        ]