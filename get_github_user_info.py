#!/usr/bin/env python3
"""
Get GitHub user information from GITHUB_TOKEN.

This script fetches the authenticated GitHub user's email and username
to use for AGENT_USER_EMAIL instead of the default.
"""

import os
import sys
from github import Github, GithubException, Auth

def get_github_user_info():
    """Get GitHub user email and username from token."""
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("GITHUB_TOKEN not set", file=sys.stderr)
        return None, None
    
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
        except GithubException:
            # Email scope not available, use username format
            pass
        
        # Fallback to username@users.noreply.github.com if no email
        if not email:
            email = f"{user.login}@users.noreply.github.com"
        
        username = user.login
        name = user.name or user.login
        
        github.close()
        
        return email, username, name
        
    except GithubException as e:
        print(f"GitHub API error: {e}", file=sys.stderr)
        return None, None, None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None, None, None

if __name__ == "__main__":
    email, username, name = get_github_user_info()
    if email:
        # Output in format suitable for shell export
        print(f"export GITHUB_USER_EMAIL='{email}'")
        print(f"export GITHUB_USERNAME='{username}'")
        print(f"export GITHUB_NAME='{name}'")
        sys.exit(0)
    else:
        sys.exit(1)

