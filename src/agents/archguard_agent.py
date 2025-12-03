"""ArchGuard agent implementation.

Uses centralized options builder for consistent SDK configuration.
Handles architecture design, ADR creation, and Backstage integration.

Prompts are loaded from templates and rendered with project context.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from src.agents.runner import AgentResult, run_agent, render_agent_prompt
from src.config.project_config import load_project_config
from src.utils.prompt_renderer import get_default_context


def get_archguard_prompt(target_dir: Optional[Path] = None) -> str:
    """
    Get the rendered prompt for ArchGuard agent.
    
    Args:
        target_dir: Optional path to target project directory
        
    Returns:
        Rendered prompt string with project context
    """
    # Get project context
    context = get_default_context()
    project_name = "the project"
    if target_dir:
        config = load_project_config(target_dir)
        if config:
            context = config.to_context_dict()
            project_name = config.name
    
    # Try to load full prompt template
    try:
        base_prompt = render_agent_prompt("archguard", target_dir)
    except Exception:
        base_prompt = f"You are ArchGuard designing architecture for {project_name}."
    
    # Define memory paths
    prd_path = ".sdlc/memories/prd.xml"
    arch_path = ".sdlc/memories/architecture_plan.xml"
    
    return f"""{base_prompt}

## Current Task

Design system architecture for {project_name}:

### Steps
1. Load PRD from `{prd_path}`
2. Use plan-architect subagent to research existing patterns
3. Use generate_architecture_plan to create architecture
4. Query Backstage catalog via backstage_catalog_lookup
5. Write ADRs for key decisions with write_adr
6. Store architecture plan in `{arch_path}`

### Output Location
Save architecture plan to: `{arch_path}`
Save ADRs to: `docs/adr/` or `.sdlc/adr/`
"""


async def run_archguard_agent(
    target_dir: Optional[Path] = None,
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AgentResult:
    """
    Run the ArchGuard agent for architecture design.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration.
    
    Args:
        target_dir: Optional path to target project directory.
        resume: Optional session ID to resume.
        permission_mode: Override permission mode.
    
    Returns:
        AgentResult containing session_id for potential resumption.
        
    Example:
        >>> result = await run_archguard_agent()
        >>> print(f"Session: {result.session_id}")
        
        >>> # With target project
        >>> result = await run_archguard_agent(
        ...     target_dir=Path("/path/to/project")
        ... )
    """
    prompt = get_archguard_prompt(target_dir)
    
    return await run_agent(
        agent_id="archguard",
        prompt=prompt,
        target_dir=target_dir,
        resume=resume,
        permission_mode_override=permission_mode,
    )


if __name__ == "__main__":
    asyncio.run(run_archguard_agent())
