"""SprintMaster agent implementation.

Uses centralized options builder for consistent SDK configuration.
Handles sprint planning, task breakdown, and Linear integration.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.agents.runner import AgentResult, run_agent
from src.utils.constants import MEMORY_ARCHITECTURE_PLAN_PATH


async def run_sprintmaster_agent(
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AgentResult:
    """
    Run the SprintMaster agent for sprint planning.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration.
    
    Args:
        resume: Optional session ID to resume.
        permission_mode: Override permission mode.
    
    Returns:
        AgentResult containing session_id for potential resumption.
    """
    prompt = f"""
    Create sprint plan for the authentication microservice by:
    1. Loading architecture plan from {MEMORY_ARCHITECTURE_PLAN_PATH}
    2. Using code_execution_task_breakdown for task analysis
    3. Creating a Linear sprint using linear_sprint_planning
    4. Returning story points, dependencies, resource allocation, and risks
    """
    
    return await run_agent(
        agent_id="sprintmaster",
        prompt=prompt,
        resume=resume,
        permission_mode_override=permission_mode,
    )


if __name__ == "__main__":
    asyncio.run(run_sprintmaster_agent())
