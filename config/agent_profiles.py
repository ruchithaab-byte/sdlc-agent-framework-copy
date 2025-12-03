"""
Agent Profiles Configuration.

Centralized configuration for all SDLC agents. Each profile defines:
- Model settings (profile, max_turns, permission_mode)
- SDK capabilities (output_schema, tools, system_prompt, hooks)
- Resource limits (budget_usd)

This is the single source of truth for agent configurations,
following SDK best practices for consistency across all agents.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AgentProfile:
    """Immutable configuration for an SDLC agent."""
    
    # Core settings
    model_profile: str  # Maps to MODEL_REGISTRY in agent_config.py
    max_turns: int = 50  # SDK best practice: prevent infinite loops
    permission_mode: str = "default"  # default, acceptEdits, bypassPermissions
    
    # SDK Capabilities (Phase 2+)
    output_schema: Optional[str] = None  # Maps to SCHEMA_REGISTRY (Phase 2)
    system_prompt_file: Optional[str] = None  # Loads from prompts/agents/ (Phase 4)
    hooks_profile: str = "default"  # Maps to HOOKS_PROFILES (Phase 3)
    
    # Custom tools - MCP servers to include
    mcp_servers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    extra_allowed_tools: List[str] = field(default_factory=list)
    
    # Resource limits (Phase 3)
    budget_usd: Optional[float] = None


# MCP Server configurations - reusable across agents
MCP_SERVER_CONFIGS = {
    "code-ops": {
        "command": "node",
        "args_template": "{project_root}/servers/code-ops/dist/index.js",
        "env": {
            "POSTGRES_URL": os.getenv("POSTGRES_URL", ""),
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", ""),
        },
    },
    "infra-observe": {
        "command": "python",
        "args_template": "-c",
        "args_extra": "from src.mcp_servers.infra_observe_server import InfraObserveMCPServer; import asyncio; asyncio.run(InfraObserveMCPServer().run())",
        "env": {
            "VAULT_ADDR": os.getenv("VAULT_ADDR", ""),
            "VAULT_TOKEN": os.getenv("VAULT_TOKEN", ""),
            "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
            "UNLEASH_URL": os.getenv("UNLEASH_URL", ""),
            "DOCKER_REGISTRY": os.getenv("DOCKER_REGISTRY", ""),
        },
    },
    # Playwright MCP for visual feedback (Anthropic best practice)
    # Enables agents to take screenshots, validate UI layouts, and verify visual changes
    # Reference: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
    "playwright": {
        "command": "npx",
        "args": ["-y", "@anthropic/mcp-playwright"],
        "env": {
            "PLAYWRIGHT_BROWSERS_PATH": os.getenv("PLAYWRIGHT_BROWSERS_PATH", ""),
        },
    },
}


def _build_mcp_config(server_id: str, project_root: str) -> Dict[str, Any]:
    """Build MCP server config with resolved paths."""
    config = MCP_SERVER_CONFIGS.get(server_id)
    if not config:
        return {}
    
    result = {
        "command": config["command"],
        "env": config.get("env", {}),
    }
    
    # Handle different argument formats
    if "args_template" in config:
        if config["command"] == "node":
            result["args"] = [config["args_template"].format(project_root=project_root)]
        elif config["command"] == "python" and "args_extra" in config:
            result["args"] = [config["args_template"], config["args_extra"]]
    
    return result


# Agent Profiles - centralized configuration for all 10 SDLC agents
AGENT_PROFILES: Dict[str, AgentProfile] = {
    # =========================================================================
    # Strategy Agents (Planning & Analysis)
    # =========================================================================
    
    "productspec": AgentProfile(
        model_profile="strategy",
        max_turns=50,
        permission_mode="default",
        # Phase 2: Structured outputs enabled
        output_schema=None,  # ProductSpec uses free-form output for flexibility
        system_prompt_file=None,  # Will be "productspec.md" (Phase 4)
        hooks_profile="default",
        budget_usd=2.0,
    ),
    
    "archguard": AgentProfile(
        model_profile="strategy",
        max_turns=50,
        permission_mode="default",
        output_schema="architecture_review",  # Phase 2: ArchitectureReviewResult schema
        system_prompt_file=None,  # Will be "archguard.md" (Phase 4)
        hooks_profile="default",
        budget_usd=2.0,
    ),
    
    "sprintmaster": AgentProfile(
        model_profile="strategy",
        max_turns=50,
        permission_mode="default",
        output_schema="sprint_plan",  # Phase 2: SprintPlanResult schema
        system_prompt_file=None,  # Will be "sprintmaster.md" (Phase 4)
        hooks_profile="default",
        budget_usd=1.5,
    ),
    
    # =========================================================================
    # Build Agents (Code Generation & Modification)
    # =========================================================================
    
    "codecraft": AgentProfile(
        model_profile="build",
        max_turns=100,  # Higher for code generation tasks
        permission_mode="acceptEdits",  # Auto-accept code changes
        output_schema="code_craft",  # Phase 2: CodeCraftResult schema
        system_prompt_file="codecraft",  # Phase 4: Agent persona prompt
        hooks_profile="build",
        mcp_servers={
            "code-ops": MCP_SERVER_CONFIGS["code-ops"],
            # Playwright for visual feedback (Anthropic best practice)
            "playwright": MCP_SERVER_CONFIGS["playwright"],
        },
        # Include Playwright tools for UI verification
        extra_allowed_tools=[
            "mcp__playwright__screenshot",
            "mcp__playwright__navigate",
        ],
        budget_usd=5.0,
    ),
    
    "docuscribe": AgentProfile(
        model_profile="strategy",
        max_turns=50,
        permission_mode="acceptEdits",
        output_schema=None,  # DocuScribe uses free-form documentation output
        system_prompt_file=None,  # Will be "docuscribe.md" (Phase 4)
        hooks_profile="default",
        extra_allowed_tools=[
            "mcp__dev-lifecycle__publish_techdocs",
        ],
        budget_usd=2.0,
    ),
    
    # =========================================================================
    # Quality Agents (Testing & Review)
    # =========================================================================
    
    "qualityguard": AgentProfile(
        model_profile="strategy",
        max_turns=75,  # Higher for comprehensive reviews
        permission_mode="default",
        output_schema="quality_review",  # Phase 2: QualityReviewResult schema
        system_prompt_file="qualityguard",  # Phase 4: Agent persona prompt
        hooks_profile="default",
        # Enable Agent tool for subagent invocation (code-reviewer-specialist, test-generator)
        extra_allowed_tools=["Agent"],
        budget_usd=3.0,
    ),
    
    "sentinel": AgentProfile(
        model_profile="strategy",
        max_turns=75,
        permission_mode="default",
        output_schema="security_scan",  # Phase 2: SecurityScanResult schema
        system_prompt_file="sentinel",  # Phase 4: Agent persona prompt
        hooks_profile="security",  # Extra security validation hooks
        extra_allowed_tools=[
            "mcp__dev-lifecycle__create_linear_issue",
            "mcp__infra-observe__rotate_secret",
        ],
        budget_usd=3.0,
    ),
    
    # =========================================================================
    # Infrastructure Agents (DevOps & SRE)
    # =========================================================================
    
    "infraops": AgentProfile(
        model_profile="build",
        max_turns=75,
        permission_mode="default",  # Require approval for infra changes
        output_schema=None,  # InfraOps uses free-form output for flexibility
        system_prompt_file=None,  # Will be "infraops.md" (Phase 4)
        hooks_profile="build",
        mcp_servers={"infra-observe": MCP_SERVER_CONFIGS["infra-observe"]},
        extra_allowed_tools=[
            "Agent",
            "mcp__infra-observe__terraform_analyze",
            "mcp__infra-observe__docker_build_push",
            "mcp__infra-observe__rotate_secret",
            "mcp__infra-observe__toggle_feature_flag",
        ],
        budget_usd=5.0,
    ),
    
    "sre-triage": AgentProfile(
        model_profile="strategy",  # Uses strategy model per original
        max_turns=100,  # Higher for complex incident investigation
        permission_mode="default",
        output_schema="incident_triage",  # Phase 2: IncidentTriageResult schema
        system_prompt_file="sre_triage",  # Phase 4: Agent persona prompt
        hooks_profile="default",
        extra_allowed_tools=[
            "Agent",
            "mcp__infra-observe__toggle_feature_flag",
            "mcp__infra-observe__check_langfuse_score",
            "mcp__dev-lifecycle__create_linear_issue",
        ],
        budget_usd=2.0,
    ),
    
    # =========================================================================
    # Operations Agents (Cost & Analytics)
    # =========================================================================
    
    "finops": AgentProfile(
        model_profile="strategy",
        max_turns=50,
        permission_mode="default",
        output_schema="cost_analysis",  # Phase 2: CostAnalysisResult schema
        system_prompt_file=None,  # Will be "finops.md" (Phase 4)
        hooks_profile="default",
        extra_allowed_tools=[
            "mcp__infra-observe__cost_analysis",
        ],
        budget_usd=1.5,
    ),
}


def get_agent_profile(agent_id: str) -> AgentProfile:
    """
    Get agent profile by ID.
    
    Args:
        agent_id: Agent identifier (e.g., "codecraft", "qualityguard")
        
    Returns:
        AgentProfile configuration
        
    Raises:
        KeyError: If agent_id not found in AGENT_PROFILES
    """
    if agent_id not in AGENT_PROFILES:
        available = ", ".join(sorted(AGENT_PROFILES.keys()))
        raise KeyError(f"Unknown agent '{agent_id}'. Available: {available}")
    return AGENT_PROFILES[agent_id]


def list_agent_ids() -> List[str]:
    """Return list of all available agent IDs."""
    return list(AGENT_PROFILES.keys())


__all__ = [
    "AgentProfile",
    "AGENT_PROFILES",
    "MCP_SERVER_CONFIGS",
    "get_agent_profile",
    "list_agent_ids",
]

