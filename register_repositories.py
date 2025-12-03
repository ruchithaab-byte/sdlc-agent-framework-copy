#!/usr/bin/env python3
"""
Register existing repositories in the database.

This script scans for Git repositories and registers them in the database
so they appear in the dashboard Analytics page.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.logging.execution_logger import ExecutionLogger
from src.utils.repository_utils import detect_repository

def register_repository(repo_path: str, user_email: str) -> bool:
    """
    Register a repository in the database.
    
    Args:
        repo_path: Path to the repository
        user_email: User email for tracking
        
    Returns:
        True if registered successfully, False otherwise
    """
    repo_info = detect_repository(repo_path)
    if not repo_info:
        print(f"❌ Not a Git repository: {repo_path}")
        return False
    
    # Initialize logger with user_email to trigger repository registration
    logger = ExecutionLogger(
        user_email=user_email,
        project_path=repo_path,
    )
    
    # Force repository registration
    logger._ensure_repository_registered()
    
    if logger._repository_id:
        print(f"✅ Registered: {repo_info['repo_name']}")
        print(f"   Path: {repo_info['repo_path']}")
        print(f"   Remote: {repo_info.get('git_remote_url', 'N/A')}")
        print(f"   Branch: {repo_info.get('git_branch', 'N/A')}")
        print(f"   Repository ID: {logger._repository_id}")
        return True
    else:
        print(f"⚠️  Failed to register: {repo_path}")
        return False

def main():
    """Main function to register repositories."""
    user_email = os.getenv("AGENT_USER_EMAIL")
    if not user_email:
        print("❌ AGENT_USER_EMAIL environment variable not set")
        print("\n📝 Set it with:")
        print("   export AGENT_USER_EMAIL='your.email@company.com'")
        print("   or add it to setup_langsmith.sh")
        return 1
    
    print(f"🔍 Registering repositories for user: {user_email}")
    print("=" * 60)
    print()
    
    # Common repository locations to scan
    repos_dir = project_root / "repos"
    registered_count = 0
    
    if repos_dir.exists():
        print(f"📂 Scanning: {repos_dir}")
        for repo_path in repos_dir.iterdir():
            if repo_path.is_dir() and not repo_path.name.startswith('.'):
                # Check if it's actually a git repo before trying to register
                if (repo_path / ".git").exists():
                    if register_repository(str(repo_path), user_email):
                        registered_count += 1
                    print()
                else:
                    print(f"⏭️  Skipping (not a git repo): {repo_path.name}")
    else:
        print(f"⚠️  Repos directory not found: {repos_dir}")
        print("   Creating it...")
        repos_dir.mkdir(parents=True, exist_ok=True)
    
    # Also register the framework itself if it's a git repo
    print("📂 Checking framework directory...")
    if register_repository(str(project_root), user_email):
        registered_count += 1
    print()
    
    print("=" * 60)
    if registered_count > 0:
        print(f"✅ Successfully registered {registered_count} repository(ies)")
        print("\n🚀 Refresh the dashboard Analytics page to see the repositories!")
    else:
        print("⚠️  No repositories were registered")
        print("\n💡 Make sure:")
        print("   1. Repositories are Git repositories (have .git directory)")
        print("   2. AGENT_USER_EMAIL is set correctly")
        print("   3. Database is accessible (logs/agent_execution.db)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

