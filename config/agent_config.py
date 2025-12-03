"""
Configuration helpers for the SDLC agent framework.

Loads environment variables (with support for .env files), exposes strongly-typed
model settings, and centralizes beta feature flag management so that agents can
reuse the same configuration surface.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Resolve project root and load a .env file if it exists (non-fatal when missing).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class ModelConfig:
    """Immutable configuration for a Claude model."""

    name: str
    allowed_tools: List[str]
    beta_flags: List[str] = field(default_factory=list)


DEFAULT_BETA_FLAGS: Dict[str, List[str]] = {
    "core": ["context-management-2025-06-27", "skills-2025-10-02"],
    "code_execution": ["code-execution-2025-08-25"],
}

MODEL_REGISTRY: Dict[str, ModelConfig] = {
    "strategy": ModelConfig(
        name="claude-opus-4-5@20251101",
        allowed_tools=["Skill", "Read", "Write", "Bash", "memory"],
        beta_flags=DEFAULT_BETA_FLAGS["core"],
    ),
    "build": ModelConfig(
        name="claude-opus-4-5@20251101",
        allowed_tools=[
            "Skill",
            "Read",
            "Write",
            "Bash",
            "memory",
            "code_execution",
            "Agent",
            "mcp__code-ops__flyway_validate",
            "mcp__code-ops__scaffold_shadcn_component",
            "mcp__code-ops__code_execution_review",
            "mcp__code-ops__code_execution_verify_change",
        ],
        beta_flags=DEFAULT_BETA_FLAGS["core"],
    ),
    "infra": ModelConfig(
        name="claude-sonnet-4-20250514",
        allowed_tools=[
            "Skill",
            "Read",
            "Write",
            "Bash",
            "memory",
            "Agent",
            "mcp__infra-observe__code_execution_terraform_analyze",
            "mcp__infra-observe__docker_build_push",
            "mcp__infra-observe__rotate_secret",
            "mcp__infra-observe__toggle_feature_flag",
            "mcp__infra-observe__check_langfuse_score",
            "mcp__infra-observe__code_execution_cost_analysis",
        ],
        beta_flags=DEFAULT_BETA_FLAGS["core"],
    ),
    # Vertex AI / Gemini models
    "vertex-strategy": ModelConfig(
        name="gemini-1.5-pro-001",
        allowed_tools=["Skill", "Read", "Write", "Bash", "memory"],
        beta_flags=[],
    ),
    "vertex-build": ModelConfig(
        name="gemini-1.5-pro-001",
        allowed_tools=[
            "Skill",
            "Read",
            "Write",
            "Bash",
            "memory",
            "code_execution",
            "mcp__code-ops__flyway_validate",
            "mcp__code-ops__scaffold_shadcn_component",
            "mcp__code-ops__code_execution_review",
            "mcp__code-ops__code_execution_verify_change",
        ],
        beta_flags=[],
    ),
}


def get_env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Fetch an environment variable with optional default/required semantics.
    """
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Define it in your shell or .env file."
        )
    return value


def get_api_keys() -> Dict[str, Optional[str]]:
    """Return the third-party API keys used throughout the framework."""
    return {
        "anthropic": get_env("ANTHROPIC_API_KEY"),
        "linear": get_env("LINEAR_API_KEY"),
        "mintlify": get_env("MINTLIFY_API_KEY"),
    }


def get_llm_provider() -> str:
    """
    Determine which LLM provider to use.
    
    Returns:
        "anthropic" if ANTHROPIC_API_KEY is set
        "vertex" if Google Cloud credentials are available
        Defaults to "anthropic"
    """
    anthropic_key = get_env("ANTHROPIC_API_KEY")
    if anthropic_key:
        return "anthropic"
    
    if get_google_cloud_credentials_path():
        return "vertex"
    
    return "anthropic"  # Default


def get_service_endpoints() -> Dict[str, Optional[str]]:
    """Return service endpoint configuration (Backstage, etc.)."""
    return {
        "backstage_url": get_env("BACKSTAGE_URL"),
    }


def get_linear_settings() -> Dict[str, Optional[str]]:
    """Return Linear-specific configuration."""
    return {
        "team_id": get_env("LINEAR_TEAM_ID"),
        "api_key": get_env("LINEAR_API_KEY"),
    }


def get_user_email() -> Optional[str]:
    """
    Get user email from config file or environment variable.
    
    Checks in order:
    1. CLAUDE_AGENT_USER_EMAIL environment variable
    2. .claude/user_config.json file
    3. Returns None if not found
    """
    # Check environment variable first
    email = get_env("CLAUDE_AGENT_USER_EMAIL")
    if email:
        return email
    
    # Check config file
    config_file = PROJECT_ROOT / ".claude" / "user_config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
                return config.get("user")
        except Exception:
            pass
    
    return None


def get_google_cloud_credentials_path() -> Optional[Path]:
    """
    Return the path to Google Cloud service account JSON file.
    
    Checks GOOGLE_APPLICATION_CREDENTIALS env var first, then falls back to
    default location: config/credentials/google-service-account.json
    """
    env_path = get_env("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path:
        return Path(env_path)
    
    default_path = PROJECT_ROOT / "config" / "credentials" / "google-service-account.json"
    if default_path.exists():
        return default_path
    
    return None


def resolve_model_config(profile: str, *, include_code_execution: bool = False) -> ModelConfig:
    """
    Lookup a model configuration by profile name.

    Args:
        profile: One of the keys defined in MODEL_REGISTRY (e.g., \"strategy\", \"build\").
        include_code_execution: When True, append code execution beta flags.
    """
    if profile not in MODEL_REGISTRY:
        raise KeyError(
            f"Unknown model profile '{profile}'. Available profiles: {', '.join(MODEL_REGISTRY)}"
        )

    model = MODEL_REGISTRY[profile]
    beta_flags = list(model.beta_flags)
    if include_code_execution and "code_execution" in DEFAULT_BETA_FLAGS:
        beta_flags.extend(DEFAULT_BETA_FLAGS["code_execution"])

    return ModelConfig(
        name=model.name,
        allowed_tools=list(model.allowed_tools),
        beta_flags=beta_flags,
    )


__all__ = [
    "PROJECT_ROOT",
    "ModelConfig",
    "get_env",
    "get_api_keys",
    "get_service_endpoints",
    "get_linear_settings",
    "get_user_email",
    "get_google_cloud_credentials_path",
    "resolve_model_config",
]

