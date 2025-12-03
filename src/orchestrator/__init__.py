"""Orchestrator module for multi-repository context management.

This module provides the Context Orchestrator layer that routes user prompts
to appropriate repositories and sets up agent sessions with repository-specific
context and tools.

Components:
- RepoRegistry: Loads and manages repository configurations
- RepoRouter: Routes prompts to repositories using LLM classification
- ContextOrchestrator: Coordinates session preparation
- SessionContext: Pydantic model for session configuration
"""

from src.orchestrator.registry import (
    RepoConfig,
    RepoRegistry,
    RepoNotFoundError,
    RegistryLoadError,
)
from src.orchestrator.router import (
    RepoRouter,
    RoutingError,
)
from src.orchestrator.session_manager import (
    SessionContext,
    SessionError,
    ContextOrchestrator,
)


__all__ = [
    # Registry
    "RepoConfig",
    "RepoRegistry",
    "RepoNotFoundError",
    "RegistryLoadError",
    # Router
    "RepoRouter",
    "RoutingError",
    # Session Manager
    "SessionContext",
    "SessionError",
    "ContextOrchestrator",
]

