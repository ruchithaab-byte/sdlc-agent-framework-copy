"""ProductSpec agent implementation.

Uses centralized options builder for consistent SDK configuration.
Creates PRDs from requirements and integrates with Linear.

Note: This agent yields messages for streaming use cases.
Prompts are loaded from templates and rendered with project context.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator, Optional

from src.agents.runner import run_agent_streaming, render_agent_prompt
from src.config.project_config import load_project_config
from src.utils.prompt_renderer import get_default_context


def get_productspec_prompt(
    requirements: str,
    target_dir: Optional[Path] = None,
) -> str:
    """
    Get the rendered prompt for ProductSpec agent.
    
    Args:
        requirements: The requirements text to analyze
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
    
    # Try to load full prompt template
    try:
        base_prompt = render_agent_prompt("productspec", target_dir)
    except Exception:
        base_prompt = f"You are ProductSpec creating a PRD for {context['project']['name']}."
    
    # Build the full prompt
    memory_path = ".sdlc/memories/prd.xml"
    
    return f"""{base_prompt}

## Current Task

Analyze the following requirements and produce a PRD stored at `{memory_path}`.

### Requirements
{requirements}

### Steps
1. Research using mintlify_search_docs skill
2. Run competitor_analysis to gather comparables
3. Create a Linear epic via linear_create_epic
4. Store the resulting PRD in memory for downstream agents (ArchGuard, SprintMaster)

### Output Location
Save PRD to: `{memory_path}`
"""


async def run_productspec_agent(
    requirements: str,
    target_dir: Optional[Path] = None,
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AsyncIterator:
    """
    Run the ProductSpec agent to create a PRD.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration. Yields messages for streaming consumers.
    
    Args:
        requirements: The requirements text to analyze.
        target_dir: Optional path to target project directory.
        resume: Optional session ID to resume.
        permission_mode: Override permission mode.
    
    Yields:
        Messages from the agent conversation.
        
    Example:
        >>> async for message in run_productspec_agent("Build auth service"):
        ...     print(message)
        
        >>> # With target project
        >>> async for message in run_productspec_agent(
        ...     "Build login system",
        ...     target_dir=Path("/path/to/project")
        ... ):
        ...     print(message)
    """
    prompt = get_productspec_prompt(requirements, target_dir)
    
    async for message in run_agent_streaming(
        agent_id="productspec",
        prompt=prompt,
        target_dir=target_dir,
        resume=resume,
        permission_mode_override=permission_mode,
    ):
        yield message


if __name__ == "__main__":
    async def _main():
        async for event in run_productspec_agent("Build authentication service with JWT"):
            print(event)

    asyncio.run(_main())
