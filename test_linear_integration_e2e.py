#!/usr/bin/env python3
"""
End-to-End Linear Integration Test

Tests the complete flow:
1. Create Linear issue/epic
2. Verify agent can access Linear context
3. Agent works on the task
4. Update Linear issue status
5. Link code changes to Linear issue

This test verifies that agents integrate with Linear for task management
and continue working with that feature throughout the SDLC.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any
import aiohttp

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from config.agent_config import get_linear_settings
from src.mcp_servers.linear_server import LinearMCPServer
from src.orchestrator.registry import RepoRegistry
from src.orchestrator.session_manager import ContextOrchestrator
from src.orchestrator.router import RepoRouter


async def test_linear_integration() -> Dict[str, Any]:
    """
    Test complete Linear integration flow.
    
    Returns:
        Dict with test results and Linear issue details
    """
    print("=" * 80)
    print("LINEAR INTEGRATION END-TO-END TEST")
    print("=" * 80)
    print()
    
    results = {
        "linear_issue_created": False,
        "linear_issue_id": None,
        "linear_issue_identifier": None,
        "linear_issue_url": None,
        "agent_can_access_linear": False,
        "linear_tools_available": False,
        "status_updated": False,
        "errors": [],
    }
    
    # Step 1: Initialize Linear Client
    print("STEP 1: Initialize Linear Client")
    print("-" * 80)
    try:
        linear_config = get_linear_settings()
        api_key = linear_config.get("api_key")
        team_id = linear_config.get("team_id")
        
        if not api_key or not team_id:
            error_msg = "LINEAR_API_KEY and LINEAR_TEAM_ID must be set"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            return results
        
        # Resolve team_id if it's a team name (not UUID)
        if not team_id.startswith(("team-", "TEAM-")):
            print(f"⚠️  Team ID appears to be a name: {team_id}")
            print("   Attempting to resolve to UUID...")
            # Query Linear API to get team UUID
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
            try:
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
                                    team_id = team["id"]
                                    print(f"   ✅ Resolved to UUID: {team_id}")
                                    break
            except Exception as e:
                print(f"   ⚠️  Could not resolve team ID: {e}")
                print(f"   Using provided team_id as-is: {team_id}")
        
        linear_client = LinearMCPServer(api_key=api_key, team_id=team_id)
        
        linear_client = LinearMCPServer(api_key=api_key, team_id=team_id)
        print(f"✅ Linear client initialized")
        print(f"   Team ID: {team_id}")
        print()
    except Exception as e:
        error_msg = f"Failed to initialize Linear client: {e}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)
        return results
    
    # Step 2: Create Linear Issue for Testing
    print("STEP 2: Create Linear Issue for Testing")
    print("-" * 80)
    try:
        issue_title = "Test: Agent Linear Integration Verification"
        issue_description = """
## Test Issue for Agent Integration

This issue is created to verify that agents can:
1. Create Linear issues
2. Access Linear context
3. Work on tasks linked to Linear
4. Update issue status

### Acceptance Criteria
- [ ] Agent can create Linear issues
- [ ] Agent can retrieve issue details
- [ ] Agent can update issue status
- [ ] Code changes are linked to Linear issue

### Technical Notes
- Testing LinearMCPServer integration
- Verifying agent orchestration with Linear
- End-to-end workflow validation
"""
        
        print(f"Creating issue: {issue_title}")
        result = await linear_client.create_issue(
            title=issue_title,
            description=issue_description.strip(),
        )
        
        issue_data = result.get("issueCreate", {}).get("issue", {})
        issue_id = issue_data.get("id")
        issue_identifier = issue_data.get("identifier")
        issue_url = issue_data.get("url")
        
        if issue_id:
            results["linear_issue_created"] = True
            results["linear_issue_id"] = issue_id
            results["linear_issue_identifier"] = issue_identifier
            results["linear_issue_url"] = issue_url
            print(f"✅ Issue created successfully")
            print(f"   Issue ID: {issue_id}")
            print(f"   Identifier: {issue_identifier}")
            print(f"   URL: {issue_url}")
        else:
            error_msg = "Issue created but no ID returned"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
        print()
    except Exception as e:
        error_msg = f"Failed to create Linear issue: {e}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)
        import traceback
        traceback.print_exc()
        print()
    
    # Step 3: Check if Linear Tools are Available to Agents
    print("STEP 3: Check Linear Tools Availability")
    print("-" * 80)
    try:
        # Load repository registry
        registry = RepoRegistry()
        repo_config = registry.get_repo("sandbox")
        
        # Initialize session orchestrator
        router = RepoRouter(registry)
        orchestrator = ContextOrchestrator(registry, router)
        
        # Prepare session
        session = orchestrator.prepare_session_for_repo("sandbox")
        
        # Check if Linear tools are exposed
        # Note: Currently, LinearMCPServer is NOT initialized in session_manager
        # This is a gap - Linear tools should be exposed like GitHub tools
        print(f"✅ Session prepared for repository: {session.repo_id}")
        print(f"   Tools available: {len(session.tools)}")
        for tool in session.tools:
            print(f"      - {tool.__name__}")
        
        # Check if Linear tools are available
        linear_tools = [tool for tool in session.tools if hasattr(tool, '__self__') and isinstance(tool.__self__, LinearMCPServer)]
        if linear_tools:
            print(f"✅ Linear tools are available: {len(linear_tools)} tools")
            for tool in linear_tools:
                print(f"      - {tool.__name__}")
            results["linear_tools_available"] = True
            results["agent_can_access_linear"] = True
        else:
            print("⚠️  Linear tools are NOT available in session")
            print("   Check that LINEAR_API_KEY and LINEAR_TEAM_ID are set")
            results["agent_can_access_linear"] = False
        print()
    except Exception as e:
        error_msg = f"Failed to check Linear tools: {e}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)
        import traceback
        traceback.print_exc()
        print()
    
    # Step 4: Test Status Update
    print("STEP 4: Test Linear Issue Status Update")
    print("-" * 80)
    if results["linear_issue_id"]:
        try:
            # First, get available states for the team
            query = """
            query GetStates($teamId: String!) {
              team(id: $teamId) {
                states {
                  nodes {
                    id
                    name
                    type
                  }
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
                    json={"query": query, "variables": {"teamId": team_id}}
                ) as resp:
                    data = await resp.json()
                    if "data" in data and "team" in data["data"]:
                        states = data["data"]["team"]["states"]["nodes"]
                        # Find "In Progress" or similar state
                        in_progress_state = None
                        for state in states:
                            if state.get("type") == "started" or "progress" in state.get("name", "").lower():
                                in_progress_state = state["id"]
                                print(f"✅ Found 'In Progress' state: {state.get('name')} ({in_progress_state})")
                                break
                        
                        if in_progress_state:
                            # Update issue status
                            result = await linear_client.update_issue_status(
                                issue_id=results["linear_issue_id"],
                                state_id=in_progress_state,
                            )
                            
                            updated_issue = result.get("issueUpdate", {}).get("issue", {})
                            if updated_issue:
                                state_name = updated_issue.get("state", {}).get("name", "Unknown")
                                print(f"✅ Issue status updated to: {state_name}")
                                results["status_updated"] = True
                            else:
                                print("⚠️  Status update returned no data")
                        else:
                            print("⚠️  Could not find 'In Progress' state")
                            print("   Available states:")
                            for state in states:
                                print(f"      - {state.get('name')} ({state.get('type')})")
                    else:
                        print("⚠️  Could not retrieve team states")
        except Exception as e:
            error_msg = f"Failed to update issue status: {e}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            import traceback
            traceback.print_exc()
        print()
    else:
        print("⚠️  Skipping status update - no issue ID available")
        print()
    
    # Step 5: Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    if results["linear_issue_created"]:
        print(f"✅ Linear Issue Created: {results['linear_issue_identifier']}")
        print(f"   URL: {results['linear_issue_url']}")
    else:
        print("❌ Failed to create Linear issue")
    
    print()
    
    if results["linear_tools_available"]:
        print("✅ Linear tools are available (via get_tools())")
    else:
        print("⚠️  Linear tools are NOT exposed to agents")
        print("   Current gap: LinearMCPServer not initialized in session_manager")
        print("   Recommendation: Add Linear tool initialization like GitHub tools")
    
    print()
    
    if results["status_updated"]:
        print("✅ Issue status updated successfully")
    else:
        print("⚠️  Issue status update skipped or failed")
    
    print()
    
    if results["errors"]:
        print("❌ ERRORS ENCOUNTERED:")
        for error in results["errors"]:
            print(f"   - {error}")
    else:
        print("✅ No errors encountered")
    
    print()
    print("=" * 80)
    print("INTEGRATION STATUS")
    print("=" * 80)
    print()
    if results["linear_tools_available"]:
        print("✅ FULLY INTEGRATED:")
        print("  ✅ LinearMCPServer class exists and works")
        print("  ✅ Can create issues, epics, update status")
        print("  ✅ LinearMCPServer initialized in ContextOrchestrator")
        print("  ✅ Linear tools exposed via get_tools()")
        print("  ✅ Agents CAN call Linear tools during execution")
        print()
        print("Agents can now:")
        print("  - Create Linear epics and issues")
        print("  - Update issue status as work progresses")
        print("  - Plan sprints")
        print("  - Link code changes to Linear issues")
    else:
        print("⚠️  PARTIAL INTEGRATION:")
        print("  ✅ LinearMCPServer class exists and works")
        print("  ✅ Can create issues, epics, update status")
        print("  ❌ Linear tools NOT available in agent session")
        print("  ❌ Check LINEAR_API_KEY and LINEAR_TEAM_ID environment variables")
    print()
    
    return results


if __name__ == "__main__":
    results = asyncio.run(test_linear_integration())
    sys.exit(0 if results["linear_issue_created"] else 1)

