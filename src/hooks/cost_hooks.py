"""
Cost Tracking Hooks for SDLC Agents.

Provides hooks that integrate with CostTracker to:
- Track token usage per step
- Enforce budget limits
- Log cost events for dashboards

These hooks work alongside documentation_hooks to provide
comprehensive observability.

Usage:
    from src.hooks.cost_hooks import create_cost_hooks
    from src.hooks.cost_tracker import CostTracker
    
    tracker = CostTracker(budget_usd=5.0)
    hooks = create_cost_hooks(tracker)
    
    # Add to ClaudeAgentOptions.hooks
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.hooks.cost_tracker import BudgetExceededError, CostTracker


# Global tracker reference for hooks (set per-session)
_active_trackers: Dict[str, CostTracker] = {}


def set_active_tracker(session_id: str, tracker: CostTracker) -> None:
    """Register a tracker for a session."""
    _active_trackers[session_id] = tracker


def get_active_tracker(session_id: str) -> Optional[CostTracker]:
    """Get the active tracker for a session."""
    return _active_trackers.get(session_id)


def clear_active_tracker(session_id: str) -> None:
    """Clear tracker when session ends."""
    _active_trackers.pop(session_id, None)


async def cost_tracking_post_tool_hook(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Track costs after tool use completes.
    
    This hook captures token usage from assistant messages and
    updates the CostTracker. Works in conjunction with the
    message-level tracking in runner.py.
    
    Note: Primary cost tracking happens in runner.py via process_message().
    This hook provides real-time logging and budget check after each tool.
    """
    session_id = input_data.get("session_id", "unknown")
    tracker = get_active_tracker(session_id)
    
    if not tracker:
        return {}
    
    # Log current cost status
    summary = tracker.get_summary()
    cost_str = f"${summary.actual_cost_usd or summary.estimated_cost_usd:.4f}"
    
    if summary.budget_usd:
        remaining = summary.budget_remaining_usd or 0
        percent_used = ((summary.budget_usd - remaining) / summary.budget_usd) * 100
        print(f"💰 [Cost] {cost_str} ({percent_used:.1f}% of ${summary.budget_usd:.2f} budget)")
        
        # Check budget after tool use
        if tracker.is_budget_exceeded():
            print(f"🚨 [Budget] EXCEEDED - Session: {session_id}")
            # Return block decision to stop agent
            return {
                'decision': 'block',
                'systemMessage': f"Budget exceeded: {cost_str} of ${summary.budget_usd:.2f}. Stopping agent."
            }
    else:
        print(f"💰 [Cost] {cost_str} - Session: {session_id}")
    
    return {}


async def budget_check_stop_hook(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Final budget check when agent stops.
    
    Logs final cost summary and clears the tracker.
    """
    session_id = input_data.get("session_id", "unknown")
    tracker = get_active_tracker(session_id)
    
    if tracker:
        summary = tracker.get_summary()
        cost = summary.actual_cost_usd or summary.estimated_cost_usd
        
        print(f"💵 [Final Cost] ${cost:.4f} | "
              f"{summary.total_input_tokens} input + {summary.total_output_tokens} output tokens | "
              f"{summary.step_count} steps - Session: {session_id}")
        
        if summary.budget_exceeded:
            print(f"⚠️  [Budget] Exceeded: ${cost:.4f} of ${summary.budget_usd:.2f}")
        elif summary.budget_usd:
            print(f"✅ [Budget] Within limit: ${cost:.4f} of ${summary.budget_usd:.2f}")
        
        # Clear tracker when session ends
        clear_active_tracker(session_id)
    
    return {}


async def budget_warning_pre_tool_hook(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Check budget before tool use and warn if approaching limit.
    
    Injects a system message if budget is 80%+ used.
    """
    session_id = input_data.get("session_id", "unknown")
    tracker = get_active_tracker(session_id)
    
    if not tracker or not tracker.budget_usd:
        return {}
    
    summary = tracker.get_summary()
    remaining = summary.budget_remaining_usd or 0
    percent_used = ((tracker.budget_usd - remaining) / tracker.budget_usd) * 100
    
    # Warn at 80% usage
    if percent_used >= 80 and percent_used < 100:
        print(f"⚠️  [Budget Warning] {percent_used:.1f}% used - Session: {session_id}")
        return {
            'systemMessage': (
                f"Budget alert: {percent_used:.1f}% of ${tracker.budget_usd:.2f} used. "
                "Please wrap up the current task efficiently."
            )
        }
    
    # Block at 100%
    if percent_used >= 100:
        return {
            'decision': 'block',
            'systemMessage': f"Budget exceeded. Stopping agent."
        }
    
    return {}


def create_cost_hooks(tracker: CostTracker) -> Dict[str, list]:
    """
    Create hooks dict for cost tracking.
    
    Note: These hooks are designed to complement documentation_hooks,
    not replace them. Use build_hooks() in hooks/__init__.py to
    combine all hooks properly.
    
    Args:
        tracker: CostTracker instance for this session
        
    Returns:
        Dict of hooks to merge with other hooks
    """
    # Register tracker for hooks to access
    if tracker.session_id:
        set_active_tracker(tracker.session_id, tracker)
    
    from claude_agent_sdk import HookMatcher
    
    return {
        "PreToolUse": [HookMatcher(hooks=[budget_warning_pre_tool_hook])],
        "PostToolUse": [HookMatcher(hooks=[cost_tracking_post_tool_hook])],
        "Stop": [HookMatcher(hooks=[budget_check_stop_hook])],
    }


__all__ = [
    "create_cost_hooks",
    "set_active_tracker",
    "get_active_tracker",
    "clear_active_tracker",
    "cost_tracking_post_tool_hook",
    "budget_check_stop_hook",
    "budget_warning_pre_tool_hook",
]

