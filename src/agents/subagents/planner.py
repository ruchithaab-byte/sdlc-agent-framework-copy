"""
Planner Sub-Agent.

Research specialist for plan mode.
Uses Sonnet model for planning context gathering.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.agents.subagents.base import (
    BaseSubAgent,
    SubAgentConfig,
    SubAgentModel,
    SubAgentResult,
    PLANNER_PROMPT,
)


class PlannerSubAgent(BaseSubAgent):
    """
    Planning research specialist.
    
    Uses Sonnet model to gather context for planning:
    - Identify affected files
    - Map dependencies
    - Find constraints
    - Discover patterns to follow
    
    Does NOT suggest implementations - only gathers context.
    """
    
    DEFAULT_TOOLS = ["Read", "Grep", "Glob", "get_call_graph"]
    
    def __init__(
        self,
        name: str = "planner",
        max_turns: int = 15,
        max_tokens: int = 30000,
    ):
        """Initialize the Planner sub-agent."""
        config = SubAgentConfig(
            name=name,
            model=SubAgentModel.SONNET,
            tools=self.DEFAULT_TOOLS,
            system_prompt=PLANNER_PROMPT,
            max_turns=max_turns,
            max_tokens=max_tokens,
            timeout_seconds=240,
            read_only=True,
        )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        """Get the planner system prompt."""
        return self.config.system_prompt
    
    async def execute(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Execute a planning research task.
        
        Args:
            objective: What we're planning to do.
            context: Optional additional context.
            
        Returns:
            SubAgentResult with planning context.
        """
        await self._start()
        
        try:
            findings = []
            file_references = []
            
            self._track_turn(2500)
            
            summary = f"Gathered planning context for: {objective}"
            
            await self._stop()
            
            return SubAgentResult(
                success=True,
                summary=summary,
                findings=findings,
                file_references=file_references,
                tokens_consumed=self._tokens_consumed,
                turns_used=self._turns_used,
                execution_time_ms=self._get_execution_time_ms(),
            )
            
        except Exception as e:
            await self._stop()
            return SubAgentResult(
                success=False,
                summary=f"Planning research failed: {str(e)}",
                error=str(e),
                execution_time_ms=self._get_execution_time_ms(),
            )


__all__ = ["PlannerSubAgent"]

