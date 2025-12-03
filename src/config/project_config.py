"""
Project Configuration Loader

Loads and validates .sdlc/config.yaml from target repositories.
Provides project context to SDLC agents for contextual operation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class IntegrationConfig:
    """Configuration for external integrations."""
    linear: Dict[str, Any] = field(default_factory=lambda: {"enabled": False})
    github: Dict[str, Any] = field(default_factory=lambda: {"enabled": True})


@dataclass
class MemoryConfig:
    """Configuration for agent memories."""
    path: str = "memories/"
    auto_save: bool = True


@dataclass
class AgentOverride:
    """Per-agent configuration overrides."""
    budget_usd: Optional[float] = None
    task_type: Optional[str] = None
    coverage_target: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentOverride":
        """Create AgentOverride from dictionary."""
        known_fields = {"budget_usd", "task_type", "coverage_target"}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        return cls(
            budget_usd=data.get("budget_usd"),
            task_type=data.get("task_type"),
            coverage_target=data.get("coverage_target"),
            extra=extra
        )


@dataclass
class ProjectConfig:
    """
    Project configuration loaded from .sdlc/config.yaml.
    
    This provides context for SDLC agents operating on a target repository.
    """
    # Core project info
    name: str
    project_type: str  # microservice | frontend | monolith | data-pipeline
    description: str
    
    # Technology stack
    tech_stack: Dict[str, List[str]] = field(default_factory=dict)
    
    # Skills to auto-load
    skills: List[str] = field(default_factory=list)
    
    # Agent-specific overrides
    agent_overrides: Dict[str, AgentOverride] = field(default_factory=dict)
    
    # Integration settings
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)
    
    # Memory configuration
    memories: MemoryConfig = field(default_factory=MemoryConfig)
    
    # Custom prompts directory
    prompts_dir: Optional[str] = None
    
    # Environment settings
    environments: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Source path (where config was loaded from)
    source_path: Optional[Path] = None
    
    def get_agent_override(self, agent_name: str) -> Optional[AgentOverride]:
        """Get override settings for a specific agent."""
        return self.agent_overrides.get(agent_name)
    
    def get_tech_stack_flat(self) -> List[str]:
        """Get flattened list of all technologies."""
        result = []
        for techs in self.tech_stack.values():
            result.extend(techs)
        return result
    
    def get_memory_path(self, target_dir: Path) -> Path:
        """Get the full path to memories directory."""
        return target_dir / ".sdlc" / self.memories.path
    
    def to_context_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary suitable for prompt template injection.
        
        Returns a flattened dictionary with project context that can be
        used in Jinja2 templates.
        """
        return {
            "project": {
                "name": self.name,
                "type": self.project_type,
                "description": self.description,
                "tech_stack": self.tech_stack,
                "skills": self.skills,
            },
            "tech_stack": self.tech_stack,
            "skills": self.skills,
            "environments": self.environments,
        }


def load_project_config(target_dir: Path) -> Optional[ProjectConfig]:
    """
    Load .sdlc/config.yaml from target directory.
    
    Args:
        target_dir: Path to the target repository root
        
    Returns:
        ProjectConfig if config exists and is valid, None otherwise
    """
    config_path = target_dir / ".sdlc" / "config.yaml"
    
    if not config_path.exists():
        # Try alternate location
        alt_path = target_dir / ".sdlc" / "config.yml"
        if alt_path.exists():
            config_path = alt_path
        else:
            return None
    
    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        
        if not data:
            return None
            
        return _parse_config(data, config_path)
        
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error loading config from {config_path}: {e}")


def _parse_config(data: Dict[str, Any], source_path: Path) -> ProjectConfig:
    """Parse raw YAML data into ProjectConfig."""
    project_data = data.get("project", {})
    
    # Parse agent overrides
    agent_overrides = {}
    for agent_name, override_data in data.get("agents", {}).items():
        if override_data:
            agent_overrides[agent_name] = AgentOverride.from_dict(override_data)
    
    # Parse integrations
    integrations_data = data.get("integrations", {})
    integrations = IntegrationConfig(
        linear=integrations_data.get("linear", {"enabled": False}),
        github=integrations_data.get("github", {"enabled": True})
    )
    
    # Parse memory config
    memories_data = data.get("memories", {})
    memories = MemoryConfig(
        path=memories_data.get("path", "memories/"),
        auto_save=memories_data.get("auto_save", True)
    )
    
    return ProjectConfig(
        name=project_data.get("name", "Unnamed Project"),
        project_type=project_data.get("type", "microservice"),
        description=project_data.get("description", ""),
        tech_stack=data.get("tech_stack", {}),
        skills=data.get("skills", []),
        agent_overrides=agent_overrides,
        integrations=integrations,
        memories=memories,
        prompts_dir=data.get("prompts_dir"),
        environments=data.get("environments", {}),
        source_path=source_path
    )


def create_default_config(
    project_name: str,
    project_type: str = "microservice",
    description: str = ""
) -> ProjectConfig:
    """
    Create a default ProjectConfig for initialization.
    
    Args:
        project_name: Name of the project
        project_type: Type of project (microservice, frontend, monolith, data-pipeline)
        description: Project description
        
    Returns:
        ProjectConfig with sensible defaults
    """
    # Default tech stacks by project type
    default_tech_stacks = {
        "microservice": {
            "backend": ["python", "fastapi"],
            "infrastructure": ["docker", "kubernetes"]
        },
        "frontend": {
            "frontend": ["react", "typescript", "tailwind"],
            "infrastructure": ["vercel"]
        },
        "monolith": {
            "backend": ["python", "django"],
            "frontend": ["htmx", "tailwind"],
            "infrastructure": ["docker"]
        },
        "data-pipeline": {
            "backend": ["python", "apache-airflow"],
            "data": ["postgresql", "apache-spark"],
            "infrastructure": ["docker", "kubernetes"]
        }
    }
    
    return ProjectConfig(
        name=project_name,
        project_type=project_type,
        description=description,
        tech_stack=default_tech_stacks.get(project_type, {}),
        skills=[],
        agent_overrides={},
        integrations=IntegrationConfig(),
        memories=MemoryConfig()
    )


def save_project_config(config: ProjectConfig, target_dir: Path) -> Path:
    """
    Save ProjectConfig to .sdlc/config.yaml.
    
    Args:
        config: ProjectConfig to save
        target_dir: Target repository root
        
    Returns:
        Path to saved config file
    """
    sdlc_dir = target_dir / ".sdlc"
    sdlc_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = sdlc_dir / "config.yaml"
    
    # Build YAML structure
    data = {
        "project": {
            "name": config.name,
            "type": config.project_type,
            "description": config.description
        },
        "tech_stack": config.tech_stack,
        "skills": config.skills,
        "agents": {
            name: {
                k: v for k, v in {
                    "budget_usd": override.budget_usd,
                    "task_type": override.task_type,
                    "coverage_target": override.coverage_target,
                    **override.extra
                }.items() if v is not None
            }
            for name, override in config.agent_overrides.items()
        },
        "integrations": {
            "linear": config.integrations.linear,
            "github": config.integrations.github
        },
        "memories": {
            "path": config.memories.path,
            "auto_save": config.memories.auto_save
        },
        "environments": config.environments
    }
    
    if config.prompts_dir:
        data["prompts_dir"] = config.prompts_dir
    
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    return config_path

