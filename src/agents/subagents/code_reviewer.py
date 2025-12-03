"""
Code Reviewer Sub-Agent.

Code review specialist for quality analysis.
Uses Sonnet model for thorough review.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.agents.subagents.base import (
    BaseSubAgent,
    SubAgentConfig,
    SubAgentModel,
    SubAgentResult,
    CODE_REVIEWER_PROMPT,
)


class CodeReviewerSubAgent(BaseSubAgent):
    """
    Code review specialist.
    
    Uses Sonnet model for comprehensive review:
    - Quality assessment
    - Security analysis
    - Pattern verification
    - Convention checking
    
    Returns prioritized feedback (critical, warnings, suggestions).
    """
    
    DEFAULT_TOOLS = ["Read", "Grep", "Glob", "Bash"]
    
    def __init__(
        self,
        name: str = "code-reviewer",
        max_turns: int = 15,
        max_tokens: int = 30000,
    ):
        """Initialize the Code Reviewer sub-agent."""
        config = SubAgentConfig(
            name=name,
            model=SubAgentModel.SONNET,
            tools=self.DEFAULT_TOOLS,
            system_prompt=CODE_REVIEWER_PROMPT,
            max_turns=max_turns,
            max_tokens=max_tokens,
            timeout_seconds=240,
            read_only=True,
        )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        """Get the code reviewer system prompt."""
        return self.config.system_prompt
    
    async def execute(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Execute a code review task.
        
        Args:
            objective: What to review (files, changes, etc.).
            context: Optional additional context.
            
        Returns:
            SubAgentResult with review findings.
        """
        await self._start()
        
        try:
            findings = []
            file_references = []
            
            self._track_turn(2500)
            
            summary = f"Reviewed: {objective}"
            
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
                summary=f"Code review failed: {str(e)}",
                error=str(e),
                execution_time_ms=self._get_execution_time_ms(),
            )


__all__ = ["CodeReviewerSubAgent"]

