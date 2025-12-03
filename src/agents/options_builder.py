"""
Centralized Options Builder for SDLC Agents.

Provides a single function to build ClaudeAgentOptions with all SDK capabilities,
replacing duplicate _options() functions across agent files.

SDK Best Practices Applied:
- max_turns set to prevent infinite loops
- hooks for logging and lifecycle events
- setting_sources for user/project configurations
- Proper MCP server configuration
- Session resumption support
- Structured outputs with Pydantic schemas (Phase 2)
- Cost tracking with budget enforcement (Phase 3)
- System prompts with repository context (Phase 4)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

from config.agent_config import PROJECT_ROOT, resolve_model_config
from config.agent_profiles import AgentProfile, get_agent_profile
from src.hooks import build_hooks, CostTracker, set_active_tracker
from src.schemas import get_output_format
from src.utils.prompt_loader import get_system_prompt_config, build_repo_context


def _create_cost_tracker(
    profile: AgentProfile,
    model_name: str,
    session_id: Optional[str] = None,
) -> Optional[CostTracker]:
    """
    Create CostTracker if budget is defined in profile.
    
    Args:
        profile: Agent profile with optional budget_usd
        model_name: Model name for pricing lookup
        session_id: Optional session ID for tracking
        
    Returns:
        CostTracker if budget defined, None otherwise
    """
    if profile.budget_usd is None:
        return None
    
    tracker = CostTracker(
        budget_usd=profile.budget_usd,
        model=model_name,
        session_id=session_id,
    )
    
    # Register tracker for hooks to access
    if session_id:
        set_active_tracker(session_id, tracker)
    
    return tracker


def _build_mcp_servers(
    profile: AgentProfile,
    project_root: Path,
) -> Optional[Dict[str, Any]]:
    """
    Build MCP servers configuration from profile.
    
    Args:
        profile: Agent profile containing mcp_servers config
        project_root: Project root path for resolving server paths
        
    Returns:
        MCP servers dict ready for ClaudeAgentOptions, or None if empty
    """
    if not profile.mcp_servers:
        return None
    
    servers = {}
    for server_name, server_config in profile.mcp_servers.items():
        # Build resolved config
        resolved = {
            "command": server_config.get("command", "node"),
            "env": server_config.get("env", {}),
        }
        
        # Handle args with path resolution
        if "args_template" in server_config:
            template = server_config["args_template"]
            if "{project_root}" in template:
                resolved["args"] = [template.format(project_root=str(project_root))]
            elif server_config.get("command") == "python" and "args_extra" in server_config:
                resolved["args"] = [template, server_config["args_extra"]]
            else:
                resolved["args"] = [template]
        elif "args" in server_config:
            resolved["args"] = server_config["args"]
        
        servers[server_name] = resolved
    
    return servers if servers else None


def build_agent_options(
    agent_id: str,
    *,
    resume: Optional[str] = None,
    permission_mode_override: Optional[str] = None,
    extra_allowed_tools: Optional[List[str]] = None,
    cwd_override: Optional[str] = None,
    session_id: Optional[str] = None,
    repo_name: Optional[str] = None,
    repo_branch: Optional[str] = None,
    repo_context: Optional[str] = None,
) -> Tuple[ClaudeAgentOptions, Optional[CostTracker]]:
    """
    Build ClaudeAgentOptions for an agent with all SDK capabilities.
    
    This is the single source of truth for creating agent options,
    replacing duplicate _options() functions across agent files.
    
    Args:
        agent_id: Agent identifier from AGENT_PROFILES
        resume: Optional session ID to resume (SDK session management)
        permission_mode_override: Override permission mode from profile
        extra_allowed_tools: Additional tools beyond profile defaults
        cwd_override: Override working directory
        session_id: Optional session ID for cost tracking
        repo_name: Repository name for system prompt context
        repo_branch: Branch name for system prompt context
        repo_context: Pre-built repository context string
        
    Returns:
        Tuple of (ClaudeAgentOptions, CostTracker or None)
        
    Raises:
        KeyError: If agent_id not found in AGENT_PROFILES
        
    Example:
        >>> options, tracker = build_agent_options(
        ...     "codecraft",
        ...     resume="session-123",
        ...     repo_name="auth-service",
        ...     repo_branch="feature/oauth"
        ... )
        >>> async with ClaudeSDKClient(options=options) as client:
        ...     await client.query("Build the authentication module")
        >>> if tracker:
        ...     print(f"Cost: ${tracker.get_current_cost():.4f}")
    """
    # Get agent profile
    profile = get_agent_profile(agent_id)
    
    # Resolve model configuration
    model = resolve_model_config(profile.model_profile)
    
    # Build allowed tools list
    allowed_tools = list(model.allowed_tools)
    if profile.extra_allowed_tools:
        allowed_tools.extend(profile.extra_allowed_tools)
    if extra_allowed_tools:
        allowed_tools.extend(extra_allowed_tools)
    
    # Phase 3: Create cost tracker if budget defined
    cost_tracker = _create_cost_tracker(profile, model.name, session_id)
    
    # Build hooks with cost tracking support
    # SDK Best Practice: Combine documentation hooks with cost tracking hooks
    hooks = build_hooks(
        hooks_profile=profile.hooks_profile,
        cost_tracker=cost_tracker,
    )
    
    # Build MCP servers
    mcp_servers = _build_mcp_servers(profile, PROJECT_ROOT)
    
    # Determine permission mode
    permission_mode = permission_mode_override or profile.permission_mode
    
    # Determine working directory
    cwd = cwd_override or str(PROJECT_ROOT)
    
    # Phase 2: Get structured output format (if schema defined)
    # SDK Best Practice: Use output_format with JSON Schema from Pydantic
    output_format = None
    if profile.output_schema:
        output_format = get_output_format(profile.output_schema)
    
    # Phase 4: Build system prompt with repository context
    # SDK Best Practice: Use preset with append to extend Claude Code
    system_prompt = None
    if profile.system_prompt_file:
        # Build repo context if not provided
        if not repo_context and (repo_name or repo_branch):
            repo_context = build_repo_context(
                repo_name=repo_name,
                branch=repo_branch,
                working_dir=cwd,
            )
        
        system_prompt = get_system_prompt_config(
            profile.system_prompt_file.replace(".md", ""),  # Remove extension if present
            repo_context=repo_context,
            use_preset=True,  # Use claude_code preset + append
        )
    
    # Build options
    options = ClaudeAgentOptions(
        # Core settings
        cwd=cwd,
        model=model.name,
        max_turns=profile.max_turns,
        permission_mode=permission_mode,
        allowed_tools=allowed_tools,
        setting_sources=["user", "project"],
        
        # Session management
        resume=resume,
        
        # Hooks (documentation + cost tracking)
        hooks=hooks,
        
        # MCP servers (if configured)
        mcp_servers=mcp_servers,
        
        # Phase 2: Structured outputs
        output_format=output_format,
        
        # Phase 4: System prompt with agent persona
        system_prompt=system_prompt,
    )
    
    return options, cost_tracker


def build_agent_options_from_profile(
    profile: AgentProfile,
    agent_id: str,
    *,
    resume: Optional[str] = None,
    permission_mode_override: Optional[str] = None,
    extra_allowed_tools: Optional[List[str]] = None,
    cwd_override: Optional[str] = None,
    session_id: Optional[str] = None,
    repo_context: Optional[str] = None,
) -> Tuple[ClaudeAgentOptions, Optional[CostTracker]]:
    """
    Build ClaudeAgentOptions from an AgentProfile directly.
    
    Use this when you have a profile instance rather than an agent_id.
    This is useful for testing or custom profile configurations.
    
    Args:
        profile: AgentProfile configuration
        resume: Optional session ID to resume
        permission_mode_override: Override permission mode
        extra_allowed_tools: Additional tools
        cwd_override: Override working directory
        session_id: Optional session ID for cost tracking
        repo_context: Repository context for prompt
        
    Returns:
        Tuple of (ClaudeAgentOptions, CostTracker or None)
    """
    model = resolve_model_config(profile.model_profile)
    
    allowed_tools = list(model.allowed_tools)
    if profile.extra_allowed_tools:
        allowed_tools.extend(profile.extra_allowed_tools)
    if extra_allowed_tools:
        allowed_tools.extend(extra_allowed_tools)
    
    # Phase 3: Create cost tracker
    cost_tracker = _create_cost_tracker(profile, model.name, session_id)
    
    # Build hooks with cost tracking
    hooks = build_hooks(
        hooks_profile=profile.hooks_profile,
        cost_tracker=cost_tracker,
    )
    
    mcp_servers = _build_mcp_servers(profile, PROJECT_ROOT)
    permission_mode = permission_mode_override or profile.permission_mode
    cwd = cwd_override or str(PROJECT_ROOT)
    
    # Phase 2: Get structured output format
    output_format = None
    if profile.output_schema:
        output_format = get_output_format(profile.output_schema)
    
    # Phase 4: Build system prompt
    system_prompt = None
    if profile.system_prompt_file:
        system_prompt = get_system_prompt_config(
            profile.system_prompt_file.replace(".md", ""),
            repo_context=repo_context,
            use_preset=True,
        )
    
    options = ClaudeAgentOptions(
        cwd=cwd,
        model=model.name,
        max_turns=profile.max_turns,
        permission_mode=permission_mode,
        allowed_tools=allowed_tools,
        setting_sources=["user", "project"],
        resume=resume,
        hooks=hooks,
        mcp_servers=mcp_servers,
        output_format=output_format,
        system_prompt=system_prompt,
    )
    
    return options, cost_tracker


__all__ = [
    "build_agent_options",
    "build_agent_options_from_profile",
]

