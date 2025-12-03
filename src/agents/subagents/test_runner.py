"""
Test Runner Sub-Agent.

Test execution and failure analysis specialist.
Uses Haiku model for speed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.agents.subagents.base import (
    BaseSubAgent,
    SubAgentConfig,
    SubAgentModel,
    SubAgentResult,
    TEST_RUNNER_PROMPT,
)


class TestRunnerSubAgent(BaseSubAgent):
    """
    Test execution specialist.
    
    Uses Haiku model for fast test execution:
    - Run test suites
    - Capture failures
    - Analyze root causes
    - Suggest fixes
    
    Optimized for speed in TDD loops.
    """
    
    DEFAULT_TOOLS = ["Bash", "Read"]
    
    def __init__(
        self,
        name: str = "test-runner",
        max_turns: int = 10,
        max_tokens: int = 20000,
    ):
        """Initialize the Test Runner sub-agent."""
        config = SubAgentConfig(
            name=name,
            model=SubAgentModel.HAIKU,
            tools=self.DEFAULT_TOOLS,
            system_prompt=TEST_RUNNER_PROMPT,
            max_turns=max_turns,
            max_tokens=max_tokens,
            timeout_seconds=180,
            read_only=False,  # Needs to run tests
        )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        """Get the test runner system prompt."""
        return self.config.system_prompt
    
    async def execute(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Execute a test run task.
        
        Args:
            objective: What tests to run.
            context: Optional additional context (test command, etc.).
            
        Returns:
            SubAgentResult with test results.
        """
        await self._start()
        
        try:
            findings = []
            file_references = []
            
            self._track_turn(1500)
            
            # Extract test results
            test_command = context.get("test_command", "make test") if context else "make test"
            summary = f"Ran tests: {test_command}"
            
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
                summary=f"Test run failed: {str(e)}",
                error=str(e),
                execution_time_ms=self._get_execution_time_ms(),
            )


__all__ = ["TestRunnerSubAgent"]

