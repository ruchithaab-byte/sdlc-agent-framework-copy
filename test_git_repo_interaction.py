"""
COMPREHENSIVE GIT REPOSITORY INTERACTION TEST

This test demonstrates the complete end-to-end flow of how agents interact with
Git repositories through the GitHub MCP Server integration.

Test Flow:
1. Repository Access (Authentication & Initialization)
2. Branch Creation
3. File Reading
4. File Editing (Commit)
5. Pull Request Creation
6. Error Handling (Conflicts, Credentials, Invalid Operations)

Components Tested:
- ContextOrchestrator: Session preparation with GitHub tools
- GitHubMCPServer: Direct GitHub API operations
- Tool Exposure: get_tools() method for Agent SDK
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.orchestrator.registry import RepoRegistry
from src.orchestrator.session_manager import ContextOrchestrator
from src.mcp_servers.github_server import GitHubMCPServer, GitHubServerError


class GitRepoInteractionTest:
    """Comprehensive test for Git repository interaction."""
    
    def __init__(self, test_repo_url: str, github_token: str):
        """
        Initialize test with repository URL and GitHub token.
        
        Args:
            test_repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
            github_token: GitHub personal access token
        """
        self.test_repo_url = test_repo_url
        self.github_token = github_token
        self.test_branch = f"test/agent-integration-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.test_file = "test_agent_integration.md"
        self.results = []
    
    def log_step(self, step: str, component: str, status: str, details: str = ""):
        """Log a test step with component and status."""
        result = {
            "step": step,
            "component": component,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"\n{status_icon} Step {len(self.results)}: {step}")
        print(f"   Component: {component}")
        print(f"   Status: {status}")
        if details:
            print(f"   Details: {details}")
    
    async def test_1_repository_access(self):
        """Test 1: Repository Access (Authentication & Initialization)"""
        print("\n" + "=" * 80)
        print("TEST 1: REPOSITORY ACCESS")
        print("=" * 80)
        
        # Component: ContextOrchestrator
        # Trigger: prepare_session_for_repo() or prepare_session()
        try:
            registry = RepoRegistry()
            orchestrator = ContextOrchestrator(registry, router=None)
            
            # Use sandbox repo for testing (or create a test repo entry)
            repo_id = "sandbox"
            session = orchestrator.prepare_session_for_repo(repo_id)
            
            # Verify GitHub server initialization
            if session.github_server:
                self.log_step(
                    "Repository Access",
                    "ContextOrchestrator.prepare_session_for_repo()",
                    "PASS",
                    f"GitHub server initialized for {session.repo_id}"
                )
                return session.github_server
            else:
                self.log_step(
                    "Repository Access",
                    "ContextOrchestrator.prepare_session_for_repo()",
                    "FAIL",
                    "GitHub server not initialized (GITHUB_TOKEN may be missing)"
                )
                return None
                
        except Exception as e:
            self.log_step(
                "Repository Access",
                "ContextOrchestrator",
                "FAIL",
                f"Error: {e}"
            )
            return None
    
    async def test_2_direct_github_server(self):
        """Test 2: Direct GitHub Server Initialization"""
        print("\n" + "=" * 80)
        print("TEST 2: DIRECT GITHUB SERVER INITIALIZATION")
        print("=" * 80)
        
        # Component: GitHubMCPServer
        # Trigger: Direct initialization (used by ContextOrchestrator internally)
        try:
            github_server = GitHubMCPServer(
                repo_url=self.test_repo_url,
                token=self.github_token
            )
            
            # Verify authentication
            repo = github_server._get_repo()
            repo_name = repo.full_name
            
            self.log_step(
                "GitHub Server Initialization",
                "GitHubMCPServer.__init__()",
                "PASS",
                f"Authenticated to {repo_name}"
            )
            
            # Verify tool exposure
            tools = github_server.get_tools()
            tool_names = [tool.__name__ for tool in tools]
            
            self.log_step(
                "Tool Exposure",
                "GitHubMCPServer.get_tools()",
                "PASS",
                f"Exposed {len(tools)} tools: {', '.join(tool_names)}"
            )
            
            return github_server
            
        except GitHubServerError as e:
            self.log_step(
                "GitHub Server Initialization",
                "GitHubMCPServer",
                "FAIL",
                f"GitHubServerError: {e}"
            )
            return None
        except Exception as e:
            self.log_step(
                "GitHub Server Initialization",
                "GitHubMCPServer",
                "FAIL",
                f"Unexpected error: {e}"
            )
            return None
    
    async def test_3_read_file(self, github_server: GitHubMCPServer):
        """Test 3: Read File from Repository"""
        print("\n" + "=" * 80)
        print("TEST 3: READ FILE FROM REPOSITORY")
        print("=" * 80)
        
        # Component: GitHubMCPServer.get_file_contents()
        # Trigger: Agent SDK tool invocation
        try:
            # Read README.md from main branch
            result = await github_server.get_file_contents("README.md", branch="main")
            
            if result.get("content"):
                self.log_step(
                    "Read File",
                    "GitHubMCPServer.get_file_contents()",
                    "PASS",
                    f"Read {result['path']} ({result['size']} bytes, SHA: {result['sha'][:8]}...)"
                )
                return True
            else:
                self.log_step(
                    "Read File",
                    "GitHubMCPServer.get_file_contents()",
                    "FAIL",
                    "No content returned"
                )
                return False
                
        except GitHubServerError as e:
            self.log_step(
                "Read File",
                "GitHubMCPServer.get_file_contents()",
                "FAIL",
                f"Error: {e}"
            )
            return False
    
    async def test_4_create_branch(self, github_server: GitHubMCPServer):
        """Test 4: Create Branch"""
        print("\n" + "=" * 80)
        print("TEST 4: CREATE BRANCH")
        print("=" * 80)
        
        # Component: GitHubMCPServer.create_branch()
        # Trigger: Agent SDK tool invocation
        try:
            result = await github_server.create_branch(
                new_branch=self.test_branch,
                source_branch="main"
            )
            
            if result.get("success"):
                self.log_step(
                    "Create Branch",
                    "GitHubMCPServer.create_branch()",
                    "PASS",
                    f"Created branch '{self.test_branch}' from 'main' (SHA: {result['sha'][:8]}...)"
                )
                return True
            else:
                self.log_step(
                    "Create Branch",
                    "GitHubMCPServer.create_branch()",
                    "FAIL",
                    "Branch creation returned success=False"
                )
                return False
                
        except GitHubServerError as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                self.log_step(
                    "Create Branch",
                    "GitHubMCPServer.create_branch()",
                    "WARN",
                    f"Branch already exists (expected in retry): {error_msg}"
                )
                return True  # Branch exists, can continue
            else:
                self.log_step(
                    "Create Branch",
                    "GitHubMCPServer.create_branch()",
                    "FAIL",
                    f"Error: {e}"
                )
                return False
    
    async def test_5_create_commit(self, github_server: GitHubMCPServer):
        """Test 5: Create Commit (Edit File)"""
        print("\n" + "=" * 80)
        print("TEST 5: CREATE COMMIT (EDIT FILE)")
        print("=" * 80)
        
        # Component: GitHubMCPServer.create_commit()
        # Trigger: Agent SDK tool invocation
        try:
            content = f"""# Agent Integration Test File

This file was created by the Git Repository Interaction Test.

**Test Details:**
- Created: {datetime.now().isoformat()}
- Branch: {self.test_branch}
- Component: GitHubMCPServer.create_commit()
- Purpose: Verify agent can create commits through GitHub API

## Test Flow Verification

✅ Repository access authenticated
✅ Branch created
✅ File committed
⏳ Pull request creation (next step)

## Agent Integration

This demonstrates how agents interact with Git repositories:
1. **ContextOrchestrator** prepares session with GitHub tools
2. **GitHubMCPServer** provides async GitHub operations
3. **Agent SDK** invokes tools to perform Git operations
4. **Tools exposed**: get_file_contents, create_branch, create_commit, create_pull_request
"""
            
            commit_message = f"test: Add agent integration test file [{self.test_branch}]"
            
            result = await github_server.create_commit(
                branch=self.test_branch,
                path=self.test_file,
                content=content,
                message=commit_message
            )
            
            if result.get("success"):
                self.log_step(
                    "Create Commit",
                    "GitHubMCPServer.create_commit()",
                    "PASS",
                    f"Committed {result['path']} to {result['branch']} (SHA: {result['commit_sha'][:8]}...)"
                )
                print(f"   Commit URL: {result.get('url', 'N/A')}")
                return True
            else:
                self.log_step(
                    "Create Commit",
                    "GitHubMCPServer.create_commit()",
                    "FAIL",
                    "Commit creation returned success=False"
                )
                return False
                
        except GitHubServerError as e:
            self.log_step(
                "Create Commit",
                "GitHubMCPServer.create_commit()",
                "FAIL",
                f"Error: {e}"
            )
            return False
    
    async def test_6_create_pull_request(self, github_server: GitHubMCPServer):
        """Test 6: Create Pull Request"""
        print("\n" + "=" * 80)
        print("TEST 6: CREATE PULL REQUEST")
        print("=" * 80)
        
        # Component: GitHubMCPServer.create_pull_request()
        # Trigger: Agent SDK tool invocation
        try:
            pr_title = f"[TEST] Agent Integration Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            pr_body = f"""## Agent Integration Test

This PR was created automatically by the Git Repository Interaction Test.

**Test Branch:** `{self.test_branch}`
**Test File:** `{self.test_file}`

### Components Tested

1. ✅ **ContextOrchestrator** - Session preparation with GitHub tools
2. ✅ **GitHubMCPServer** - GitHub API operations
3. ✅ **Tool Exposure** - get_tools() for Agent SDK integration
4. ✅ **Branch Creation** - create_branch() tool
5. ✅ **File Operations** - get_file_contents() and create_commit() tools
6. ✅ **PR Creation** - create_pull_request() tool

### Agent Flow

```
User Prompt
    ↓
ContextOrchestrator.prepare_session()
    ↓
GitHubMCPServer initialized
    ↓
Tools exposed via get_tools()
    ↓
Agent SDK invokes tools
    ↓
GitHub operations executed
```

### Verification

This PR demonstrates that:
- Agents can authenticate to GitHub repositories
- Agents can create branches programmatically
- Agents can read and modify files
- Agents can create commits with proper messages
- Agents can create pull requests

**Note:** This is a test PR and can be safely closed/deleted.
"""
            
            result = await github_server.create_pull_request(
                head_branch=self.test_branch,
                base_branch="main",
                title=pr_title,
                body=pr_body
            )
            
            if result.get("success"):
                self.log_step(
                    "Create Pull Request",
                    "GitHubMCPServer.create_pull_request()",
                    "PASS",
                    f"Created PR #{result['pr_number']}: {result['title']}"
                )
                print(f"   PR URL: {result.get('url', 'N/A')}")
                return result
            else:
                self.log_step(
                    "Create Pull Request",
                    "GitHubMCPServer.create_pull_request()",
                    "FAIL",
                    "PR creation returned success=False"
                )
                return None
                
        except GitHubServerError as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                self.log_step(
                    "Create Pull Request",
                    "GitHubMCPServer.create_pull_request()",
                    "WARN",
                    f"PR already exists for this branch: {error_msg}"
                )
                return {"pr_exists": True}
            else:
                self.log_step(
                    "Create Pull Request",
                    "GitHubMCPServer.create_pull_request()",
                    "FAIL",
                    f"Error: {e}"
                )
                return None
    
    async def test_7_error_handling(self, github_server: GitHubMCPServer):
        """Test 7: Error Handling (Invalid Operations)"""
        print("\n" + "=" * 80)
        print("TEST 7: ERROR HANDLING")
        print("=" * 80)
        
        # Test invalid file path
        try:
            await github_server.get_file_contents("nonexistent/file/path.md", branch="main")
            self.log_step(
                "Error Handling - Invalid File",
                "GitHubMCPServer.get_file_contents()",
                "FAIL",
                "Should have raised GitHubServerError for nonexistent file"
            )
        except GitHubServerError:
            self.log_step(
                "Error Handling - Invalid File",
                "GitHubMCPServer.get_file_contents()",
                "PASS",
                "Correctly raised GitHubServerError for nonexistent file"
            )
        except Exception as e:
            self.log_step(
                "Error Handling - Invalid File",
                "GitHubMCPServer.get_file_contents()",
                "WARN",
                f"Raised unexpected exception: {type(e).__name__}"
            )
        
        # Test invalid branch
        try:
            await github_server.create_branch("test/invalid-branch", source_branch="nonexistent-branch")
            self.log_step(
                "Error Handling - Invalid Source Branch",
                "GitHubMCPServer.create_branch()",
                "FAIL",
                "Should have raised GitHubServerError for nonexistent source branch"
            )
        except GitHubServerError:
            self.log_step(
                "Error Handling - Invalid Source Branch",
                "GitHubMCPServer.create_branch()",
                "PASS",
                "Correctly raised GitHubServerError for nonexistent source branch"
            )
        except Exception as e:
            self.log_step(
                "Error Handling - Invalid Source Branch",
                "GitHubMCPServer.create_branch()",
                "WARN",
                f"Raised unexpected exception: {type(e).__name__}"
            )
        
        # Test missing credentials
        try:
            invalid_server = GitHubMCPServer(
                repo_url=self.test_repo_url,
                token="invalid_token_12345"
            )
            await invalid_server.get_file_contents("README.md", branch="main")
            self.log_step(
                "Error Handling - Invalid Credentials",
                "GitHubMCPServer",
                "FAIL",
                "Should have raised GitHubServerError for invalid token"
            )
        except GitHubServerError:
            self.log_step(
                "Error Handling - Invalid Credentials",
                "GitHubMCPServer",
                "PASS",
                "Correctly raised GitHubServerError for invalid credentials"
            )
        except Exception as e:
            self.log_step(
                "Error Handling - Invalid Credentials",
                "GitHubMCPServer",
                "WARN",
                f"Raised exception (may be valid): {type(e).__name__}: {e}"
            )
    
    async def run_all_tests(self):
        """Run all tests in sequence."""
        print("=" * 80)
        print("GIT REPOSITORY INTERACTION TEST - COMPREHENSIVE")
        print("=" * 80)
        print(f"Test Repository: {self.test_repo_url}")
        print(f"Test Branch: {self.test_branch}")
        print(f"Test File: {self.test_file}")
        print("=" * 80)
        
        # Test 1: Repository Access via Orchestrator
        session_github = await self.test_1_repository_access()
        
        # Test 2: Direct GitHub Server (primary test)
        github_server = await self.test_2_direct_github_server()
        if not github_server:
            print("\n❌ Cannot continue - GitHub server initialization failed")
            return self.results
        
        # Test 3: Read File
        await self.test_3_read_file(github_server)
        
        # Test 4: Create Branch
        branch_created = await self.test_4_create_branch(github_server)
        if not branch_created:
            print("\n⚠️  Branch creation failed, but continuing with tests...")
        
        # Test 5: Create Commit
        if branch_created:
            await self.test_5_create_commit(github_server)
        
        # Test 6: Create Pull Request
        if branch_created:
            pr_result = await self.test_6_create_pull_request(github_server)
            if pr_result and pr_result.get("url"):
                print(f"\n📋 Pull Request Created: {pr_result['url']}")
        
        # Test 7: Error Handling
        await self.test_7_error_handling(github_server)
        
        # Cleanup
        github_server.close()
        
        return self.results
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warned = sum(1 for r in self.results if r["status"] == "WARN")
        
        print(f"Total Steps: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warned}")
        
        print("\nComponent Breakdown:")
        components = {}
        for result in self.results:
            comp = result["component"]
            if comp not in components:
                components[comp] = {"PASS": 0, "FAIL": 0, "WARN": 0}
            components[comp][result["status"]] += 1
        
        for comp, counts in components.items():
            print(f"\n  {comp}:")
            print(f"    ✅ {counts['PASS']} passed, ❌ {counts['FAIL']} failed, ⚠️  {counts['WARN']} warnings")
        
        print("\n" + "=" * 80)
        if failed == 0:
            print("✅ ALL TESTS PASSED")
        else:
            print(f"⚠️  {failed} TEST(S) FAILED")
        print("=" * 80)


async def main():
    """Main test execution."""
    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        print("   Set it with: export GITHUB_TOKEN=ghp_xxx")
        return 1
    
    # Get test repository URL from environment or discover from GitHub
    test_repo_url = os.getenv("TEST_REPO_URL")
    if not test_repo_url:
        # Try to discover a test repository
        try:
            from github import Github, Auth
            auth = Auth.Token(github_token)
            g = Github(auth=auth)
            user = g.get_user()
            
            # Look for test repos
            repos = list(user.get_repos())
            test_repos = [r for r in repos if 'test' in r.name.lower() or 'sandbox' in r.name.lower()]
            
            if test_repos:
                test_repo = test_repos[0]
                test_repo_url = test_repo.html_url
                print(f"✅ Found test repository: {test_repo.full_name}")
            elif repos:
                # Use first available repo
                test_repo = repos[0]
                test_repo_url = test_repo.html_url
                print(f"⚠️  Using available repository: {test_repo.full_name}")
            else:
                print("❌ No repositories found. Please create a test repository or set TEST_REPO_URL")
                return 1
        except Exception as e:
            print(f"❌ Could not discover repository: {e}")
            print("   Set TEST_REPO_URL environment variable with a valid GitHub repository URL")
            return 1
    
    # Run tests
    test = GitRepoInteractionTest(test_repo_url, github_token)
    results = await test.run_all_tests()
    test.print_summary()
    
    # Return exit code based on results
    failed = sum(1 for r in results if r["status"] == "FAIL")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

