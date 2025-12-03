"""
SDLC Configuration Module

Provides configuration loading for both the framework and target projects.
"""

from .project_config import (
    ProjectConfig,
    AgentOverride,
    IntegrationConfig,
    MemoryConfig,
    load_project_config,
    create_default_config,
    save_project_config,
)

__all__ = [
    "ProjectConfig",
    "AgentOverride",
    "IntegrationConfig",
    "MemoryConfig",
    "load_project_config",
    "create_default_config",
    "save_project_config",
]

