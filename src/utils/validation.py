"""
Profile Validation for SDLC Agents.

Validates agent profiles at startup to catch configuration errors early.
This prevents runtime failures due to missing prompts, schemas, or invalid settings.

Usage:
    from src.utils.validation import validate_all_profiles, validate_profile
    
    # Validate single profile
    errors = validate_profile("codecraft")
    
    # Validate all profiles at startup
    validate_all_profiles(raise_on_error=True)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from config.agent_config import PROJECT_ROOT, MODEL_REGISTRY
from config.agent_profiles import AGENT_PROFILES, get_agent_profile
from src.schemas import SCHEMA_REGISTRY
from src.utils.prompt_loader import PROMPTS_DIR, list_available_prompts
from src.hooks import HOOKS_PROFILES


class ProfileValidationError(Exception):
    """Raised when profile validation fails."""
    
    def __init__(self, errors: Dict[str, List[str]]):
        self.errors = errors
        msg = "\n".join(
            f"  {agent}: {', '.join(errs)}"
            for agent, errs in errors.items()
        )
        super().__init__(f"Profile validation failed:\n{msg}")


def validate_profile(agent_id: str) -> List[str]:
    """
    Validate a single agent profile.
    
    Checks:
    - Model profile exists in MODEL_REGISTRY
    - Output schema exists in SCHEMA_REGISTRY (if defined)
    - System prompt file exists (if defined)
    - Hooks profile exists in HOOKS_PROFILES
    - Budget is non-negative (if defined)
    - max_turns is positive
    
    Args:
        agent_id: Agent identifier to validate
        
    Returns:
        List of error messages, empty if valid
    """
    errors = []
    
    try:
        profile = get_agent_profile(agent_id)
    except KeyError as e:
        return [str(e)]
    
    # Validate model profile
    if profile.model_profile not in MODEL_REGISTRY:
        available = ", ".join(MODEL_REGISTRY.keys())
        errors.append(
            f"Unknown model_profile '{profile.model_profile}'. "
            f"Available: {available}"
        )
    
    # Validate output schema
    if profile.output_schema and profile.output_schema not in SCHEMA_REGISTRY:
        available = ", ".join(SCHEMA_REGISTRY.keys())
        errors.append(
            f"Unknown output_schema '{profile.output_schema}'. "
            f"Available: {available}"
        )
    
    # Validate system prompt file
    if profile.system_prompt_file:
        prompt_file = PROMPTS_DIR / f"{profile.system_prompt_file}.md"
        if not prompt_file.exists():
            # Try without extension
            prompt_file_alt = PROMPTS_DIR / profile.system_prompt_file
            if not prompt_file_alt.exists():
                available = list_available_prompts()
                errors.append(
                    f"System prompt file not found: {profile.system_prompt_file}. "
                    f"Available: {', '.join(available) or 'none'}"
                )
    
    # Validate hooks profile
    if profile.hooks_profile not in HOOKS_PROFILES:
        available = ", ".join(HOOKS_PROFILES.keys())
        errors.append(
            f"Unknown hooks_profile '{profile.hooks_profile}'. "
            f"Available: {available}"
        )
    
    # Validate numeric constraints
    if profile.max_turns <= 0:
        errors.append(f"max_turns must be positive, got {profile.max_turns}")
    
    if profile.budget_usd is not None and profile.budget_usd < 0:
        errors.append(f"budget_usd must be non-negative, got {profile.budget_usd}")
    
    # Validate permission mode
    valid_modes = {"default", "acceptEdits", "plan", "bypassPermissions"}
    if profile.permission_mode not in valid_modes:
        errors.append(
            f"Invalid permission_mode '{profile.permission_mode}'. "
            f"Must be one of: {', '.join(valid_modes)}"
        )
    
    return errors


def validate_all_profiles(
    *,
    raise_on_error: bool = False,
    log_results: bool = True,
) -> Dict[str, List[str]]:
    """
    Validate all agent profiles.
    
    Args:
        raise_on_error: If True, raise ProfileValidationError on any errors
        log_results: If True, print validation results
        
    Returns:
        Dict mapping agent_id to list of errors (empty list if valid)
        
    Raises:
        ProfileValidationError: If raise_on_error=True and any errors found
    """
    all_errors: Dict[str, List[str]] = {}
    valid_count = 0
    
    for agent_id in AGENT_PROFILES:
        errors = validate_profile(agent_id)
        if errors:
            all_errors[agent_id] = errors
        else:
            valid_count += 1
    
    if log_results:
        total = len(AGENT_PROFILES)
        if all_errors:
            print(f"⚠️  Profile validation: {valid_count}/{total} valid")
            for agent_id, errors in all_errors.items():
                for error in errors:
                    print(f"  ❌ {agent_id}: {error}")
        else:
            print(f"✅ Profile validation: {total}/{total} profiles valid")
    
    if raise_on_error and all_errors:
        raise ProfileValidationError(all_errors)
    
    return all_errors


def get_profile_summary() -> str:
    """
    Get a summary of all agent profiles.
    
    Returns:
        Formatted string with profile overview
    """
    lines = ["SDLC Agent Profiles Summary", "=" * 40]
    
    for agent_id, profile in sorted(AGENT_PROFILES.items()):
        features = []
        if profile.output_schema:
            features.append(f"schema:{profile.output_schema}")
        if profile.system_prompt_file:
            features.append(f"prompt:{profile.system_prompt_file}")
        if profile.budget_usd:
            features.append(f"budget:${profile.budget_usd}")
        if profile.mcp_servers:
            features.append(f"mcp:{','.join(profile.mcp_servers.keys())}")
        
        feature_str = " | ".join(features) if features else "basic"
        lines.append(f"  {agent_id}: {profile.model_profile} [{feature_str}]")
    
    return "\n".join(lines)


__all__ = [
    "validate_profile",
    "validate_all_profiles",
    "get_profile_summary",
    "ProfileValidationError",
]

