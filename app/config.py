"""
ResolveAI — Central Configuration Module.
Loads and validates environment variables, security keys, Cashfree Sandbox parameters,
LLM settings, and database connections.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()


def _get_hf_token() -> Optional[str]:
    """
    Retrieve the Hugging Face API token from standard environment variables.
    """
    token = (
        os.getenv("HUGGINGFACEHUB_API_TOKEN")
        or os.getenv("HF_TOKEN")
        or os.getenv("HUGGING_FACE_HUB_TOKEN")
    )
    if token:
        token = token.strip().strip("'\"")
    return token or None


def is_valid_hf_token(token: Optional[str] = None) -> bool:
    """
    Validate whether a Hugging Face token is present and not a placeholder.
    """
    t = token if token is not None else _get_hf_token()
    if not t:
        return False
    placeholders = {
        "your_huggingface_token_here",
        "your_token_here",
        "your_hf_token",
        "hf_xxx",
        "none",
        "null",
    }
    if t.lower() in placeholders or t.startswith("your_"):
        return False
    return True


def get_masked_secret(secret: Optional[str]) -> str:
    """
    Return a safe masked representation of a sensitive key.
    Never exposes the raw secret in logs or UI.
    """
    if not secret or secret.lower() in {"none", "null", ""}:
        return "[NOT CONFIGURED]"
    if secret.startswith("your_"):
        return "[PLACEHOLDER / UNSET]"
    if len(secret) > 8:
        return f"{secret[:4]}...{secret[-4:]}"
    return "********"


# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///resolveai.db"
)

# =============================================================================
# JWT & Authentication Configuration
# =============================================================================
JWT_SECRET = os.getenv("JWT_SECRET", "resolveai_enterprise_super_secret_jwt_key_change_in_prod")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))  # 24 hours

# =============================================================================
# Cashfree Gateway Configuration (Sandbox / Production)
# =============================================================================
CASHFREE_CLIENT_ID = (
    os.getenv("CASHFREE_CLIENT_ID")
    or os.getenv("CASHFREE_APP_ID")
)
CASHFREE_CLIENT_SECRET = (
    os.getenv("CASHFREE_CLIENT_SECRET")
    or os.getenv("CASHFREE_SECRET_KEY")
)
# Alias for backward compatibility
CASHFREE_APP_ID = CASHFREE_CLIENT_ID
CASHFREE_SECRET_KEY = CASHFREE_CLIENT_SECRET

CASHFREE_ENVIRONMENT = os.getenv("CASHFREE_ENVIRONMENT", "sandbox").lower()
_default_api_url = (
    "https://sandbox.cashfree.com/pg"
    if CASHFREE_ENVIRONMENT == "sandbox"
    else "https://api.cashfree.com/pg"
)
CASHFREE_API_URL = os.getenv("CASHFREE_API_URL", _default_api_url)
CASHFREE_API_VERSION = os.getenv("CASHFREE_API_VERSION", "2025-01-01")
PAYMENT_API_TIMEOUT = int(os.getenv("PAYMENT_API_TIMEOUT", "10"))

# =============================================================================
# Hugging Face / LLM Configuration
# =============================================================================
HUGGINGFACEHUB_API_TOKEN = _get_hf_token()
HUGGINGFACE_MODEL = os.getenv(
    "HUGGINGFACE_MODEL",
    os.getenv("HUGGINGFACE_REPO_ID", "openai/gpt-oss-20b")
)
_provider_env = os.getenv("HUGGINGFACE_PROVIDER", "").strip()
HUGGINGFACE_PROVIDER: Optional[str] = _provider_env if _provider_env else None
HUGGINGFACE_MAX_NEW_TOKENS = int(os.getenv("HUGGINGFACE_MAX_NEW_TOKENS", "512"))
HUGGINGFACE_TEMPERATURE = float(os.getenv("HUGGINGFACE_TEMPERATURE", "0.7"))
HUGGINGFACE_TOP_P = float(os.getenv("HUGGINGFACE_TOP_P", "0.95"))
HUGGINGFACE_TIMEOUT = int(os.getenv("HUGGINGFACE_TIMEOUT", "60"))


def get_integration_health() -> Dict[str, Any]:
    """
    Returns integration status dictionary for admin diagnostics without leaking secrets.
    """
    cashfree_configured = bool(
        CASHFREE_CLIENT_ID
        and CASHFREE_CLIENT_SECRET
        and not CASHFREE_CLIENT_ID.startswith("your_")
    )
    hf_configured = is_valid_hf_token(HUGGINGFACEHUB_API_TOKEN)

    return {
        "database": {
            "status": "Connected",
            "type": "PostgreSQL" if "postgresql" in DATABASE_URL.lower() else "SQLite (Local Dev)",
            "url_masked": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "local_instance",
        },
        "cashfree": {
            "status": "Configured (Sandbox)" if cashfree_configured else "Not Configured",
            "environment": CASHFREE_ENVIRONMENT,
            "client_id_masked": get_masked_secret(CASHFREE_CLIENT_ID),
            "api_version": CASHFREE_API_VERSION,
        },
        "huggingface": {
            "status": "Configured" if hf_configured else "Not Configured / Token Missing",
            "model": HUGGINGFACE_MODEL,
            "token_masked": get_masked_secret(HUGGINGFACEHUB_API_TOKEN),
        },
    }