"""Entry point for running SDLC agents or the dashboard server."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from src.agents import (
    run_archguard_agent,
    run_codecraft_agent,
    run_docuscribe_agent,
    run_finops_agent,
    run_infraops_agent,
    run_productspec_agent,
    run_qualityguard_agent,
    run_sentinel_agent,
    run_sprintmaster_agent,
    run_sre_triage_agent,
)
from src.commands.init_project import init_project, print_init_result
from src.dashboard.http_server import run_http_server
from src.dashboard.websocket_server import DashboardServer
from src.orchestrator import (
    RepoRegistry,
    RepoRouter,
    ContextOrchestrator,
    SessionError,
    RegistryLoadError,
    RoutingError,
)

AGENTS = {
    "productspec": run_productspec_agent,
    "archguard": run_archguard_agent,
    "sprintmaster": run_sprintmaster_agent,
    "codecraft": run_codecraft_agent,
    "qualityguard": run_qualityguard_agent,
    "docuscribe": run_docuscribe_agent,
    "infraops": run_infraops_agent,
    "sentinel": run_sentinel_agent,
    "sre-triage": run_sre_triage_agent,
    "finops": run_finops_agent,
}


def resolve_target_dir(target: str | None) -> Path | None:
    """
    Resolve the target directory for agent operations.
    
    Priority:
    1. Explicit --target argument
    2. Current directory if it has .sdlc/config.yaml
    3. Walk up to find Git root with .sdlc/config.yaml
    4. None (framework-local operation)
    
    Args:
        target: Explicit target path from CLI argument
        
    Returns:
        Resolved Path or None if no target found
    """
    if target:
        path = Path(target).resolve()
        if path.exists():
            return path
        raise SystemExit(f"Target directory does not exist: {path}")
    
    # Check current directory
    cwd = Path.cwd()
    if (cwd / ".sdlc" / "config.yaml").exists():
        return cwd
    
    # Walk up to find .sdlc/config.yaml
    for parent in cwd.parents:
        if (parent / ".sdlc" / "config.yaml").exists():
            return parent
        # Stop at Git root without .sdlc
        if (parent / ".git").exists():
            break
    
    return None


async def run_agent(
    name: str, 
    *, 
    task_type: str | None = None, 
    requirements: str | None = None,
    target: str | None = None,
) -> None:
    if name not in AGENTS:
        raise SystemExit(f"Unknown agent '{name}'. Available: {', '.join(AGENTS)}")
    agent_fn = AGENTS[name]
    
    # Resolve target directory
    target_dir = resolve_target_dir(target)
    if target_dir:
        print(f"🎯 Target project: {target_dir}")
    
    # Agents that take requirements text
    if name == "productspec":
        async for chunk in agent_fn(
            requirements or "Default requirements placeholder",
            target_dir=target_dir,
        ):
            print(chunk)
    # Agents that take task_type parameter
    elif name == "codecraft":
        await agent_fn(task_type or "backend", target_dir=target_dir)
    elif name == "docuscribe":
        await agent_fn(task_type or "api")
    elif name == "infraops":
        await agent_fn(task_type or "terraform")
    elif name == "sentinel":
        await agent_fn(task_type or "threat_monitor")
    elif name == "sre-triage":
        await agent_fn(task_type or "incident")
    elif name == "finops":
        await agent_fn(task_type or "analysis")
    elif name == "qualityguard":
        await agent_fn(task_type or "full")
    # Agents with target_dir support
    elif name == "archguard":
        await agent_fn(target_dir=target_dir)
    elif name == "sprintmaster":
        await agent_fn()
    # Agents with no parameters
    else:
        await agent_fn()


async def run_dashboard(host: str, port: int, api_port: int | None = None) -> None:
    """Run dashboard WebSocket server, optionally with HTTP API server."""
    if api_port is not None:
        # Start both WebSocket and HTTP servers concurrently
        ws_server = DashboardServer()
        async def run_ws():
            await ws_server.run(host=host, port=port)
        
        async def run_api():
            await run_http_server(host=host, port=api_port)
        
        await asyncio.gather(
            run_ws(),
            run_api(),
        )
    else:
        # Only WebSocket server
        server = DashboardServer()
        await server.run(host=host, port=port)


async def run_api_server(host: str, port: int) -> None:
    """Run HTTP API server only."""
    await run_http_server(host=host, port=port)


def run_orchestrate(prompt: str, *, repo_id: str | None = None, list_repos: bool = False) -> None:
    """
    Run the Context Orchestrator to prepare a session for a user prompt.
    
    This demonstrates the standard Router Pattern from Anthropic's best practices:
    1. User Input -> Router (LLM classifies)
    2. Router -> Session Manager (loads config)
    3. Session Manager -> Agent (with tools and context)
    
    Args:
        prompt: The user's task description to route.
        repo_id: Optional repository ID to bypass routing.
        list_repos: If True, list available repositories and exit.
    """
    try:
        # Initialize orchestrator components
        registry = RepoRegistry()
        
        # Handle --list-repos flag
        if list_repos:
            print("\n📦 Available Repositories:")
            print("-" * 60)
            for repo in registry.get_all_repos():
                print(f"\n  ID: {repo.id}")
                print(f"  Description: {repo.description.strip()[:80]}...")
                print(f"  GitHub: {repo.github_url}")
                print(f"  Branch: {repo.branch}")
            print()
            return
        
        # Only initialize router if we're not bypassing it
        if repo_id:
            # Bypass routing - create orchestrator without router
            router = None
            print(f"\n🔄 Preparing session for repository: {repo_id}")
            print(f"   Prompt: \"{prompt[:80]}{'...' if len(prompt) > 80 else ''}\"")
        else:
            # Initialize router for LLM-based routing
            router = RepoRouter(registry)
            print(f"\n🔄 Routing prompt to appropriate repository...")
            print(f"   Prompt: \"{prompt[:80]}{'...' if len(prompt) > 80 else ''}\"")
        
        orchestrator = ContextOrchestrator(registry, router) if router else None
        
        if repo_id:
            # Bypass routing if repo_id is specified - use direct session creation
            from src.orchestrator.session_manager import ContextOrchestrator as CO
            # Create a minimal orchestrator just for session creation
            temp_orchestrator = CO.__new__(CO)
            temp_orchestrator.registry = registry
            temp_orchestrator.router = None
            temp_orchestrator.model_profile = "vertex-strategy"
            session = temp_orchestrator.prepare_session_for_repo(repo_id)
        else:
            # Use LLM routing
            session = orchestrator.prepare_session(prompt)
        
        # Display session context
        print(f"\n✅ Session prepared successfully!")
        print("-" * 60)
        print(f"   Repository: {session.repo_id}")
        print(f"   GitHub URL: {session.repo_config.github_url}")
        print(f"   Branch: {session.repo_config.branch}")
        print(f"   Memory Path: {session.memory_path}")
        print(f"   Working Directory: {session.get_cwd()}")
        print(f"   Tools Available: {len(session.tools)}")
        
        if session.tools:
            print("\n   📧 GitHub Tools:")
            for tool in session.tools:
                print(f"      - {tool.__name__}")
        
        # Display agent configuration
        print("\n   🔧 Agent Configuration:")
        config_json = json.dumps(session.agent_config, indent=6, default=str)
        for line in config_json.split("\n"):
            print(f"      {line}")
        
        # Example usage with ClaudeAgentOptions (commented out for demo)
        print("\n" + "=" * 60)
        print("📝 Example Usage with Claude Agent SDK:")
        print("=" * 60)
        print("""
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

# Use the prepared session context
agent_options = ClaudeAgentOptions(
    cwd=session.repo_config.local_path,
    # tools parameter is not directly passed to Options in Python SDK same way
    # allowed_tools is used instead
    allowed_tools=session.agent_config.get('allowed_tools'),
)

# Initialize and run agent
async with ClaudeSDKClient(options=agent_options) as client:
    await client.query(prompt)
    async for message in client.receive_response():
        print(message)
""")
        
    except RegistryLoadError as e:
        print(f"\n❌ Registry Error: {e}")
        raise SystemExit(1)
    except RoutingError as e:
        print(f"\n❌ Routing Error: {e}")
        raise SystemExit(1)
    except SessionError as e:
        print(f"\n❌ Session Error: {e}")
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SDLC Agentic Framework CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # Init command - initialize a target repository
    init_cmd = sub.add_parser("init", help="Initialize target repository for SDLC management")
    init_cmd.add_argument(
        "--target", "-t",
        required=True,
        help="Path to target repository to initialize"
    )
    init_cmd.add_argument(
        "--type",
        choices=["microservice", "frontend", "monolith", "data-pipeline"],
        default="microservice",
        help="Project type (default: microservice)"
    )
    init_cmd.add_argument(
        "--name",
        help="Project name (auto-detected from directory if not provided)"
    )
    init_cmd.add_argument(
        "--description",
        help="Project description"
    )
    init_cmd.add_argument(
        "--no-register",
        action="store_true",
        help="Don't register project in repo_registry.yaml"
    )

    # Agent command - run a specific agent
    agent_cmd = sub.add_parser("agent", help="Run a specific agent")
    agent_cmd.add_argument("name", choices=AGENTS.keys())
    agent_cmd.add_argument(
        "--target", "-t",
        help="Target project directory (auto-detected from cwd if not provided)"
    )
    agent_cmd.add_argument("--task-type", help="Specialized task type (for CodeCraft)")
    agent_cmd.add_argument("--requirements", help="Requirement text for ProductSpec agent")

    # Dashboard command
    dash_cmd = sub.add_parser("dashboard", help="Start dashboard WebSocket server (and HTTP API server by default)")
    dash_cmd.add_argument("--host", default="0.0.0.0")
    dash_cmd.add_argument("--port", type=int, default=8765)
    dash_cmd.add_argument("--api-port", type=int, help="Start HTTP API server on this port (default: 8766, set to 0 to disable)", default=8766)
    dash_cmd.add_argument("--no-api", action="store_true", help="Don't start HTTP API server")

    # API command
    api_cmd = sub.add_parser("api", help="Start HTTP API server only")
    api_cmd.add_argument("--host", default="0.0.0.0")
    api_cmd.add_argument("--port", type=int, default=8766)

    # Orchestrate command
    orch_cmd = sub.add_parser("orchestrate", help="Route a prompt to the appropriate repository and prepare session context")
    orch_cmd.add_argument("prompt", nargs="?", default="", help="User prompt to route to a repository")
    orch_cmd.add_argument("--repo-id", help="Bypass routing and use this repository ID directly")
    orch_cmd.add_argument("--list-repos", action="store_true", help="List available repositories and exit")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    if args.command == "init":
        result = init_project(
            target_dir=args.target,
            project_type=args.type,
            name=getattr(args, "name", None),
            description=getattr(args, "description", None),
            register=not getattr(args, "no_register", False),
        )
        print_init_result(result)
        if not result.success:
            raise SystemExit(1)
    
    elif args.command == "agent":
        asyncio.run(
            run_agent(
                args.name,
                task_type=getattr(args, "task_type", None),
                requirements=getattr(args, "requirements", None),
                target=getattr(args, "target", None),
            )
        )
    elif args.command == "dashboard":
        if getattr(args, "no_api", False):
            api_port = None
        else:
            api_port = getattr(args, "api_port", 8766)
        asyncio.run(run_dashboard(args.host, args.port, api_port=api_port))
    elif args.command == "api":
        asyncio.run(run_api_server(args.host, args.port))
    elif args.command == "orchestrate":
        list_repos = getattr(args, "list_repos", False)
        prompt = getattr(args, "prompt", "")
        repo_id = getattr(args, "repo_id", None)
        
        if not list_repos and not prompt:
            raise SystemExit("Error: prompt is required unless --list-repos is specified")
        
        run_orchestrate(prompt, repo_id=repo_id, list_repos=list_repos)


if __name__ == "__main__":
    main()

