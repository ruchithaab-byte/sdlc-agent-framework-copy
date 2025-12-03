"""
Project Initialization Command

Initialize a target repository for SDLC agent management.
Creates the .sdlc/ directory structure and configuration files.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml

from config.agent_config import PROJECT_ROOT
from src.config.project_config import (
    ProjectConfig,
    create_default_config,
    save_project_config,
)


@dataclass
class InitResult:
    """Result of project initialization."""
    success: bool
    target_dir: Path
    files_created: List[str]
    config_path: Optional[Path] = None
    error: Optional[str] = None
    registered_in_registry: bool = False


def detect_project_info(target_dir: Path) -> dict:
    """
    Detect project information from the target directory.
    
    Attempts to detect:
    - Project name from directory name or package.json/pyproject.toml
    - Git remote URL
    - Existing tech stack hints
    
    Args:
        target_dir: Path to target repository
        
    Returns:
        Dictionary with detected project info
    """
    info = {
        "name": target_dir.name,
        "description": "",
        "github_url": "",
        "tech_stack": {},
    }
    
    # Try to get project name from package.json
    package_json = target_dir / "package.json"
    if package_json.exists():
        try:
            import json
            with open(package_json) as f:
                data = json.load(f)
                info["name"] = data.get("name", info["name"])
                info["description"] = data.get("description", "")
                
                # Detect tech stack from dependencies
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                frontend_techs = []
                if "next" in deps:
                    frontend_techs.append("nextjs")
                if "react" in deps:
                    frontend_techs.append("react")
                if "typescript" in deps or (target_dir / "tsconfig.json").exists():
                    frontend_techs.append("typescript")
                if "tailwindcss" in deps:
                    frontend_techs.append("tailwind")
                if frontend_techs:
                    info["tech_stack"]["frontend"] = frontend_techs
        except Exception:
            pass
    
    # Try to get project name from pyproject.toml
    pyproject = target_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
                project_data = data.get("project", {})
                info["name"] = project_data.get("name", info["name"])
                info["description"] = project_data.get("description", "")
                
                # Detect tech stack
                backend_techs = ["python"]
                deps = project_data.get("dependencies", [])
                if isinstance(deps, list):
                    deps_str = " ".join(deps)
                    if "fastapi" in deps_str:
                        backend_techs.append("fastapi")
                    if "django" in deps_str:
                        backend_techs.append("django")
                    if "flask" in deps_str:
                        backend_techs.append("flask")
                info["tech_stack"]["backend"] = backend_techs
        except Exception:
            pass
    
    # Try to get Git remote URL
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            info["github_url"] = result.stdout.strip()
    except Exception:
        pass
    
    # Try to get current branch
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip() or "main"
    except Exception:
        info["branch"] = "main"
    
    return info


def copy_template_files(
    target_dir: Path,
    project_type: str,
) -> List[str]:
    """
    Copy template files to the target project.
    
    Args:
        target_dir: Path to target repository
        project_type: Type of project (microservice, frontend, monolith)
        
    Returns:
        List of files created
    """
    files_created = []
    templates_dir = PROJECT_ROOT / "examples" / "templates" / project_type
    
    # Create .sdlc directories
    sdlc_dir = target_dir / ".sdlc"
    memories_dir = sdlc_dir / "memories"
    prompts_dir = sdlc_dir / "prompts"
    
    for dir_path in [sdlc_dir, memories_dir, prompts_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
        files_created.append(str(dir_path.relative_to(target_dir)))
    
    # Copy template files if they exist
    if templates_dir.exists():
        for template_file in templates_dir.glob("*-template.xml"):
            # Convert template name: prd-template.xml -> prd.xml
            dest_name = template_file.name.replace("-template", "")
            dest_path = memories_dir / dest_name
            
            # Copy template but don't overwrite existing files
            if not dest_path.exists():
                shutil.copy(template_file, dest_path)
                files_created.append(str(dest_path.relative_to(target_dir)))
    
    # Create .gitkeep files
    for dir_path in [memories_dir, prompts_dir]:
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            files_created.append(str(gitkeep.relative_to(target_dir)))
    
    return files_created


def register_in_repo_registry(
    project_name: str,
    target_dir: Path,
    github_url: str,
    branch: str = "main",
) -> bool:
    """
    Register the project in the framework's repo_registry.yaml.
    
    Args:
        project_name: Name/ID for the project
        target_dir: Path to target repository
        github_url: GitHub URL for the repository
        branch: Default branch
        
    Returns:
        True if registration successful
    """
    registry_path = PROJECT_ROOT / "config" / "repo_registry.yaml"
    
    if not registry_path.exists():
        return False
    
    try:
        with open(registry_path) as f:
            registry = yaml.safe_load(f) or {}
        
        repos = registry.get("repositories", {})
        
        # Create repo ID from project name (sanitize)
        repo_id = project_name.lower().replace(" ", "-").replace("_", "-")
        
        # Don't overwrite existing entries
        if repo_id in repos:
            return True
        
        # Calculate relative path from framework to target
        try:
            rel_path = target_dir.relative_to(PROJECT_ROOT)
        except ValueError:
            # Target is outside framework directory, use absolute path
            rel_path = target_dir
        
        # Add new entry
        repos[repo_id] = {
            "description": f"Target project: {project_name}",
            "github_url": github_url or f"https://github.com/org/{repo_id}",
            "local_path": str(rel_path),
            "branch": branch,
        }
        
        registry["repositories"] = repos
        
        with open(registry_path, "w") as f:
            yaml.dump(registry, f, default_flow_style=False, sort_keys=False)
        
        return True
        
    except Exception:
        return False


def init_project(
    target_dir: str,
    project_type: str = "microservice",
    name: Optional[str] = None,
    description: Optional[str] = None,
    register: bool = True,
) -> InitResult:
    """
    Initialize a target repository for SDLC agent management.
    
    Creates:
    - .sdlc/config.yaml (project configuration)
    - .sdlc/memories/ (agent memory storage)
    - .sdlc/prompts/ (custom prompt overrides)
    - Template files based on project type
    
    Args:
        target_dir: Path to target repository
        project_type: Type of project (microservice, frontend, monolith, data-pipeline)
        name: Project name (auto-detected if not provided)
        description: Project description (auto-detected if not provided)
        register: Whether to register in repo_registry.yaml
        
    Returns:
        InitResult with success status and created files
        
    Example:
        >>> result = init_project("/path/to/my-project", "microservice")
        >>> if result.success:
        ...     print(f"Initialized: {result.files_created}")
    """
    target_path = Path(target_dir).resolve()
    files_created = []
    
    # Validate target directory exists
    if not target_path.exists():
        return InitResult(
            success=False,
            target_dir=target_path,
            files_created=[],
            error=f"Target directory does not exist: {target_path}",
        )
    
    if not target_path.is_dir():
        return InitResult(
            success=False,
            target_dir=target_path,
            files_created=[],
            error=f"Target is not a directory: {target_path}",
        )
    
    # Check if already initialized
    sdlc_config = target_path / ".sdlc" / "config.yaml"
    if sdlc_config.exists():
        return InitResult(
            success=False,
            target_dir=target_path,
            files_created=[],
            config_path=sdlc_config,
            error="Project already initialized (.sdlc/config.yaml exists)",
        )
    
    try:
        # Detect project information
        detected = detect_project_info(target_path)
        
        # Use provided values or fall back to detected
        project_name = name or detected["name"]
        project_desc = description or detected.get("description", "")
        
        # Create project config
        config = create_default_config(
            project_name=project_name,
            project_type=project_type,
            description=project_desc,
        )
        
        # Merge detected tech stack with defaults
        if detected.get("tech_stack"):
            for layer, techs in detected["tech_stack"].items():
                existing = config.tech_stack.get(layer, [])
                config.tech_stack[layer] = list(dict.fromkeys(techs + existing))
        
        # Save config
        config_path = save_project_config(config, target_path)
        files_created.append(str(config_path.relative_to(target_path)))
        
        # Copy template files
        template_files = copy_template_files(target_path, project_type)
        files_created.extend(template_files)
        
        # Register in repo_registry if requested
        registered = False
        if register:
            registered = register_in_repo_registry(
                project_name=project_name,
                target_dir=target_path,
                github_url=detected.get("github_url", ""),
                branch=detected.get("branch", "main"),
            )
        
        return InitResult(
            success=True,
            target_dir=target_path,
            files_created=files_created,
            config_path=config_path,
            registered_in_registry=registered,
        )
        
    except Exception as e:
        return InitResult(
            success=False,
            target_dir=target_path,
            files_created=files_created,
            error=str(e),
        )


def print_init_result(result: InitResult) -> None:
    """Print the initialization result in a user-friendly format."""
    if result.success:
        print(f"\n✅ Successfully initialized SDLC project at: {result.target_dir}")
        print("\n📁 Files created:")
        for f in result.files_created:
            print(f"   - {f}")
        if result.registered_in_registry:
            print("\n📋 Registered in repo_registry.yaml")
        print("\n🚀 Next steps:")
        print("   1. Review .sdlc/config.yaml and customize for your project")
        print("   2. Run: sdlc agent productspec --target . --requirements 'Your requirements'")
    else:
        print(f"\n❌ Initialization failed: {result.error}")
        if result.files_created:
            print("\n📁 Partial files created (may need cleanup):")
            for f in result.files_created:
                print(f"   - {f}")


__all__ = ["init_project", "InitResult", "print_init_result"]

