"""Repository Registry for multi-repository orchestration.

Loads repository configurations from YAML and provides lookup methods
for the Router and Session Manager components.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError

from config.agent_config import PROJECT_ROOT


class RepoConfig(BaseModel):
    """Pydantic model for repository configuration."""
    
    id: str = Field(..., description="Unique identifier for the repository")
    description: str = Field(..., description="Description of the repository's purpose")
    github_url: str = Field(..., description="GitHub URL for the repository")
    local_path: str = Field(default="./repos", description="Local filesystem path to the repository")
    branch: str = Field(default="main", description="Default branch to use")

    # Phase 5: Code execution capabilities
    enable_code_execution: bool = Field(
        default=False,
        description="Enable sandboxed code execution for batch operations (Phase 5)"
    )

    class Config:
        frozen = True


class RepoNotFoundError(Exception):
    """Raised when a repository ID is not found in the registry."""
    pass


class RegistryLoadError(Exception):
    """Raised when the registry YAML file cannot be loaded or parsed."""
    pass


class RepoRegistry:
    """
    Repository Registry that loads and provides access to repository configurations.
    
    Loads repository definitions from a YAML configuration file and provides
    methods to query repositories by ID or get all registered repositories.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
    ) -> None:
        """
        Initialize the RepoRegistry.
        
        Args:
            config_path: Path to the YAML configuration file.
                        Defaults to config/repo_registry.yaml relative to PROJECT_ROOT.
        """
        if config_path is None:
            self.config_path = PROJECT_ROOT / "config" / "repo_registry.yaml"
        else:
            self.config_path = Path(config_path)
        
        self._repos: dict[str, RepoConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load and parse the YAML configuration file."""
        if not self.config_path.exists():
            raise RegistryLoadError(
                f"Registry configuration file not found: {self.config_path}"
            )
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RegistryLoadError(f"Failed to parse YAML configuration: {e}")
        
        if not data or "repositories" not in data:
            raise RegistryLoadError(
                "Invalid registry configuration: 'repositories' key not found"
            )
        
        repositories = data["repositories"]
        if not isinstance(repositories, list):
            raise RegistryLoadError(
                "Invalid registry configuration: 'repositories' must be a list"
            )
        
        for repo_data in repositories:
            try:
                repo = RepoConfig(**repo_data)
                self._repos[repo.id] = repo
            except ValidationError as e:
                raise RegistryLoadError(
                    f"Invalid repository configuration: {e}"
                )

    def get_repo(self, repo_id: str) -> RepoConfig:
        """
        Get repository configuration by ID.
        
        Args:
            repo_id: The unique identifier for the repository.
            
        Returns:
            RepoConfig: The repository configuration.
            
        Raises:
            RepoNotFoundError: If no repository with the given ID exists.
        """
        if repo_id not in self._repos:
            available = ", ".join(self._repos.keys()) if self._repos else "none"
            raise RepoNotFoundError(
                f"Repository '{repo_id}' not found. Available repositories: {available}"
            )
        return self._repos[repo_id]

    def get_all_repos(self) -> List[RepoConfig]:
        """
        Get all registered repositories.
        
        Returns:
            List[RepoConfig]: List of all repository configurations.
        """
        return list(self._repos.values())

    def get_repo_ids(self) -> List[str]:
        """
        Get list of all registered repository IDs.
        
        Returns:
            List[str]: List of repository IDs.
        """
        return list(self._repos.keys())

    def __len__(self) -> int:
        """Return the number of registered repositories."""
        return len(self._repos)

    def __contains__(self, repo_id: str) -> bool:
        """Check if a repository ID exists in the registry."""
        return repo_id in self._repos


__all__ = [
    "RepoConfig",
    "RepoRegistry",
    "RepoNotFoundError",
    "RegistryLoadError",
]

