"""
System Prompt Loader for SDLC Agents.

Loads agent system prompts from markdown files and applies templating
for repository-specific context.

SDK Best Practices Applied (per python-sdk.md):
- system_prompt can be a string or SystemPromptPreset
- Use preset with append to extend Claude Code's capabilities
- Inject repository context dynamically

Usage:
    from src.utils.prompt_loader import load_system_prompt, get_system_prompt_config
    
    # Load raw prompt
    prompt = load_system_prompt("codecraft", repo_context="Working in auth-service repo")
    
    # Get SDK-ready config (preset + append)
    config = get_system_prompt_config("codecraft", repo_context="...")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from config.agent_config import PROJECT_ROOT


# Prompt templates directory
PROMPTS_DIR = PROJECT_ROOT / "prompts" / "agents"


def load_system_prompt(
    agent_id: str,
    *,
    repo_context: Optional[str] = None,
    extra_context: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Load system prompt for an agent from markdown file.
    
    Args:
        agent_id: Agent identifier (e.g., "codecraft", "qualityguard")
        repo_context: Repository-specific context to inject
        extra_context: Additional template variables
        
    Returns:
        Formatted system prompt string, or None if file not found
        
    Example:
        >>> prompt = load_system_prompt(
        ...     "codecraft",
        ...     repo_context="Repository: auth-service\\nBranch: feature/login"
        ... )
    """
    # Try multiple file extensions
    for ext in [".md", ".txt", ""]:
        prompt_file = PROMPTS_DIR / f"{agent_id}{ext}"
        if prompt_file.exists():
            break
    else:
        # No prompt file found
        return None
    
    # Read prompt template
    try:
        prompt_content = prompt_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"⚠️  Failed to read prompt file {prompt_file}: {e}")
        return None
    
    # Build template context
    context = {
        "repo_context": repo_context or "",
        "agent_id": agent_id,
        **(extra_context or {}),
    }
    
    # Apply simple template substitution
    # Uses {variable} format, similar to Python's str.format()
    try:
        formatted = prompt_content.format(**context)
    except KeyError as e:
        # Missing template variable - return with placeholder intact
        print(f"⚠️  Missing template variable in {agent_id} prompt: {e}")
        formatted = prompt_content
    
    return formatted.strip()


def get_system_prompt_config(
    agent_id: str,
    *,
    repo_context: Optional[str] = None,
    extra_context: Optional[Dict[str, str]] = None,
    use_preset: bool = True,
) -> Optional[Union[str, Dict[str, Any]]]:
    """
    Get system prompt configuration for ClaudeAgentOptions.
    
    SDK Best Practice: Use preset with append to extend Claude Code's
    built-in capabilities with agent-specific instructions.
    
    Args:
        agent_id: Agent identifier
        repo_context: Repository context to inject
        extra_context: Additional template variables
        use_preset: If True, return SystemPromptPreset with append
                   If False, return raw string prompt
        
    Returns:
        System prompt config for ClaudeAgentOptions.system_prompt:
        - Dict with type/preset/append for preset mode
        - String for custom prompt mode
        - None if no prompt file found
        
    Example:
        >>> config = get_system_prompt_config("codecraft", use_preset=True)
        >>> # Returns: {"type": "preset", "preset": "claude_code", "append": "..."}
        
        >>> options = ClaudeAgentOptions(system_prompt=config)
    """
    prompt = load_system_prompt(
        agent_id,
        repo_context=repo_context,
        extra_context=extra_context,
    )
    
    if not prompt:
        return None
    
    if use_preset:
        # SDK: Use Claude Code preset and append agent-specific instructions
        return {
            "type": "preset",
            "preset": "claude_code",
            "append": prompt,
        }
    else:
        # Return raw prompt string
        return prompt


def build_repo_context(
    repo_name: Optional[str] = None,
    branch: Optional[str] = None,
    working_dir: Optional[str] = None,
    additional_info: Optional[Dict[str, str]] = None,
) -> str:
    """
    Build repository context string for prompt injection.
    
    Args:
        repo_name: Repository name
        branch: Current branch
        working_dir: Working directory path
        additional_info: Additional context key-value pairs
        
    Returns:
        Formatted repository context string
        
    Example:
        >>> context = build_repo_context(
        ...     repo_name="auth-service",
        ...     branch="feature/oauth",
        ...     additional_info={"sprint": "Sprint 23"}
        ... )
    """
    lines = ["## Repository Context"]
    
    if repo_name:
        lines.append(f"- **Repository**: {repo_name}")
    if branch:
        lines.append(f"- **Branch**: {branch}")
    if working_dir:
        lines.append(f"- **Working Directory**: {working_dir}")
    
    if additional_info:
        for key, value in additional_info.items():
            lines.append(f"- **{key}**: {value}")
    
    if len(lines) == 1:
        return ""  # No context provided
    
    return "\n".join(lines)


def list_available_prompts() -> list[str]:
    """
    List all available agent prompt files.
    
    Returns:
        List of agent IDs with available prompts
    """
    if not PROMPTS_DIR.exists():
        return []
    
    prompts = []
    for f in PROMPTS_DIR.iterdir():
        if f.is_file() and f.suffix in [".md", ".txt", ""]:
            prompts.append(f.stem)
    
    return sorted(prompts)


__all__ = [
    "load_system_prompt",
    "get_system_prompt_config",
    "build_repo_context",
    "list_available_prompts",
    "PROMPTS_DIR",
]

