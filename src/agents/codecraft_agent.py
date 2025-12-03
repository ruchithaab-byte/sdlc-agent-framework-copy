"""CodeCraft agent with specialized prompts.

Uses centralized options builder for consistent SDK configuration
across all agents. Supports frontend, backend, and data development tasks.

Prompts are loaded from templates and rendered with project context.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from src.agents.runner import AgentResult, run_agent, render_agent_prompt
from src.utils.prompt_renderer import render_inline_prompt, get_default_context
from src.config.project_config import load_project_config


# Task-specific prompt templates (Jinja2)
TASK_PROMPTS = {
    "frontend": """
Develop frontend components for {{ project.name }}.

## Context
Load architecture from `.sdlc/memories/architecture_plan.xml`

{% if skills %}
## Skills to Apply
{% for skill in skills %}
- {{ skill }}
{% endfor %}
{% endif %}

## Steps
1. Load architecture plan from memory
2. Apply modern React/Next.js patterns
3. Use component scaffolding for UI
4. Style following project conventions
5. Verify changes with code_execution_verify_change
6. Validate visual layout using Playwright screenshots

## Anti-Patterns to Avoid
- No direct Server Component imports in Client Components
- No non-serializable props crossing component boundaries
- No window/localStorage in Server Components
""",
    "backend": """
Develop backend services for {{ project.name }}.

## Context
Load architecture from `.sdlc/memories/architecture_plan.xml`

{% if tech_stack.backend %}
## Technologies
{{ tech_stack.backend | join(", ") }}
{% endif %}

{% if skills %}
## Skills to Apply
{% for skill in skills %}
- {{ skill }}
{% endfor %}
{% endif %}

## Steps
1. Load architecture plan from memory
2. Follow layered architecture (Controller -> Service -> Repository)
3. Use proper DTOs and data models
4. Implement business logic in service layer
5. Apply rate limiting and security middleware
6. Verify logic via memory_verify_logic
7. Validate code structure and quality

## Anti-Patterns to Avoid
- No business logic in Controllers
- No transactional overhead on read operations
- No blocking I/O in async code paths
""",
    "data": """
Implement data layer for {{ project.name }}.

## Context
Load architecture from `.sdlc/memories/architecture_plan.xml`

{% if tech_stack.data or tech_stack.backend %}
## Technologies
{% if tech_stack.data %}{{ tech_stack.data | join(", ") }}{% endif %}
{% if tech_stack.backend %}{{ tech_stack.backend | join(", ") }}{% endif %}
{% endif %}

{% if skills %}
## Skills to Apply
{% for skill in skills %}
- {{ skill }}
{% endfor %}
{% endif %}

## Steps
1. Load architecture plan from memory
2. Create database schemas with proper migrations
3. Generate migrations with proper naming (V001__, V002__, etc.)
4. Apply immutability principle - never modify applied migrations
5. Configure caching layer if applicable
6. Set up event streaming if needed

## Anti-Patterns to Avoid
- No mutation of applied versioned migration scripts
- No retrospective insertion of migrations
- No cache as source of truth (cache is supplementary)
- No big keys (>1MB) in cache
""",
}


def get_codecraft_prompt(
    task_type: str = "backend",
    target_dir: Optional[Path] = None,
) -> str:
    """
    Get the rendered prompt for CodeCraft agent.
    
    First tries to load the full codecraft.md prompt template,
    then appends task-specific instructions.
    
    Args:
        task_type: Type of coding task (frontend, backend, data)
        target_dir: Optional path to target project directory
        
    Returns:
        Rendered prompt string with project context
    """
    # Get project context
    context = get_default_context()
    if target_dir:
        config = load_project_config(target_dir)
        if config:
            context = config.to_context_dict()
    
    # Try to load full prompt template first
    try:
        base_prompt = render_agent_prompt("codecraft", target_dir)
    except Exception:
        base_prompt = f"You are CodeCraft implementing code for {context['project']['name']}."
    
    # Render task-specific prompt
    task_template = TASK_PROMPTS.get(task_type, TASK_PROMPTS["backend"])
    task_prompt = render_inline_prompt(task_template, context)
    
    return f"{base_prompt}\n\n## Current Task\n{task_prompt}"


async def run_codecraft_agent(
    task_type: str = "backend",
    task_description: Optional[str] = None,
    target_dir: Optional[Path] = None,
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AgentResult:
    """
    Run the CodeCraft agent for code generation.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration. Supports resumption via session ID.
    
    Args:
        task_type: Type of coding task (frontend, backend, data).
        task_description: Optional specific task description to append.
        target_dir: Optional path to target project directory.
        resume: Optional session ID to resume previous conversation.
        permission_mode: Override permission mode (default from profile: acceptEdits).
    
    Returns:
        AgentResult containing session_id for potential resumption.
        
    Example:
        >>> result = await run_codecraft_agent("backend")
        >>> print(f"Session: {result.session_id}")
        
        >>> # With target project
        >>> result = await run_codecraft_agent(
        ...     "frontend",
        ...     target_dir=Path("/path/to/project"),
        ...     task_description="Build the login component"
        ... )
    """
    prompt = get_codecraft_prompt(task_type, target_dir)
    
    if task_description:
        prompt = f"{prompt}\n\n## Specific Task\n{task_description}"
    
    return await run_agent(
        agent_id="codecraft",
        prompt=prompt,
        target_dir=target_dir,
        resume=resume,
        permission_mode_override=permission_mode,
    )


if __name__ == "__main__":
    asyncio.run(run_codecraft_agent("backend"))
