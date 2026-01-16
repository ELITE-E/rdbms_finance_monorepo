"""
app/security.py

Security primitives:
- Password hashing + verification using native bcrypt
- JWT creation + validation using PyJWT

Standardized to bypass passlib version bugs and bcrypt 72-byte limits.
"""

from __future__ import annotations

import hashlib
import bcrypt  # Use native bcrypt instead of passlib
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from . import settings

def _pre_hash(password: str) -> bytes:
    """
    Industry standard fix for bcrypt's 72-byte limit.
    Converts password to SHA-256 hex, then returns bytes for bcrypt.
    """
    # hex-digest is 64 chars, safely under the 72-byte limit.
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using native bcrypt.
    """
    # 1. Pre-hash to handle length
    prepared_password = _pre_hash(password)
    # 2. Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared_password, salt)
    # 3. Return as string for database storage
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash string.
    """
    try:
        prepared_password = _pre_hash(password)
        # We encode the hash from the DB back to bytes for bcrypt to compare
        return bcrypt.checkpw(prepared_password, password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(*, user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except jwt.PyJWTError:
        return None