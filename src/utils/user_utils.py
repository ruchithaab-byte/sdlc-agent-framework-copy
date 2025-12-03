"""
User management utilities.
"""

from __future__ import annotations

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    return True, None


def get_user_email_from_config() -> Optional[str]:
    """
    Get user email from per-user config file.
    
    Returns:
        Email address or None if config file doesn't exist
    """
    from pathlib import Path
    
    config_file = Path.home() / ".agent_user_email"
    if config_file.exists():
        try:
            email = config_file.read_text().strip()
            if email and validate_email(email):
                return email
        except Exception:
            pass
    
    return None


def get_user_email_from_env() -> Optional[str]:
    """
    Get user email with priority order:
    1. AGENT_USER_EMAIL environment variable
    2. ~/.agent_user_email config file
    
    Returns:
        Email address or None if not set
    """
    import os
    
    # Priority 1: Environment variable (highest priority)
    email = os.getenv("AGENT_USER_EMAIL")
    if email and validate_email(email):
        return email
    
    # Priority 2: Config file
    email = get_user_email_from_config()
    if email:
        return email
    
    return None


__all__ = [
    "validate_email",
    "validate_password_strength",
    "get_user_email_from_env",
    "get_user_email_from_config",
]

