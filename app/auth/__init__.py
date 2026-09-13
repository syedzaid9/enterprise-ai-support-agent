"""
ResolveAI Authentication Package.
"""

from app.auth.security import hash_password, verify_password
from app.auth.service import (
    register_customer,
    register_admin,
    authenticate_user,
    get_user_by_id,
    get_customer_by_user_id,
)

__all__ = [
    "hash_password",
    "verify_password",
    "register_customer",
    "register_admin",
    "authenticate_user",
    "get_user_by_id",
    "get_customer_by_user_id",
]
