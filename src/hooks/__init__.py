"""
Hooks package for SDLC Agents.

Provides hook implementations for all supported Python SDK hooks:
- PreToolUse, PostToolUse, UserPromptSubmit, Stop, SubagentStop, PreCompact

Modules:
- documentation_hooks: Logging and artifact detection
- cost_tracker: CostTracker class for usage tracking
- cost_hooks: Budget enforcement hooks

Usage:
    from src.hooks import build_hooks, CostTracker
    
    # Build all hooks for an agent
    tracker = CostTracker(budget_usd=5.0)
    hooks = build_hooks(
        hooks_profile="default",
        cost_tracker=tracker,
    )
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from claude_agent_sdk import HookMatcher

from . import documentation_hooks
from .documentation_hooks import set_project_path
from .cost_tracker import (
    BudgetExceededError,
    ContextBudgetError,
    ContextHealth,
    CostSummary,
    CostTracker,
    StepUsage,
)
from .cost_hooks import (
    budget_check_stop_hook,
    budget_warning_pre_tool_hook,
    clear_active_tracker,
    cost_tracking_post_tool_hook,
    create_cost_hooks,
    get_active_tracker,
    set_active_tracker,
)
from .verification_hooks import (
    create_verification_hooks,
    configure_verification,
    verification_post_tool_hook,
    test_runner_post_tool_hook,
    VerificationResult,
    LINTER_CONFIG,
)


# Hook profiles define which documentation hooks to include
HOOKS_PROFILES = {
    "default": {
        "pre_tool_use": True,
        "post_tool_use": True,
        "user_prompt_submit": True,
        "stop": True,
        "subagent_stop": True,
        "pre_compact": True,
        # Verification (disabled by default for strategy agents)
        "run_linters": False,
        "run_tests": False,
    },
    "build": {
        # Build agents (CodeCraft, InfraOps) - all hooks for full observability
        "pre_tool_use": True,
        "post_tool_use": True,
        "user_prompt_submit": True,
        "stop": True,
        "subagent_stop": True,
        "pre_compact": True,
        # Verification enabled for build agents (Anthropic best practice)
        "run_linters": True,
        "run_tests": False,  # Tests are expensive, enable explicitly
    },
    "security": {
        # Security agents (Sentinel) - all hooks with extra validation potential
        "pre_tool_use": True,
        "post_tool_use": True,
        "user_prompt_submit": True,
        "stop": True,
        "subagent_stop": True,
        "pre_compact": True,
        # Linters help catch security issues
        "run_linters": True,
        "run_tests": False,
    },
    "minimal": {
        # Minimal hooks for lightweight operations
        "pre_tool_use": False,
        "post_tool_use": True,  # Always track results
        "user_prompt_submit": False,
        "stop": True,  # Always track stops
        "subagent_stop": False,
        "pre_compact": False,
        "run_linters": False,
        "run_tests": False,
    },
}


def build_hooks(
    hooks_profile: str = "default",
    cost_tracker: Optional[CostTracker] = None,
) -> Dict[str, List[HookMatcher]]:
    """
    Build complete hooks configuration for an agent.
    
    Combines documentation hooks with cost tracking hooks based on profile.
    
    Args:
        hooks_profile: Profile name from HOOKS_PROFILES
        cost_tracker: Optional CostTracker for budget enforcement
        
    Returns:
        Dict mapping hook events to HookMatcher lists
        
    Example:
        >>> tracker = CostTracker(budget_usd=5.0, session_id="sess-123")
        >>> hooks = build_hooks("default", cost_tracker=tracker)
        >>> options = ClaudeAgentOptions(hooks=hooks)
    """
    profile = HOOKS_PROFILES.get(hooks_profile, HOOKS_PROFILES["default"])
    hooks: Dict[str, List[HookMatcher]] = {}
    
    # =========================================================================
    # PreToolUse hooks
    # =========================================================================
    pre_tool_hooks = []
    if profile.get("pre_tool_use"):
        pre_tool_hooks.append(documentation_hooks.pre_tool_use_logger)
    if cost_tracker:
        pre_tool_hooks.append(budget_warning_pre_tool_hook)
    
    if pre_tool_hooks:
        hooks["PreToolUse"] = [HookMatcher(hooks=pre_tool_hooks)]
    
    # =========================================================================
    # PostToolUse hooks
    # =========================================================================
    post_tool_hooks = []
    if profile.get("post_tool_use"):
        post_tool_hooks.append(documentation_hooks.post_tool_use_logger)
    if cost_tracker:
        post_tool_hooks.append(cost_tracking_post_tool_hook)
    
    # Add verification hooks (Anthropic best practice: rules-based feedback)
    if profile.get("run_linters"):
        configure_verification(
            run_linters=True,
            run_tests=profile.get("run_tests", False),
            verbose=True,
        )
        post_tool_hooks.append(verification_post_tool_hook)
    if profile.get("run_tests"):
        post_tool_hooks.append(test_runner_post_tool_hook)
    
    if post_tool_hooks:
        hooks["PostToolUse"] = [HookMatcher(hooks=post_tool_hooks)]
    
    # =========================================================================
    # UserPromptSubmit hooks
    # =========================================================================
    if profile.get("user_prompt_submit"):
        hooks["UserPromptSubmit"] = [
            HookMatcher(hooks=[documentation_hooks.user_prompt_submit_logger])
        ]
    
    # =========================================================================
    # Stop hooks
    # =========================================================================
    stop_hooks = []
    if profile.get("stop"):
        stop_hooks.append(documentation_hooks.stop_logger)
    if cost_tracker:
        stop_hooks.append(budget_check_stop_hook)
    
    if stop_hooks:
        hooks["Stop"] = [HookMatcher(hooks=stop_hooks)]
    
    # =========================================================================
    # SubagentStop hooks
    # =========================================================================
    if profile.get("subagent_stop"):
        hooks["SubagentStop"] = [
            HookMatcher(hooks=[documentation_hooks.subagent_stop_logger])
        ]
    
    # =========================================================================
    # PreCompact hooks
    # =========================================================================
    if profile.get("pre_compact"):
        hooks["PreCompact"] = [
            HookMatcher(hooks=[documentation_hooks.pre_compact_logger])
        ]
    
    return hooks


__all__ = [
    # Modules
    "documentation_hooks",
    
    # Project path management
    "set_project_path",
    
    # Main builder
    "build_hooks",
    "HOOKS_PROFILES",
    
    # Cost tracking
    "CostTracker",
    "CostSummary",
    "StepUsage",
    "BudgetExceededError",
    "ContextBudgetError",
    "ContextHealth",
    
    # Cost hooks
    "create_cost_hooks",
    "set_active_tracker",
    "get_active_tracker",
    "clear_active_tracker",
    
    # Verification hooks (Anthropic best practice)
    "create_verification_hooks",
    "configure_verification",
    "verification_post_tool_hook",
    "test_runner_post_tool_hook",
    "VerificationResult",
    "LINTER_CONFIG",
]
