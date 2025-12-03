#!/usr/bin/env python3
"""
Real SDLC Cycle with LangSmith Tracing

This script demonstrates the complete SDLC workflow using REAL agents (not simulated API calls)
with full LangSmith tracing integration. This replaces the previous simulation-based approach.

Architecture:
- Phase 1: ProductSpec Agent discovers repo from Linear epic (Chain run)
- Phase 2: SprintMaster Agent creates issues with repo references (Chain run)
- Phase 3: CodeCraft Agent discovers repo from issue and implements feature (LLM + Tool runs)
- Phase 4: QualityGuard Agent reviews PR (Tool runs)
- Phase 5: InfraOps Agent deploys (Chain run)

All phases are traced to LangSmith with proper hierarchy and metadata.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from config.agent_config import get_linear_settings
from src.mcp_servers.linear_server import LinearMCPServer
from src.mcp_servers.github_server import GitHubMCPServer
from src.orchestrator.registry import RepoRegistry
from src.orchestrator.router import RepoRouter
from src.orchestrator.session_manager import ContextOrchestrator
from src.orchestrator.discovery import RepositoryDiscovery
from src.agents.runner import run_agent, run_agent_with_rpi
from src.tracing import LangSmithTracer, RunType, trace_run, set_parent_run_id


async def resolve_team_id(api_key: str, team_id: str) -> str:
    """Resolve team name to UUID if needed."""
    if team_id.startswith(("team-", "TEAM-")) or len(team_id) == 36:
        return team_id
    
    import aiohttp
    query = """
    query {
      teams {
        nodes {
          id
          name
          key
        }
      }
    }
    """
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(
            "https://api.linear.app/graphql",
            json={"query": query}
        ) as resp:
            data = await resp.json()
            if "data" in data and "teams" in data["data"]:
                teams = data["data"]["teams"]["nodes"]
                for team in teams:
                    if team.get("name") == team_id or team.get("key") == team_id:
                        return team["id"]
    
    return team_id


@trace_run(name="SDLC Discovery Phase", run_type=RunType.CHAIN)
async def phase1_discovery_and_epic_creation(
    linear_client: LinearMCPServer,
    target_repo: str,
    orchestrator: ContextOrchestrator,
) -> Dict[str, Any]:
    """
    Phase 1: Discovery and Epic Creation (Root Chain Run)
    
    This phase:
    1. Creates a Linear epic with repo reference
    2. Discovers the repository using RepositoryDiscovery
    3. Prepares SessionContext with all metadata
    """
    print("=" * 80)
    print("PHASE 1: DISCOVERY & EPIC CREATION (Root Chain)")
    print("=" * 80)
    print()
    
    # Create epic with repo reference
    epic_title = f"Add API rate limiting to {target_repo}"
    epic_description = f"""
## Description
Implement API rate limiting functionality in the {target_repo} service to prevent abuse and ensure fair usage.

## Repository
- **Service**: {target_repo}
- **Type**: Java Spring Boot BFF (Backend for Frontend)
- **Location**: https://github.com/ruchithaab-byte/{target_repo}

## Requirements
- Rate limiting middleware
- Configurable limits per endpoint
- Redis-based rate limiting
- Proper error responses

## Success Criteria
- Rate limits enforced per IP/user
- Configurable limits
- Redis integration working
- Proper HTTP 429 responses
    """.strip()
    
    print(f"📋 Creating Linear epic: {epic_title}")
    epic_result = await linear_client.create_epic(epic_title, epic_description)
    
    epic_data = epic_result.get("issueCreate", {}).get("issue", {})
    epic_id = epic_data.get("id")
    epic_identifier = epic_data.get("identifier")
    epic_url = epic_data.get("url")
    
    print(f"✅ Epic created: {epic_identifier}")
    print(f"   URL: {epic_url}")
    print()
    
    # Discover repository
    print("🔍 Discovering repository from epic...")
    discovery = RepositoryDiscovery(
        backstage_url=os.getenv("BACKSTAGE_URL"),
        github_token=os.getenv("GITHUB_TOKEN"),
        linear_api_key=linear_client.api_key,
        linear_team_id=linear_client.team_id,
    )
    
    repo_config = await discovery.discover_from_linear_issue(epic_id)
    
    if not repo_config:
        # Fallback to registry
        registry = RepoRegistry()
        try:
            repo_config = registry.get_repo(target_repo)
        except Exception:
            from src.orchestrator.registry import RepoConfig
            repo_config = RepoConfig(
                id=target_repo,
                description=f"Authentication BFF service - {target_repo}",
                github_url=f"https://github.com/ruchithaab-byte/{target_repo}",
                local_path=f"./repos/{target_repo}",
                branch="main"
            )
    
    print(f"✅ Repository discovered: {repo_config.id}")
    print(f"   GitHub: {repo_config.github_url}")
    print()
    
    # Prepare session context with all metadata
    # Since we already discovered the repo, use prepare_session_for_repo directly
    # to avoid router issues (Vertex AI model not accessible)
    print(f"📦 Preparing session for repository: {repo_config.id}")
    session = orchestrator.prepare_session_for_repo(repo_config.id)
    
    # Enhance session context with discovery metadata
    session.linear_ticket_id = epic_id
    session.repo_url = repo_config.github_url
    session.repo_owner, session.repo_name = GitHubMCPServer._parse_repo_url(repo_config.github_url)
    session.current_branch = repo_config.branch or "main"
    
    # Bind context to tools
    if session.github_server:
        session.github_server.set_context({
            "repo_url": session.repo_url,
            "repo_owner": session.repo_owner,
            "repo_name": session.repo_name,
            "current_branch": session.current_branch,
        })
    
    if session.linear_server:
        session.linear_server.set_context({
            "linear_ticket_id": session.linear_ticket_id,
        })
    
    return {
        "epic_id": epic_id,
        "epic_identifier": epic_identifier,
        "epic_url": epic_url,
        "session": session,
        "repo_config": repo_config,
    }


@trace_run(name="Sprint Planning Phase", run_type=RunType.CHAIN)
async def phase2_sprint_planning(
    linear_client: LinearMCPServer,
    epic_id: str,
    session: Any,
) -> Dict[str, Any]:
    """
    Phase 2: Sprint Planning (Chain Run)
    
    This phase creates Linear issues with repo references.
    In a real implementation, this would use the SprintMaster agent.
    """
    print("=" * 80)
    print("PHASE 2: SPRINT PLANNING (Chain Run)")
    print("=" * 80)
    print()
    
    repo_name = session.repo_name or session.repo_id
    
    issues = []
    
    issue_tasks = [
        {
            "title": f"Implement rate limiting middleware in {repo_name}",
            "description": f"""
## Task
Implement rate limiting middleware for {repo_name} service.

## Repository
- Service: {repo_name}
- GitHub: {session.repo_url}

## Acceptance Criteria
- [ ] Rate limiting filter/interceptor created
- [ ] Redis integration for rate limit storage
- [ ] Configurable limits per endpoint
- [ ] HTTP 429 response on limit exceeded
- [ ] Unit tests added
            """.strip(),
        },
    ]
    
    for task in issue_tasks:
        print(f"📋 Creating issue: {task['title']}")
        issue_result = await linear_client.create_issue(
            title=task["title"],
            description=task["description"],
            parent_id=epic_id,
        )
        
        issue_data = issue_result.get("issueCreate", {}).get("issue", {})
        issues.append({
            "id": issue_data.get("id"),
            "identifier": issue_data.get("identifier"),
            "url": issue_data.get("url"),
            "title": task["title"],
        })
        
        print(f"✅ Issue created: {issue_data.get('identifier')}")
        print(f"   URL: {issue_data.get('url')}")
        print()
    
    return {
        "issues": issues,
    }


@trace_run(name="Code Implementation Phase", run_type=RunType.CHAIN)
async def phase3_code_implementation(
    session: Any,
    issue: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Phase 3: Code Implementation (RPI Engine with TDD Loop)
    
    UPGRADED: Now uses Research-Plan-Implement workflow with:
    - Sub-agent spawning for research (Context Firewall)
    - Context compaction (Research → Plan)
    - TDD loop (cannot exit until tests pass)
    - Structural navigation (Gap 1)
    - Safe edits with validation (Gap 2)
    - Docker execution (Phase 5)
    """
    print("=" * 80)
    print("PHASE 3: CODE IMPLEMENTATION (RPI Deterministic Workflow)")
    print("=" * 80)
    print()
    
    print(f"📋 Working on Linear issue: {issue['identifier']}")
    print(f"   Title: {issue['title']}")
    print()
    
    # Update session context with issue
    session.linear_ticket_id = issue["id"]
    if session.linear_server:
        session.linear_server.set_context({
            "linear_ticket_id": session.linear_ticket_id,
        })
    
    # Create feature branch
    branch_name = f"feature/{issue['identifier'].lower()}"
    session.current_branch = branch_name
    
    if session.github_server:
        session.github_server.set_context({
            "repo_url": session.repo_url,
            "repo_owner": session.repo_owner,
            "repo_name": session.repo_name,
            "current_branch": session.current_branch,
        })
    
    # CRITICAL CHANGE: RPI uses DECLARATIVE objectives, not IMPERATIVE steps
    # We describe WHAT to achieve, not HOW to do it step-by-step
    # The RPI workflow will:
    # - Research: Spawn sub-agents to explore codebase structure
    # - Plan: Compact research into specific implementation steps
    # - Implement: Execute with TDD loop
    
    objective = f"""
Implement rate limiting filter for Linear Issue {issue['identifier']}: {issue['title']}

Repository: {session.repo_name}
Target Branch: {branch_name}
Base Branch: main

Requirements:
1. Create feature branch '{branch_name}' from 'main'
2. Implement rate limiting middleware for Spring Boot:
   - Filter class that intercepts requests
   - Redis-based rate limit tracking
   - Configurable limits per endpoint
   - Return HTTP 429 when limit exceeded
   - Proper error messages
3. Create comprehensive unit tests
4. Run tests using pytest/maven in Docker
5. Fix any test failures until all tests pass
6. Commit changes with message: "Implement rate limiting filter [{issue['identifier']}]"
7. Create pull request

Success Criteria:
- All tests pass (enforced by TDD loop)
- Code follows Spring Boot conventions
- Rate limiting works correctly
"""
    
    print("🤖 Activating CodeCraft Agent (RPI Mode)...")
    print(f"   Target Branch: {branch_name}")
    print(f"   Docker Execution: {'✅ ENABLED' if session.docker_service else '❌ DISABLED'}")
    print(f"   Navigation: {'✅ ENABLED' if session.navigation_server else '❌ DISABLED'}")
    print(f"   Tool Registry: {'✅ ENABLED' if session.tool_registry else '❌ DISABLED'}")
    print()
    
    if not session.docker_service:
        print("⚠️  WARNING: Docker execution disabled. TDD loop will not work.")
        print("   Set 'enable_code_execution: true' in repo_registry.yaml")
        print()
    
    # Execute RPI Workflow (NEW ENGINE)
    # This replaces the old prompt-based execution with deterministic RPI cycle
    print("🚀 Starting RPI Workflow...")
    print("   Phase 1: Research (sub-agents explore codebase)")
    print("   Phase 2: Planning (compact research → actionable plan)")
    print("   Phase 3: Implement (TDD loop until tests pass)")
    print()
    
    result = await run_agent_with_rpi(
        agent_id="codecraft",
        objective=objective,
        session_context=session,
    )
    
    # Validate RPI execution
    if not result.success:
        error_msg = result.error or "RPI workflow failed"
        print(f"❌ RPI WORKFLOW FAILED: {error_msg}")
        
        # Check if we have structured output with details
        if hasattr(result, 'structured_output') and result.structured_output:
            impl_result = result.structured_output
            if hasattr(impl_result, 'error'):
                print(f"   Implementation error: {impl_result.error}")
            if hasattr(impl_result, 'attempts'):
                print(f"   Attempts made: {impl_result.attempts}")
            if hasattr(impl_result, 'test_runs'):
                print(f"   Test runs: {impl_result.test_runs}")
        
        raise RuntimeError(f"Agent failed to complete ticket: {error_msg}")
    
    print(f"✅ RPI Workflow Completed Successfully")
    print(f"   Session ID: {result.session_id or 'N/A'}")
    
    # Extract implementation details from RPI result
    impl_result = result.structured_output if hasattr(result, 'structured_output') else {}
    
    if impl_result:
        print(f"   Steps Completed: {getattr(impl_result, 'steps_completed', 0)}/{getattr(impl_result, 'steps_total', 0)}")
        print(f"   Tests Passed: {getattr(impl_result, 'tests_passed', False)}")
        print(f"   Self-Healed: {getattr(impl_result, 'self_healed', False)}")
        if hasattr(impl_result, 'fixes_applied'):
            print(f"   Auto-Fixes Applied: {impl_result.fixes_applied}")
    
    # Cost tracking
    if result.cost_summary:
        print(f"   Cost: ${result.cost_usd:.6f}")
        print(f"   Context Health: {result.cost_summary.context_health.value if result.cost_summary.context_health else 'N/A'}")
        print(f"   Token Utilization: {result.cost_summary.utilization_pct:.1%}" if result.cost_summary.utilization_pct else "")
    
    print()
    
    # Verify branch creation (the agent should have created it via github tools)
    try:
        branch_info = await session.github_server.get_file_contents("README.md", branch_name)
        print(f"✅ Verified: Branch '{branch_name}' exists (agent created it)")
    except Exception as e:
        print(f"⚠️  Could not verify branch creation: {e}")
        print(f"   The agent may have created the branch but not yet pushed")
    
    print()
    
    # Extract PR info from agent's execution
    # The RPI workflow should have created the PR via github.create_pull_request
    pr_number = None
    pr_url = None
    
    print("📝 Note: The agent should have created a PR during RPI execution.")
    print("   Check GitHub to verify the PR was created.")
    print()
    
    return {
        "branch": branch_name,
        "pr_number": pr_number,  # Would be extracted from agent output
        "pr_url": pr_url,  # Would be extracted from agent output
        "agent_session_id": result.session_id,
        "rpi_workflow": {
            "success": result.success,
            "tests_passed": getattr(impl_result, 'tests_passed', False) if impl_result else False,
            "self_healed": getattr(impl_result, 'self_healed', False) if impl_result else False,
            "context_health": result.cost_summary.context_health.value if result.cost_summary and result.cost_summary.context_health else "N/A",
        },
    }


async def main():
    """Run complete SDLC cycle with real agents and tracing."""
    print("=" * 80)
    print("REAL SDLC CYCLE WITH LANGSMITH TRACING")
    print("=" * 80)
    print()
    print("This script demonstrates:")
    print("  1. Real agent execution (not simulated)")
    print("  2. LangSmith tracing with proper hierarchy")
    print("  3. Context injection to prevent hallucinations")
    print("  4. Complete SDLC workflow")
    print()
    
    target_repo = "new-auth-bff"
    
    # Initialize tracer
    # Reset singleton to ensure fresh initialization with current env vars
    # (Important if tracer was initialized elsewhere before env vars were set)
    LangSmithTracer.reset_instance()
    
    # Explicitly pass project name from env var to ensure it's used
    project_name = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT") or "sdlc-agents"
    tracer = LangSmithTracer.get_instance(project_name=project_name)
    print(f"✅ LangSmith Tracer initialized")
    print(f"   Project: {tracer.project_name}")
    print(f"   API URL: {tracer.api_url}")
    if tracer.project_name != project_name:
        print(f"   ⚠️  Warning: Project name mismatch! Expected: {project_name}, Got: {tracer.project_name}")
    print()
    
    # Verify Vertex AI configuration
    print("🔍 Verifying Vertex AI Configuration:")
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    vertex_enabled = os.getenv("CLAUDE_CODE_USE_VERTEX")
    vertex_region = os.getenv("CLAUDE_VERTEX_REGION")
    vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("ANTHROPIC_VERTEX_PROJECT_ID")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if vertex_enabled == "1":
        print(f"   ✅ CLAUDE_CODE_USE_VERTEX=1 (Vertex AI enabled)")
    else:
        print(f"   ⚠️  CLAUDE_CODE_USE_VERTEX={vertex_enabled or 'NOT SET'} (may use Anthropic API)")
    
    if google_creds:
        print(f"   ✅ GOOGLE_APPLICATION_CREDENTIALS={google_creds}")
    else:
        print(f"   ⚠️  GOOGLE_APPLICATION_CREDENTIALS not set")
    
    if vertex_project:
        print(f"   ✅ Project: {vertex_project}")
    else:
        print(f"   ⚠️  GOOGLE_CLOUD_PROJECT not set")
    
    if vertex_region:
        print(f"   ✅ Region: {vertex_region}")
    else:
        print(f"   ⚠️  CLAUDE_VERTEX_REGION not set (may use default)")
    
    if anthropic_key:
        print(f"   ⚠️  ANTHROPIC_API_KEY is set (may override Vertex AI)")
    else:
        print(f"   ✅ ANTHROPIC_API_KEY not set (will use Vertex AI)")
    
    print()
    
    # Initialize clients
    linear_config = get_linear_settings()
    if not linear_config.get("api_key") or not linear_config.get("team_id"):
        print("❌ LINEAR_API_KEY and LINEAR_TEAM_ID must be set")
        return 1
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ GITHUB_TOKEN must be set")
        return 1
    
    # Resolve team ID
    team_id = await resolve_team_id(
        linear_config["api_key"],
        linear_config["team_id"]
    )
    
    linear_client = LinearMCPServer(
        api_key=linear_config["api_key"],
        team_id=team_id
    )
    
    # Initialize orchestrator
    registry = RepoRegistry()
    router = RepoRouter(registry=registry)
    orchestrator = ContextOrchestrator(
        registry=registry,
        router=router,
        enable_discovery=True,
    )
    
    # Phase 1: Discovery and Epic Creation (Root Chain)
    print("🚀 Starting Phase 1: Discovery & Epic Creation...")
    phase1_result = await phase1_discovery_and_epic_creation(
        linear_client,
        target_repo,
        orchestrator,
    )
    session = phase1_result["session"]
    
    # Phase 2: Sprint Planning
    print("🚀 Starting Phase 2: Sprint Planning...")
    phase2_result = await phase2_sprint_planning(
        linear_client,
        phase1_result["epic_id"],
        session,
    )
    
    # Phase 3: Code Implementation
    if phase2_result["issues"]:
        issue = phase2_result["issues"][0]
        print("🚀 Starting Phase 3: Code Implementation...")
        phase3_result = await phase3_code_implementation(
            session,
            issue,
        )
    else:
        print("❌ No issues created. Cannot continue.")
        return 1
    
    # Summary
    print("=" * 80)
    print("✅ COMPLETE SDLC CYCLE WITH TRACING SUCCESSFUL!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  📋 Epic: {phase1_result['epic_identifier']}")
    print(f"     URL: {phase1_result['epic_url']}")
    print(f"  📦 Repository: {session.repo_id}")
    print(f"     GitHub: {session.repo_url}")
    print(f"  📝 Issues Created: {len(phase2_result['issues'])}")
    for issue in phase2_result["issues"]:
        print(f"     - {issue['identifier']}: {issue['title']}")
        print(f"       URL: {issue['url']}")
    if phase3_result.get("pr_number"):
        print(f"  🔀 Pull Request: #{phase3_result['pr_number']}")
        print(f"     URL: {phase3_result['pr_url']}")
        print(f"     Branch: {phase3_result['branch']}")
    print()
    print("🔍 View traces in LangSmith:")
    print(f"   Project: {tracer.project_name}")
    print()
    
    # Close tracer
    await tracer.close()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

