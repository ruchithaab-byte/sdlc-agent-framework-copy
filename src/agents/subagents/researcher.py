"""
Researcher Sub-Agent.

Deep analysis agent for comprehensive code understanding.
Uses Sonnet model for capability.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.agents.subagents.base import (
    BaseSubAgent,
    SubAgentConfig,
    SubAgentModel,
    SubAgentResult,
    RESEARCHER_PROMPT,
)


class ResearcherSubAgent(BaseSubAgent):
    """
    Deep analysis researcher.
    
    Uses Sonnet model for comprehensive analysis:
    - Implementation tracing
    - Data flow analysis
    - Dependency mapping
    - Pattern recognition
    
    Has access to navigation tools (find_definition, find_references).
    """
    
    DEFAULT_TOOLS = [
        "Read", "Grep", "Glob",
        "list_symbols", "find_definition", "find_references", "get_call_graph"
    ]
    
    def __init__(
        self,
        name: str = "researcher",
        max_turns: int = 20,
        max_tokens: int = 40000,
    ):
        """Initialize the Researcher sub-agent."""
        config = SubAgentConfig(
            name=name,
            model=SubAgentModel.SONNET,
            tools=self.DEFAULT_TOOLS,
            system_prompt=RESEARCHER_PROMPT,
            max_turns=max_turns,
            max_tokens=max_tokens,
            timeout_seconds=300,
            read_only=False,  # Can analyze but respects context
        )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        """Get the researcher system prompt."""
        return self.config.system_prompt
    
    async def execute(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Execute a research task.
        
        Args:
            objective: What to analyze.
            context: Optional additional context.
            
        Returns:
            SubAgentResult with analysis findings.
        """
        await self._start()
        
        try:
            # In a full implementation, this would use the Claude SDK
            # with Sonnet model and navigation tools
            
            findings = []
            file_references = []
            
            self._track_turn(3000)  # Estimate for deeper analysis
            
            summary = f"Analyzed: {objective}"
            
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
                summary=f"Research failed: {str(e)}",
                error=str(e),
                execution_time_ms=self._get_execution_time_ms(),
            )


__all__ = ["ResearcherSubAgent"]

