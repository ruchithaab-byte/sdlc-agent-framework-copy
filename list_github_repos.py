#!/usr/bin/env python3
"""
List all repositories for a GitHub user.

Usage:
    export GITHUB_TOKEN="ghp_..."
    python3 list_github_repos.py [username]
"""

import os
import sys
import requests
from typing import List, Dict, Optional
from datetime import datetime


def list_user_repositories(username: str, token: str) -> List[Dict]:
    """
    List all repositories for a GitHub user (including private).
    
    Uses /user/repos endpoint to get ALL repos (public + private) that the
    authenticated user has access to, then filters for the specified username.
    
    Args:
        username: GitHub username
        token: GitHub personal access token
        
    Returns:
        List of repository dictionaries
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    repos = []
    page = 1
    per_page = 100
    
    while True:
        # Use /user/repos to get ALL repos (including private) that token has access to
        # This endpoint requires authentication and returns repos where user is owner/collaborator
        url = 'https://api.github.com/user/repos'
        params = {
            'page': page,
            'per_page': per_page,
            'affiliation': 'owner,collaborator',  # Get repos where user is owner or collaborator
            'sort': 'updated',
            'direction': 'desc'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
            
            # Filter for repos owned by the specified username
            for repo in page_repos:
                if repo['owner']['login'].lower() == username.lower():
                    repos.append(repo)
            
            # Check if there are more pages
            if len(page_repos) < per_page:
                break
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}")
            break
    
    return repos


def format_repo_info(repo: Dict, index: int) -> str:
    """Format repository information for display."""
    name = repo['name']
    url = repo['html_url']
    description = repo.get('description', '') or 'No description'
    language = repo.get('language', 'N/A')
    stars = repo['stargazers_count']
    forks = repo['forks_count']
    private = '🔒 Private' if repo['private'] else '🌐 Public'
    default_branch = repo['default_branch']
    updated = repo['updated_at']
    
    # Parse and format date
    try:
        updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
        updated_str = updated_dt.strftime('%Y-%m-%d %H:%M')
    except:
        updated_str = updated[:10]
    
    return f"""{index}. {name} {private}
   URL: {url}
   Description: {description}
   Language: {language}
   Stars: {stars} | Forks: {forks}
   Default Branch: {default_branch}
   Last Updated: {updated_str}
"""


def main():
    """Main function."""
    # Get username from args or default
    username = sys.argv[1] if len(sys.argv) > 1 else 'ruchithaab-byte'
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nUsage:")
        print("  export GITHUB_TOKEN='ghp_...'")
        print("  python3 list_github_repos.py [username]")
        sys.exit(1)
    
    print("=" * 80)
    print(f"REPOSITORIES FOR: {username}")
    print("=" * 80)
    print()
    
    try:
        print(f"📡 Fetching repositories from GitHub...")
        repos = list_user_repositories(username, token)
        
        if not repos:
            print(f"No repositories found for {username}")
            return
        
        print(f"✅ Found {len(repos)} repositories")
        print()
        print("-" * 80)
        print()
        
        # Group by private/public
        public_repos = [r for r in repos if not r['private']]
        private_repos = [r for r in repos if r['private']]
        
        if public_repos:
            print(f"🌐 PUBLIC REPOSITORIES ({len(public_repos)})")
            print("-" * 80)
            for i, repo in enumerate(public_repos, 1):
                print(format_repo_info(repo, i))
        
        if private_repos:
            print(f"🔒 PRIVATE REPOSITORIES ({len(private_repos)})")
            print("-" * 80)
            for i, repo in enumerate(private_repos, 1):
                print(format_repo_info(repo, i))
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Repositories: {len(repos)}")
        print(f"  Public: {len(public_repos)}")
        print(f"  Private: {len(private_repos)}")
        print()
        
        # Languages summary
        languages = {}
        for repo in repos:
            lang = repo.get('language') or 'Unknown'
            languages[lang] = languages.get(lang, 0) + 1
        
        if languages:
            print("Languages:")
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                print(f"  {lang}: {count}")
        
        print()
        print("=" * 80)
        print("REPOSITORY URLS (for repo_registry.yaml)")
        print("=" * 80)
        print()
        for repo in repos:
            print(f"  - id: {repo['name']}")
            print(f"    github_url: {repo['html_url']}")
            print(f"    description: {repo.get('description', '') or 'No description'}")
            print(f"    branch: {repo['default_branch']}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

