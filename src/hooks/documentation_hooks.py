"""
Hook implementations for documenting agent activity.

Each hook logs to the central ExecutionLogger and prints concise console output so
that long-running agent sessions can be monitored in real-time.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from src.logging.execution_logger import ExecutionLogger
from src.utils.artifact_detection import detect_artifacts_from_output
from src.utils.user_utils import get_user_email_from_env

# Lazy logger initialization - gets user_email and project_path when first used
# This ensures the environment variables set by agents are captured
_logger_instance: Optional[ExecutionLogger] = None
_current_project_path: Optional[str] = None


def set_project_path(project_path: str) -> None:
    """
    Set the current project path for logging.
    
    Call this before running an agent to ensure executions are logged
    with the correct repository context.
    
    Args:
        project_path: Path to the target project directory
    """
    global _current_project_path, _logger_instance
    _current_project_path = project_path
    # Reset logger to pick up new project path
    _logger_instance = None


def _get_logger() -> ExecutionLogger:
    """Get or create ExecutionLogger instance with current user_email and project_path."""
    global _logger_instance, _current_project_path
    
    # Get current user_email from environment (may be set after module import)
    # Always check environment to get latest value
    user_email = os.getenv("AGENT_USER_EMAIL") or get_user_email_from_env()
    
    # If still no email, try to get from GitHub
    if not user_email:
        try:
            from src.utils.github_user_utils import get_github_email
            user_email = get_github_email()
        except Exception:
            pass
    
    # Get project path from environment or global setting
    project_path = os.getenv("SDLC_TARGET_PROJECT") or _current_project_path
    
    # Always reinitialize logger to ensure we have latest user_email
    # This prevents using stale cached values
    if _logger_instance is None or \
       _logger_instance.user_email != user_email or \
       _logger_instance.project_path != project_path:
        _logger_instance = ExecutionLogger(
            user_email=user_email,
            project_path=project_path,
        )
    
    return _logger_instance

_execution_timings: Dict[str, float] = {}


async def pre_tool_use_logger(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """Log all tool uses before execution."""
    logger = _get_logger()  # Get logger with current user_email
    session_id = input_data.get("session_id", "unknown")
    tool_name = input_data.get("tool_name", "unknown")
    _execution_timings[tool_use_id or ""] = time.time()
    
    # Extract agent_name from environment variable set by runner
    agent_name = os.getenv("CURRENT_AGENT_ID")

    logger.log_execution(
        session_id=session_id,
        hook_event="PreToolUse",
        tool_name=tool_name,
        agent_name=agent_name,
        input_data=input_data.get("tool_input"),
        metadata={
            "tool_use_id": tool_use_id,
            "permission_mode": input_data.get("permission_mode"),
            "cwd": input_data.get("cwd"),
        },
    )
    print(f"🔧 [PreToolUse] {tool_name} - Session: {session_id}")
    return {}


async def post_tool_use_logger(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """Log tool execution results and detect artifacts."""
    logger = _get_logger()  # Get logger with current user_email
    session_id = input_data.get("session_id", "unknown")
    tool_name = input_data.get("tool_name", "unknown")
    tool_response = input_data.get("tool_response", {})

    start = _execution_timings.pop(tool_use_id or "", None)
    duration_ms = int((time.time() - start) * 1000) if start else None
    success = tool_response.get("success", True)
    
    # Extract agent_name from environment variable set by runner
    agent_name = os.getenv("CURRENT_AGENT_ID")

    # Log execution and get execution ID for artifact linking
    exec_id = logger.log_execution(
        session_id=session_id,
        hook_event="PostToolUse",
        tool_name=tool_name,
        agent_name=agent_name,
        status="success" if success else "error",
        duration_ms=duration_ms,
        input_data=input_data.get("tool_input"),
        output_data=tool_response,
        error_message=tool_response.get("error"),
        metadata={"tool_use_id": tool_use_id},
    )
    logger.update_tool_usage(
        session_id=session_id,
        tool_name=tool_name,
        success=success,
        duration_ms=duration_ms or 0,
    )

    # Detect and log artifacts from tool output
    if exec_id and success:
        try:
            artifacts = detect_artifacts_from_output(
                tool_name=tool_name,
                output_data=tool_response,
                input_data=input_data.get("tool_input"),
            )
            for artifact in artifacts:
                logger.log_artifact(
                    execution_log_id=exec_id,
                    artifact_type=artifact["artifact_type"],
                    artifact_url=artifact.get("artifact_url"),
                    identifier=artifact.get("identifier"),
                    metadata=artifact.get("metadata"),
                )
                print(f"📦 [Artifact] {artifact['artifact_type']}: {artifact.get('identifier', 'N/A')}")
        except Exception as e:
            # Don't fail the hook if artifact detection fails
            print(f"⚠️  [Artifact Detection] Error: {e}")

    status_emoji = "✅" if success else "❌"
    print(f"{status_emoji} [PostToolUse] {tool_name} - {duration_ms or 0}ms - Session: {session_id}")
    return {}


async def session_start_logger(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Log session start metadata.
    
    Note: As of SDK 0.1.10, SessionStart hooks are not supported in the Python SDK.
    This function is kept for future compatibility or reference.
    """
    logger = _get_logger()  # Get logger with current user_email
    session_id = input_data.get("session_id", "unknown")
    logger.log_execution(
        session_id=session_id,
        hook_event="SessionStart",
        metadata={
            "source": input_data.get("source"),
            "transcript_path": input_data.get("transcript_path"),
            "permission_mode": input_data.get("permission_mode"),
        },
    )
    print(f"🚀 [SessionStart] {session_id}")
    return {}


async def session_end_logger(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Log summary at session end.
    
    Note: As of SDK 0.1.10, SessionEnd hooks are not supported in the Python SDK.
    This function is kept for future compatibility or reference.
    """
    logger = _get_logger()  # Get logger with current user_email
    session_id = input_data.get("session_id", "unknown")
    summary = logger.get_session_summary(session_id)
    logger.log_execution(
        session_id=session_id,
        hook_event="SessionEnd",
        metadata={
            "reason": input_data.get("reason"),
            "summary": summary,
        },
    )
    print(f"🏁 [SessionEnd] {session_id} -> {summary}")
    return {}


async def stop_logger(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """Log when an agent stops."""
    logger = _get_logger()  # Get logger with current user_email
    session_id = input_data.get("session_id", "unknown")
    logger.log_execution(
        session_id=session_id,
        hook_event="Stop",
        metadata={"stop_hook_active": input_data.get("stop_hook_active", False)},
    )
    print(f"⏸️  [Stop] Session: {session_id}")
    return {}


# =============================================================================
# Additional Supported Hooks (Python SDK)
# =============================================================================


async def user_prompt_submit_logger(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Log and optionally modify user prompts before submission.
    
    Use cases for SDLC agents:
    - Add timestamps for audit trails
    - Inject repository context
    - Validate prompt format
    - Track prompt patterns
    
    Returns:
        Empty dict to pass through, or dict with 'hookSpecificOutput' to modify prompt
    """
    logger = _get_logger()
    session_id = input_data.get("session_id", "unknown")
    prompt = input_data.get("prompt", "")
    
    # Log the prompt submission
    logger.log_execution(
        session_id=session_id,
        hook_event="UserPromptSubmit",
        input_data={"prompt_length": len(prompt), "prompt_preview": prompt[:200]},
        metadata={
            "source": input_data.get("source", "user"),
        },
    )
    
    # Add timestamp to prompt for audit trail
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat()
    
    print(f"📝 [UserPromptSubmit] {len(prompt)} chars - Session: {session_id}")
    
    # Optionally modify the prompt (uncomment to enable)
    # return {
    #     'hookSpecificOutput': {
    #         'hookEventName': 'UserPromptSubmit',
    #         'updatedPrompt': f"[{timestamp}] {prompt}"
    #     }
    # }
    
    return {}


async def subagent_stop_logger(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Log when a subagent completes execution.
    
    Use cases for SDLC agents:
    - Track InfraOps and SRE-Triage subagent completions
    - Aggregate results from delegated tasks
    - Monitor subagent costs and duration
    - Detect subagent failures
    """
    logger = _get_logger()
    
    # Handle None input_data
    if input_data is None:
        input_data = {}
    
    session_id = input_data.get("session_id", "unknown")
    
    # Try multiple ways to extract subagent_type
    subagent_type = input_data.get("subagent_type")
    if not subagent_type:
        # Try from agent field
        subagent_type = input_data.get("agent")
    if not subagent_type:
        # Try from context if available
        if context and hasattr(context, 'get'):
            subagent_type = context.get("subagent_type") or context.get("agent")
    if not subagent_type:
        # Try from result.agent_name if available
        result = input_data.get("result", {})
        if isinstance(result, dict):
            subagent_type = result.get("agent_name") or result.get("agent")
    if not subagent_type:
        # Final fallback
        subagent_type = "unknown"
    
    result = input_data.get("result", {})
    if not isinstance(result, dict):
        result = {}
    
    # Extract subagent metrics if available
    duration_ms = result.get("duration_ms")
    cost_usd = result.get("total_cost_usd")
    success = not result.get("is_error", False)
    
    logger.log_execution(
        session_id=session_id,
        hook_event="SubagentStop",
        tool_name=f"subagent:{subagent_type}",
        status="success" if success else "error",
        duration_ms=duration_ms,
        metadata={
            "subagent_type": subagent_type,
            "cost_usd": cost_usd,
            "has_result": bool(result.get("result")),
        },
    )
    
    status_emoji = "✅" if success else "❌"
    cost_str = f" ${cost_usd:.4f}" if cost_usd else ""
    duration_str = f" {duration_ms}ms" if duration_ms else ""
    print(f"{status_emoji} [SubagentStop] {subagent_type}{duration_str}{cost_str} - Session: {session_id}")
    
    return {}


async def pre_compact_logger(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Log before message compaction occurs.
    
    Use cases for SDLC agents:
    - Preserve important context before compaction
    - Track when context limits are hit
    - Log conversation state for debugging long sessions
    - Extract and save key decisions/artifacts before they're compacted
    
    Note: This hook is called when the conversation is about to be
    summarized/compacted to fit within context limits.
    """
    logger = _get_logger()
    session_id = input_data.get("session_id", "unknown")
    
    # Extract compaction metadata
    message_count = input_data.get("message_count", 0)
    token_count = input_data.get("token_count", 0)
    
    logger.log_execution(
        session_id=session_id,
        hook_event="PreCompact",
        metadata={
            "message_count": message_count,
            "token_count": token_count,
            "reason": "context_limit_reached",
        },
    )
    
    print(f"📦 [PreCompact] {message_count} messages, ~{token_count} tokens - Session: {session_id}")
    
    # Could return a system message to preserve important context
    # return {
    #     'systemMessage': "Important: Preserve key architecture decisions made in this session."
    # }
    
    return {}


__all__ = [
    # Project path management
    "set_project_path",
    # Core hooks (always used)
    "pre_tool_use_logger",
    "post_tool_use_logger",
    "stop_logger",
    # Additional supported hooks
    "user_prompt_submit_logger",
    "subagent_stop_logger",
    "pre_compact_logger",
    # Unsupported in Python SDK (kept for reference)
    "session_start_logger",
    "session_end_logger",
]

