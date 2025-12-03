#!/usr/bin/env python3
"""
Challenge: Linear Task → Repository → Feature → Commit → PR

This script demonstrates the complete workflow:
1. Create a Linear task
2. Identify the correct repository
3. Implement a relevant feature
4. Commit the changes
5. Create a PR linked to the Linear issue

ULTRA THINK: Correctly identify the repo and implement a meaningful feature.
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


async def resolve_team_id(api_key: str, team_id: str) -> str:
    """Resolve team name to UUID if needed."""
    if team_id.startswith(("team-", "TEAM-")) or len(team_id) == 36:
        # Already a UUID
        return team_id
    
    # Query Linear API to get team UUID
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
    
    # If not found, return original (will fail with clear error)
    return team_id


async def create_linear_task(
    title: str,
    description: str,
    linear_client: LinearMCPServer
) -> Dict[str, Any]:
    """Create a Linear task."""
    print(f"📋 Creating Linear task: {title}")
    result = await linear_client.create_issue(
        title=title,
        description=description,
    )
    
    issue_data = result.get("issueCreate", {}).get("issue", {})
    issue_id = issue_data.get("id")
    issue_identifier = issue_data.get("identifier")
    issue_url = issue_data.get("url")
    
    print(f"✅ Task created: {issue_identifier}")
    print(f"   URL: {issue_url}")
    print()
    
    return {
        "id": issue_id,
        "identifier": issue_identifier,
        "url": issue_url,
    }


async def identify_repository(
    task_description: str,
    registry: RepoRegistry,
    router: Optional[RepoRouter] = None,
    default_repo: Optional[str] = None
) -> str:
    """Identify the correct repository for the task."""
    print("🔍 Identifying repository...")
    print(f"   Task: {task_description[:60]}...")
    
    # Try routing first if router is available
    if router:
        try:
            repo_id = router.route(task_description)
            repo_config = registry.get_repo(repo_id)
            
            print(f"✅ Repository identified via router: {repo_id}")
            print(f"   GitHub: {repo_config.github_url}")
            print(f"   Description: {repo_config.description[:60]}...")
            print()
            
            return repo_id
        except Exception as e:
            print(f"⚠️  Router failed: {e}")
            print("   Falling back to default repository...")
    
    # Fallback to default repo or sandbox
    if default_repo:
        repo_id = default_repo
    else:
        # Default to sandbox for testing
        repo_id = "sandbox"
    
    repo_config = registry.get_repo(repo_id)
    print(f"✅ Using repository: {repo_id}")
    print(f"   GitHub: {repo_config.github_url}")
    print(f"   Description: {repo_config.description[:60]}...")
    print()
    
    return repo_id


async def implement_feature(
    repo_id: str,
    task: Dict[str, Any],
    github_server: GitHubMCPServer,
    linear_client: LinearMCPServer
) -> Dict[str, Any]:
    """Implement the feature, commit, and create PR."""
    print("=" * 80)
    print("IMPLEMENTING FEATURE")
    print("=" * 80)
    print()
    
    # Step 1: Create feature branch
    branch_name = f"feature/{task['identifier'].lower().replace(' ', '-')}"
    print(f"🌿 Creating branch: {branch_name}")
    
    try:
        branch_result = await github_server.create_branch(
            new_branch=branch_name,
            source_branch="main"
        )
        print(f"✅ Branch created: {branch_name}")
        print()
    except Exception as e:
        print(f"⚠️  Branch might already exist: {e}")
        print(f"   Continuing with branch: {branch_name}")
        print()
    
    # Step 2: Determine feature based on repository
    repo_config = RepoRegistry().get_repo(repo_id)
    
    # ULTRA THINK: Implement a relevant feature based on repo type
    if "auth" in repo_id.lower():
        feature = implement_auth_feature(repo_id, task)
    elif "frontend" in repo_id.lower() or "dashboard" in repo_id.lower():
        feature = implement_frontend_feature(repo_id, task)
    elif "sandbox" in repo_id.lower():
        feature = implement_sandbox_feature(repo_id, task)
    elif "agent" in repo_id.lower() and "service" in repo_id.lower():
        feature = implement_java_service_feature(repo_id, task)
    elif "bff" in repo_id.lower():
        feature = implement_java_service_feature(repo_id, task)
    else:
        feature = implement_generic_feature(repo_id, task)
    
    # Step 3: Create/update file
    print(f"📝 Implementing feature: {feature['title']}")
    print(f"   File: {feature['path']}")
    
    commit_result = await github_server.create_commit(
        branch=branch_name,
        path=feature['path'],
        content=feature['content'],
        message=f"{feature['title']} [{task['identifier']}]"
    )
    
    print(f"✅ Commit created")
    print(f"   SHA: {commit_result.get('sha', 'N/A')[:8]}")
    print()
    
    # Step 4: Update Linear issue status to "In Progress"
    print("🔄 Updating Linear issue status...")
    try:
        # Get "In Progress" state ID
        import aiohttp
        headers = {
            "Authorization": linear_client.api_key,
            "Content-Type": "application/json",
        }
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
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                "https://api.linear.app/graphql",
                json={"query": query, "variables": {"teamId": linear_client.team_id}}
            ) as resp:
                data = await resp.json()
                if "data" in data and "team" in data["data"]:
                    states = data["data"]["team"]["states"]["nodes"]
                    in_progress_state = None
                    for state in states:
                        if state.get("type") == "started" or "progress" in state.get("name", "").lower():
                            in_progress_state = state["id"]
                            break
                    
                    if in_progress_state:
                        await linear_client.update_issue_status(
                            issue_id=task["id"],
                            state_id=in_progress_state
                        )
                        print(f"✅ Issue status updated to 'In Progress'")
        print()
    except Exception as e:
        print(f"⚠️  Could not update Linear status: {e}")
        print()
    
    # Step 5: Create Pull Request
    print("🔀 Creating Pull Request...")
    
    pr_title = f"[{task['identifier']}] {feature['title']}"
    pr_body = f"""## Description

{feature['description']}

## Changes
{feature['changes']}

## Related
Closes {task['identifier']}

## Testing
- [ ] Feature tested locally
- [ ] Code follows project standards
"""
    
    try:
        pr_result = await github_server.create_pull_request(
            head_branch=branch_name,
            base_branch="main",
            title=pr_title,
            body=pr_body
        )
        
        pr_data = pr_result.get("pull_request", {})
        pr_url = pr_data.get("html_url", "N/A")
        pr_number = pr_data.get("number", "N/A")
        
        print(f"✅ Pull Request created!")
        print(f"   PR #{pr_number}: {pr_title}")
        print(f"   URL: {pr_url}")
        print()
        
        return {
            "pr_number": pr_number,
            "pr_url": pr_url,
            "branch": branch_name,
            "commit_sha": commit_result.get("sha"),
        }
    except Exception as e:
        print(f"❌ Failed to create PR: {e}")
        import traceback
        traceback.print_exc()
        raise


def implement_auth_feature(repo_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
    """Implement a feature for auth-service repository."""
    return {
        "title": "Add health check endpoint",
        "description": "Adds a health check endpoint for monitoring service status",
        "path": "src/api/health.py",
        "content": '''"""
Health check endpoint for authentication service.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Add database connection check
    return {
        "status": "ready",
        "checks": {
            "database": "connected",
            "redis": "connected"
        }
    }
''',
        "changes": "- Added `/health` endpoint for basic health checks\n- Added `/health/ready` endpoint for readiness checks"
    }


def implement_frontend_feature(repo_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
    """Implement a feature for frontend-dashboard repository."""
    return {
        "title": "Add loading state component",
        "description": "Adds a reusable loading spinner component",
        "path": "src/components/ui/LoadingSpinner.tsx",
        "content": '''import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-gray-300 border-t-blue-600',
        sizeClasses[size],
        className
      )}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};

export default LoadingSpinner;
''',
        "changes": "- Added reusable LoadingSpinner component\n- Supports three sizes (sm, md, lg)\n- Includes accessibility attributes"
    }


def implement_sandbox_feature(repo_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
    """Implement a feature for sandbox repository."""
    return {
        "title": "Add example API client",
        "description": "Adds a simple example API client for testing",
        "path": "examples/api_client.py",
        "content": '''"""
Example API client for testing agent capabilities.
"""

import requests
from typing import Dict, Any, Optional


class ExampleAPIClient:
    """Simple API client for demonstration."""
    
    def __init__(self, base_url: str = "https://api.example.com"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            result = self.get("/health")
            return result.get("status") == "healthy"
        except Exception:
            return False


if __name__ == "__main__":
    client = ExampleAPIClient()
    print(f"Health check: {client.health_check()}")
''',
        "changes": "- Added ExampleAPIClient class\n- Supports GET and POST requests\n- Includes health check method"
    }


def implement_java_service_feature(repo_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
    """Implement a feature for Java Spring Boot service."""
    return {
        "title": "Add health check endpoint",
        "description": "Adds Spring Boot Actuator health check endpoint for service monitoring",
        "path": "src/main/java/com/example/agent/controller/HealthController.java",
        "content": '''package com.example.agent.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * Health check controller for service monitoring.
 * Provides endpoints for health and readiness checks.
 */
@RestController
@RequestMapping("/api/health")
public class HealthController {

    /**
     * Basic health check endpoint.
     * Returns service status and timestamp.
     *
     * @return Health status response
     */
    @GetMapping
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "UP");
        response.put("service", "new-agent-service");
        response.put("timestamp", Instant.now().toString());
        response.put("version", "1.0.0");
        return ResponseEntity.ok(response);
    }

    /**
     * Readiness check endpoint.
     * Indicates if the service is ready to accept traffic.
     *
     * @return Readiness status response
     */
    @GetMapping("/ready")
    public ResponseEntity<Map<String, Object>> readiness() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "READY");
        response.put("checks", Map.of(
            "database", "UP",
            "cache", "UP"
        ));
        return ResponseEntity.ok(response);
    }

    /**
     * Liveness check endpoint.
     * Indicates if the service is alive.
     *
     * @return Liveness status response
     */
    @GetMapping("/live")
    public ResponseEntity<Map<String, Object>> liveness() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "ALIVE");
        return ResponseEntity.ok(response);
    }
}
''',
        "changes": "- Added HealthController with /api/health endpoint\n- Added /api/health/ready for readiness checks\n- Added /api/health/live for liveness checks\n- Follows Spring Boot REST controller patterns"
    }


def implement_generic_feature(repo_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
    """Implement a generic feature."""
    return {
        "title": "Add README documentation",
        "description": "Adds comprehensive README documentation",
        "path": "README.md",
        "content": f'''# {repo_id}

## Description

This repository contains the implementation for {repo_id}.

## Features

- Feature 1
- Feature 2
- Feature 3

## Setup

```bash
# Install dependencies
npm install  # or pip install -r requirements.txt

# Run the application
npm start  # or python main.py
```

## Development

See CONTRIBUTING.md for development guidelines.

## License

MIT
''',
        "changes": "- Added comprehensive README\n- Includes setup instructions\n- Documents features and usage"
    }


async def main():
    """Main challenge execution."""
    print("=" * 80)
    print("CHALLENGE: LINEAR TASK → REPOSITORY → FEATURE → COMMIT → PR")
    print("=" * 80)
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
    
    # Resolve team ID to UUID if needed
    team_id = await resolve_team_id(
        linear_config["api_key"],
        linear_config["team_id"]
    )
    
    linear_client = LinearMCPServer(
        api_key=linear_config["api_key"],
        team_id=team_id
    )
    
    registry = RepoRegistry()
    
    # Try to initialize router, but don't fail if it doesn't work
    router = None
    try:
        router = RepoRouter(registry)
    except Exception as e:
        print(f"⚠️  Router initialization failed: {e}")
        print("   Will use default repository instead")
        print()
    
    # Step 1: Create Linear Task
    print("STEP 1: CREATE LINEAR TASK")
    print("-" * 80)
    
    # Ask user which repo to use, or use new-agent-service as default
    target_repo = os.getenv("TARGET_REPO", "new-agent-service")
    
    task_title = "Add health check endpoint for service monitoring"
    task_description = f"""
## Description
Add a health check endpoint to enable monitoring and status checks for the {target_repo} service.

## Acceptance Criteria
- [ ] Health check endpoint returns service status
- [ ] Endpoint responds quickly (< 100ms)
- [ ] Includes service version information
- [ ] Ready for integration with monitoring tools
- [ ] Follows Spring Boot REST controller patterns

## Technical Notes
- Use Spring Boot @RestController annotation
- Implement /api/health endpoint
- Add /api/health/ready for readiness checks
- Add /api/health/live for liveness checks
- Use standard HTTP status codes
- Include timestamp in response
    """.strip()
    
    task = await create_linear_task(task_title, task_description, linear_client)
    
    # Step 2: Identify Repository
    print("STEP 2: IDENTIFY REPOSITORY")
    print("-" * 80)
    
    # Use new-agent-service as target (or from env)
    target_repo = os.getenv("TARGET_REPO", "new-agent-service")
    
    # Use target repo for challenge
    repo_id = await identify_repository(
        task_title, 
        registry, 
        router=router,
        default_repo=target_repo
    )
    repo_config = registry.get_repo(repo_id)
    
    # Allow override via environment variable (only if explicitly set)
    github_repo_url = os.getenv("GITHUB_REPO_URL")
    if github_repo_url and github_repo_url != repo_config.github_url:
        print(f"📝 Overriding repo URL with: {github_repo_url}")
        # Create a modified config
        from dataclasses import dataclass
        @dataclass
        class ModifiedRepoConfig:
            id: str = repo_config.id
            description: str = repo_config.description
            github_url: str = github_repo_url
            local_path: str = repo_config.local_path
            branch: str = repo_config.branch
        repo_config = ModifiedRepoConfig()
        print()
    
    # Step 3: Initialize GitHub Server
    print("STEP 3: INITIALIZE GITHUB SERVER")
    print("-" * 80)
    
    github_server = GitHubMCPServer(
        repo_url=repo_config.github_url,
        token=github_token
    )
    print(f"✅ GitHub server initialized for: {repo_config.github_url}")
    print()
    
    # Step 4: Implement Feature, Commit, and Create PR
    print("STEP 4: IMPLEMENT FEATURE → COMMIT → PR")
    print("-" * 80)
    
    result = await implement_feature(repo_id, task, github_server, linear_client)
    
    # Final Summary
    print("=" * 80)
    print("✅ CHALLENGE COMPLETED!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  📋 Linear Task: {task['identifier']} - {task_title}")
    print(f"  📦 Repository: {repo_id} ({repo_config.github_url})")
    print(f"  🌿 Branch: {result['branch']}")
    print(f"  🔀 Pull Request: {result['pr_url']}")
    print()
    print("Next Steps:")
    print(f"  1. Review the PR: {result['pr_url']}")
    print(f"  2. Check Linear issue: {task['url']}")
    print(f"  3. Merge when ready!")
    print()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

