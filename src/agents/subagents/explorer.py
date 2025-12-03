"""
Explorer Sub-Agent.

Fast, read-only agent for codebase exploration.
Uses Haiku model for speed and efficiency.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from src.agents.subagents.base import (
    BaseSubAgent,
    SubAgentConfig,
    SubAgentModel,
    SubAgentResult,
    EXPLORER_PROMPT,
)


class ExplorerSubAgent(BaseSubAgent):
    """
    Fast, read-only codebase explorer.
    
    Uses Haiku model for quick searches:
    - File pattern matching
    - Symbol listing
    - Content searching
    
    Does NOT modify files - read-only mode enforced.
    """
    
    DEFAULT_TOOLS = ["Read", "Grep", "Glob", "list_symbols"]
    
    def __init__(
        self,
        name: str = "explorer",
        max_turns: int = 10,
        max_tokens: int = 20000,
    ):
        """Initialize the Explorer sub-agent."""
        config = SubAgentConfig(
            name=name,
            model=SubAgentModel.HAIKU,
            tools=self.DEFAULT_TOOLS,
            system_prompt=EXPLORER_PROMPT,
            max_turns=max_turns,
            max_tokens=max_tokens,
            timeout_seconds=120,
            read_only=True,
        )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        """Get the explorer system prompt."""
        return self.config.system_prompt
    
    async def execute(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Execute an exploration task.
        
        Args:
            objective: What to search for.
            context: Optional additional context (e.g., scope directories).
            
        Returns:
            SubAgentResult with found locations.
        """
        await self._start()
        
        try:
            # In a full implementation, this would use the Claude SDK
            # For now, we simulate the exploration
            
            findings = []
            file_references = []
            
            # Extract search patterns from objective
            # This would be done by the actual LLM
            self._track_turn(1000)
            
            # Simulate finding results
            summary = f"Explored codebase for: {objective}"
            
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
                summary=f"Exploration failed: {str(e)}",
                error=str(e),
                execution_time_ms=self._get_execution_time_ms(),
            )


__all__ = ["ExplorerSubAgent"]

