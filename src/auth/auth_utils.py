"""
Authentication utilities for password hashing and JWT token management.
"""

from __future__ import annotations

import hashlib
import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt


def get_jwt_secret() -> str:
    """Get JWT secret from environment variable."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET environment variable is required. "
            "Set it in your .env file or environment."
        )
    return secret


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password: Plain text password
        password_hash: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except Exception:
        return False


def generate_jwt_token(
    user_email: str,
    is_admin: bool = False,
    expires_in_hours: int = 24,
) -> tuple[str, str]:
    """
    Generate a JWT token for a user.
    
    Args:
        user_email: User's email address
        is_admin: Whether user is an admin
        expires_in_hours: Token expiration time in hours
        
    Returns:
        Tuple of (token, jti) where jti is the token ID for revocation
    """
    secret = get_jwt_secret()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=expires_in_hours)
    
    # Generate unique token ID (jti)
    jti = hashlib.sha256(
        f"{user_email}{now.isoformat()}{os.urandom(16).hex()}".encode()
    ).hexdigest()
    
    payload = {
        "email": user_email,
        "is_admin": is_admin,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": jti,
    }
    
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, jti


def verify_jwt_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        secret = get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_from_token(token: str) -> Optional[dict]:
    """
    Extract user information from a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dict with email and is_admin if valid, None otherwise
    """
    payload = verify_jwt_token(token)
    if payload:
        return {
            "email": payload.get("email"),
            "is_admin": payload.get("is_admin", False),
            "jti": payload.get("jti"),
        }
    return None


__all__ = [
    "hash_password",
    "verify_password",
    "generate_jwt_token",
    "verify_jwt_token",
    "get_user_from_token",
    "get_jwt_secret",
]

