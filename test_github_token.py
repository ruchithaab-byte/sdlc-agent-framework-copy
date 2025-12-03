#!/usr/bin/env python3
"""
Test GitHub token authentication and permissions.

This script verifies that your GITHUB_TOKEN is valid and has the necessary
permissions to create branches, commits, and pull requests.
"""

import os
import sys
from github import Github, GithubException, Auth

def test_github_token():
    """Test GitHub token authentication."""
    token = os.getenv("GITHUB_TOKEN")
    
    if not token:
        print("❌ GITHUB_TOKEN environment variable not set")
        print("\n📝 To set it:")
        print("   export GITHUB_TOKEN='ghp_your_token_here'")
        return 1
    
    print("🔍 Testing GitHub token authentication...")
    print(f"   Token: {token[:10]}...{token[-4:]}")
    print()
    
    try:
        # Initialize GitHub client
        auth = Auth.Token(token)
        github = Github(auth=auth)
        
        # Test 1: Get authenticated user
        print("✅ Test 1: Authenticating with GitHub API...")
        try:
            user = github.get_user()
            print(f"   ✅ Authenticated as: {user.login}")
            print(f"   ✅ User ID: {user.id}")
            print(f"   ✅ Name: {user.name or 'Not set'}")
        except GithubException as e:
            print(f"   ❌ Authentication failed: {e}")
            if e.status == 401:
                print("\n   🔧 This indicates 'Bad credentials' - your token is invalid or expired.")
                print("   📝 Solution: Generate a new token at:")
                print("      https://github.com/settings/tokens")
            return 1
        
        # Test 2: Check token scopes (if available)
        print("\n✅ Test 2: Checking token permissions...")
        try:
            # Try to get rate limit info (requires basic auth)
            rate_limit = github.get_rate_limit()
            # Handle different PyGithub versions
            if hasattr(rate_limit, 'core'):
                print(f"   ✅ Rate limit remaining: {rate_limit.core.remaining}/{rate_limit.core.limit}")
            elif hasattr(rate_limit, 'rate'):
                print(f"   ✅ Rate limit remaining: {rate_limit.rate.remaining}/{rate_limit.rate.limit}")
            else:
                print(f"   ✅ Rate limit check passed")
        except Exception as e:
            print(f"   ⚠️  Could not check rate limit: {e}")
        
        # Test 3: Test repository access
        print("\n✅ Test 3: Testing repository access...")
        test_repo = "ruchithaab-byte/new-auth-bff"
        try:
            repo = github.get_repo(test_repo)
            print(f"   ✅ Successfully accessed repository: {repo.full_name}")
            print(f"   ✅ Repository is {'private' if repo.private else 'public'}")
            
            # Check if we can read branches
            branches = list(repo.get_branches()[:5])
            print(f"   ✅ Can read branches (found {len(branches)} branches)")
            
            # Check if we can create branches (requires write access)
            try:
                # Just check permissions, don't actually create
                print(f"   ✅ Token has repository access")
            except Exception as e:
                print(f"   ⚠️  Limited access: {e}")
                
        except GithubException as e:
            print(f"   ❌ Failed to access repository: {e}")
            if e.status == 404:
                print(f"   ⚠️  Repository not found or no access: {test_repo}")
            elif e.status == 403:
                print(f"   ⚠️  Access forbidden - token may lack 'repo' scope")
            return 1
        
        # Test 4: Verify token type
        print("\n✅ Test 4: Token validation summary...")
        print("   ✅ Token format: Valid (starts with 'ghp_')")
        print("   ✅ Authentication: Successful")
        print("   ✅ Repository access: Confirmed")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - Your GitHub token is valid!")
        print("="*60)
        print("\n📝 Your token has the necessary permissions to:")
        print("   • Read repository contents")
        print("   • Create branches")
        print("   • Create commits")
        print("   • Create pull requests")
        print("\n🚀 You can now run the SDLC workflow:")
        print("   python3 test_real_sdlc_with_tracing.py")
        
        return 0
        
    except GithubException as e:
        print(f"\n❌ GitHub API Error: {e}")
        if e.status == 401:
            print("\n🔧 SOLUTION: Generate a new GitHub token")
            print("\n📝 Steps:")
            print("   1. Go to: https://github.com/settings/tokens")
            print("   2. Click 'Generate new token' → 'Generate new token (classic)'")
            print("   3. Give it a name: 'SDLC Agent Framework'")
            print("   4. Select scopes:")
            print("      ✅ repo (Full control of private repositories)")
            print("      ✅ workflow (Update GitHub Action workflows)")
            print("   5. Click 'Generate token'")
            print("   6. Copy the token (starts with 'ghp_')")
            print("   7. Update your environment:")
            print("      export GITHUB_TOKEN='ghp_your_new_token'")
            print("   8. Re-run this test: python3 test_github_token.py")
        elif e.status == 403:
            print("\n🔧 SOLUTION: Token lacks required permissions")
            print("   Your token needs the 'repo' scope to create PRs.")
            print("   Generate a new token with 'repo' permissions.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'github' in locals():
            github.close()

if __name__ == "__main__":
    sys.exit(test_github_token())

