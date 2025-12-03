"""
Repository detection utilities.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


def detect_repository(project_path: str) -> Optional[dict]:
    """
    Detect Git repository information from a project path.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Dict with repo_path, repo_name, git_remote_url, git_branch, or None
    """
    project = Path(project_path).resolve()
    
    # Walk up the directory tree to find .git
    current = project
    while current != current.parent:
        git_dir = current / ".git"
        if git_dir.exists():
            repo_path = str(current)
            repo_name = current.name
            
            # Get git remote URL
            git_remote_url = None
            try:
                result = subprocess.run(
                    ["git", "config", "--get", "remote.origin.url"],
                    cwd=current,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=5,
                )
                git_remote_url = result.stdout.strip()
            except Exception:
                pass
            
            # Get current branch
            git_branch = None
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=current,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=5,
                )
                git_branch = result.stdout.strip()
            except Exception:
                pass
            
            return {
                "repo_path": repo_path,
                "repo_name": repo_name,
                "git_remote_url": git_remote_url,
                "git_branch": git_branch,
            }
        
        current = current.parent
    
    return None


def get_repo_name_from_path(repo_path: str) -> str:
    """
    Extract repository name from path.
    
    Args:
        repo_path: Full path to repository
        
    Returns:
        Repository name
    """
    return Path(repo_path).name


__all__ = ["detect_repository", "get_repo_name_from_path"]

