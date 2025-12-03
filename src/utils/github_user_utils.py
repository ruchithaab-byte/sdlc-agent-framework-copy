"""
GitHub user information utilities.

Fetches GitHub user information from GITHUB_TOKEN and provides
helper functions to get email, username, and display name.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

try:
    from github import Github, GithubException, Auth
except ImportError:
    Github = None
    GithubException = None
    Auth = None


def get_github_user_info() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get GitHub user information from GITHUB_TOKEN.
    
    Returns:
        Tuple of (email, username, display_name) or (None, None, None) if unavailable
    """
    if Github is None:
        return None, None, None
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return None, None, None
    
    try:
        auth = Auth.Token(token)
        github = Github(auth=auth)
        user = github.get_user()
        
        # Try to get email - requires user:email scope
        email = None
        try:
            emails = user.get_emails()
            # Find primary email
            for email_obj in emails:
                if email_obj.primary:
                    email = email_obj.email
                    break
            # If no primary, use first email
            if not email and emails:
                email = emails[0].email
        except (GithubException, AttributeError):
            # Email scope not available, use username format
            pass
        
        # Fallback to username@users.noreply.github.com if no email
        if not email:
            email = f"{user.login}@users.noreply.github.com"
        
        username = user.login
        display_name = user.name or user.login
        
        github.close()
        
        return email, username, display_name
        
    except (GithubException, Exception):
        return None, None, None


def get_github_email() -> Optional[str]:
    """Get GitHub user email."""
    email, _, _ = get_github_user_info()
    return email


def get_github_username() -> Optional[str]:
    """Get GitHub username."""
    _, username, _ = get_github_user_info()
    return username


def get_github_display_name() -> Optional[str]:
    """Get GitHub display name (real name or username)."""
    _, _, display_name = get_github_user_info()
    return display_name


__all__ = [
    "get_github_user_info",
    "get_github_email",
    "get_github_username",
    "get_github_display_name",
]

