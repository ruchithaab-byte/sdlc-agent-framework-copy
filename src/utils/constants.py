"""Constants used throughout the SDLC agent framework.

This module centralizes magic strings to improve maintainability and reduce errors.
"""

from pathlib import Path
from typing import Optional


# =============================================================================
# Memory Paths (Standard Pattern)
# =============================================================================
# All memory files are stored in the target project's .sdlc/memories/ directory.
# This keeps memories version-controlled with the project.
#
# Standard location: {target_project}/.sdlc/memories/{memory_type}.xml
#
# Examples:
#   /path/to/my-project/.sdlc/memories/prd.xml
#   /path/to/my-project/.sdlc/memories/architecture_plan.xml
#   /path/to/my-project/.sdlc/memories/qa_summary.xml

# Relative paths for use in prompts (relative to target project root)
MEMORY_PRD_PATH = ".sdlc/memories/prd.xml"
"""Relative path to PRD memory file. Always relative to target project root."""

MEMORY_ARCHITECTURE_PLAN_PATH = ".sdlc/memories/architecture_plan.xml"
"""Relative path to architecture plan memory file. Always relative to target project root."""

MEMORY_QA_SUMMARY_PATH = ".sdlc/memories/qa_summary.xml"
"""Relative path to QA summary memory file. Always relative to target project root."""

MEMORY_SPRINT_PLAN_PATH = ".sdlc/memories/sprint_plan.xml"
"""Relative path to sprint plan memory file. Always relative to target project root."""


# =============================================================================
# Memory Path Functions (Target-relative)
# =============================================================================
# New approach: Functions that return paths relative to target project's .sdlc/

def get_memory_path(target_dir: Optional[Path], memory_type: str) -> str:
    """
    Get the path to a memory file for a target project.
    
    Memory files are stored in the target project's .sdlc/memories/ directory,
    making them part of the project's version control.
    
    Args:
        target_dir: Path to target project directory (None for framework-relative)
        memory_type: Type of memory (prd, architecture_plan, qa_summary, sprint_plan, etc.)
        
    Returns:
        Path string to the memory file
        
    Example:
        >>> get_memory_path(Path("/projects/my-app"), "prd")
        '/projects/my-app/.sdlc/memories/prd.xml'
        
        >>> get_memory_path(None, "prd")
        'memories/prd.xml'
    """
    # Map memory types to filenames
    memory_files = {
        "prd": "prd.xml",
        "architecture_plan": "architecture_plan.xml",
        "qa_summary": "qa_summary.xml",
        "sprint_plan": "sprint_plan.xml",
        "code_review": "code_review.xml",
    }
    
    filename = memory_files.get(memory_type, f"{memory_type}.xml")
    
    if target_dir:
        return str(target_dir / ".sdlc" / "memories" / filename)
    else:
        # Fallback to framework-relative path
        return f"memories/{filename}"


def get_memory_dir(target_dir: Optional[Path]) -> Path:
    """
    Get the memories directory for a target project.
    
    Args:
        target_dir: Path to target project directory (None for framework-relative)
        
    Returns:
        Path to the memories directory
    """
    if target_dir:
        return target_dir / ".sdlc" / "memories"
    else:
        # Import here to avoid circular dependency
        from config.agent_config import PROJECT_ROOT
        return PROJECT_ROOT / "memories"


def ensure_memory_dir(target_dir: Optional[Path]) -> Path:
    """
    Ensure the memories directory exists for a target project.
    
    Args:
        target_dir: Path to target project directory
        
    Returns:
        Path to the (now existing) memories directory
    """
    memory_dir = get_memory_dir(target_dir)
    memory_dir.mkdir(parents=True, exist_ok=True)
    return memory_dir

# =============================================================================
# Tool Names
# =============================================================================
# Standard tool names used by Claude Agent SDK
# These should match the tool names expected by the SDK

TOOL_SKILL = "Skill"
"""Agent Skills tool - enables reusable skill execution."""

TOOL_READ = "Read"
"""Read tool - reads files from the filesystem."""

TOOL_WRITE = "Write"
"""Write tool - writes files to the filesystem."""

TOOL_BASH = "Bash"
"""Bash tool - executes shell commands."""

TOOL_MEMORY = "memory"
"""Memory tool - persistent storage across agent sessions."""

TOOL_CODE_EXECUTION = "code_execution"
"""Code execution tool - executes code in isolated environments."""

# =============================================================================
# Tool Lists
# =============================================================================
# Common tool combinations used by different agent types

STRATEGY_TOOLS = [TOOL_SKILL, TOOL_READ, TOOL_WRITE, TOOL_BASH, TOOL_MEMORY]
"""Standard tools for strategy/planning agents (no code execution)."""

BUILD_TOOLS = [
    TOOL_SKILL,
    TOOL_READ,
    TOOL_WRITE,
    TOOL_BASH,
    TOOL_MEMORY,
    TOOL_CODE_EXECUTION,
]
"""Standard tools for build/development agents (includes code execution)."""

__all__ = [
    # Memory paths (relative to target project)
    "MEMORY_PRD_PATH",
    "MEMORY_ARCHITECTURE_PLAN_PATH",
    "MEMORY_QA_SUMMARY_PATH",
    "MEMORY_SPRINT_PLAN_PATH",
    # Memory path functions (absolute paths)
    "get_memory_path",
    "get_memory_dir",
    "ensure_memory_dir",
    # Tool names
    "TOOL_SKILL",
    "TOOL_READ",
    "TOOL_WRITE",
    "TOOL_BASH",
    "TOOL_MEMORY",
    "TOOL_CODE_EXECUTION",
    # Tool lists
    "STRATEGY_TOOLS",
    "BUILD_TOOLS",
]

