"""
Password hashing, JWT token creation, and cryptographic verification utilities for ResolveAI authentication.
"""

import hmac
import hashlib
import os
import json
import base64
import datetime
from typing import Optional, Dict, Any

from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES

try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False

try:
    import jwt as pyjwt
    _HAS_PYJWT = True
except ImportError:
    _HAS_PYJWT = False


def hash_password(password: str) -> str:
    """
    Hash a cleartext password securely with bcrypt or PBKDF2-HMAC-SHA256.
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    if _HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    else:
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations=100000,
        )
        return f"pbkdf2_sha256${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a cleartext password against a stored hashed password.
    """
    if not plain_password or not hashed_password:
        return False

    try:
        if hashed_password.startswith("pbkdf2_sha256$"):
            parts = hashed_password.split("$")
            if len(parts) != 3:
                return False
            salt = bytes.fromhex(parts[1])
            expected_key = bytes.fromhex(parts[2])
            candidate_key = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt,
                iterations=100000,
            )
            return hmac.compare_digest(candidate_key, expected_key)
        elif _HAS_BCRYPT:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        else:
            return False
    except Exception:
        return False


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding < 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    Generate a signed JWT token containing claims.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(datetime.datetime.now(datetime.timezone.utc).timestamp())})

    if _HAS_PYJWT:
        return pyjwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Standard HS256 JWT implementation
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64_encode(json.dumps(to_encode).encode("utf-8"))
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        f"{header_b64}.{payload_b64}".encode("utf-8"),
        hashlib.sha256
    ).digest()
    sig_b64 = _b64_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a signed JWT token.
    Returns payload dictionary or None if invalid/expired.
    """
    if not token:
        return None

    try:
        if _HAS_PYJWT:
            return pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        expected_sig = hmac.new(
            JWT_SECRET.encode("utf-8"),
            f"{header_b64}.{payload_b64}".encode("utf-8"),
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(_b64_encode(expected_sig), sig_b64):
            return None

        payload = json.loads(_b64_decode(payload_b64).decode("utf-8"))
        exp = payload.get("exp")
        if exp and exp < datetime.datetime.now(datetime.timezone.utc).timestamp():
            return None  # Expired
        return payload
    except Exception:
        return None
