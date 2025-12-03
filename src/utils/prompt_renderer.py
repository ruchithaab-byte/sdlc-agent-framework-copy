"""
Prompt Template Renderer

Renders agent prompts with project context using Jinja2 templates.
Supports loading prompts from both the framework and target project directories.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

from config.agent_config import PROJECT_ROOT


# Framework prompts directory
FRAMEWORK_PROMPTS_DIR = PROJECT_ROOT / "prompts" / "agents"


def create_jinja_environment(prompts_dir: Path) -> Environment:
    """
    Create a Jinja2 environment for prompt rendering.
    
    Args:
        prompts_dir: Directory containing prompt templates
        
    Returns:
        Configured Jinja2 Environment
    """
    return Environment(
        loader=FileSystemLoader(str(prompts_dir)),
        autoescape=select_autoescape(enabled_extensions=(), default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_prompt(
    prompt_name: str,
    context: Dict[str, Any],
    target_prompts_dir: Optional[Path] = None,
) -> str:
    """
    Render an agent prompt with project context.
    
    Looks for prompts in this order:
    1. Target project's .sdlc/prompts/ directory (if provided)
    2. Framework's prompts/agents/ directory
    
    Args:
        prompt_name: Name of the prompt file (without .md extension)
        context: Dictionary with project context for template rendering
        target_prompts_dir: Optional path to target project's prompts directory
        
    Returns:
        Rendered prompt string
        
    Raises:
        TemplateNotFound: If prompt template doesn't exist in any location
    """
    template_name = f"{prompt_name}.md"
    
    # Try target project's prompts first
    if target_prompts_dir and target_prompts_dir.exists():
        target_template = target_prompts_dir / template_name
        if target_template.exists():
            env = create_jinja_environment(target_prompts_dir)
            template = env.get_template(template_name)
            return template.render(**context)
    
    # Fall back to framework prompts
    if FRAMEWORK_PROMPTS_DIR.exists():
        framework_template = FRAMEWORK_PROMPTS_DIR / template_name
        if framework_template.exists():
            env = create_jinja_environment(FRAMEWORK_PROMPTS_DIR)
            template = env.get_template(template_name)
            return template.render(**context)
    
    raise TemplateNotFound(f"Prompt '{prompt_name}' not found in target or framework prompts")


def render_inline_prompt(
    template_string: str,
    context: Dict[str, Any],
) -> str:
    """
    Render an inline prompt template string.
    
    Useful for prompts that are defined in agent code but need 
    project context injection.
    
    Args:
        template_string: Jinja2 template string
        context: Dictionary with project context
        
    Returns:
        Rendered prompt string
    """
    from jinja2 import Template
    template = Template(template_string, trim_blocks=True, lstrip_blocks=True)
    return template.render(**context)


def get_default_context(
    project_name: str = "Unknown Project",
    project_type: str = "microservice",
    description: str = "",
    tech_stack: Optional[Dict[str, Any]] = None,
    skills: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Create a default context dictionary for prompt rendering.
    
    Args:
        project_name: Name of the project
        project_type: Type of project
        description: Project description
        tech_stack: Technology stack dictionary
        skills: List of skills to apply
        
    Returns:
        Context dictionary suitable for Jinja2 rendering
    """
    return {
        "project": {
            "name": project_name,
            "type": project_type,
            "description": description,
            "tech_stack": tech_stack or {},
            "skills": skills or [],
        },
        "tech_stack": tech_stack or {},
        "skills": skills or [],
    }


def load_and_render_prompt(
    agent_name: str,
    context: Dict[str, Any],
    target_dir: Optional[Path] = None,
) -> str:
    """
    Load and render a prompt for a specific agent.
    
    Convenience function that combines prompt loading with project context.
    
    Args:
        agent_name: Name of the agent (productspec, archguard, codecraft, etc.)
        context: Project context dictionary (from ProjectConfig.to_context_dict())
        target_dir: Optional target project directory
        
    Returns:
        Rendered prompt ready for agent use
    """
    # Determine target prompts directory
    target_prompts_dir = None
    if target_dir:
        target_prompts_dir = target_dir / ".sdlc" / "prompts"
    
    return render_prompt(agent_name, context, target_prompts_dir)


__all__ = [
    "render_prompt",
    "render_inline_prompt",
    "get_default_context",
    "load_and_render_prompt",
]

