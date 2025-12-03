"""
Sub-Agent Manager.

Orchestrates specialized sub-agents following the "Thin Client, Fat Backend" pattern:
- Main agent acts as CEO (high-level decisions)
- Sub-agents handle heavy lifting (research, analysis, testing)
- Only distilled summaries return to main context

Reference: "No Vibes Allowed" - Dex Horthy, HumanLayer
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type

from src.context.firewall import ContextFirewall, IsolatedContext, FirewallResult
from src.agents.subagents.base import BaseSubAgent, SubAgentConfig, SubAgentModel, SubAgentResult
from src.agents.subagents.explorer import ExplorerSubAgent
from src.agents.subagents.researcher import ResearcherSubAgent
from src.agents.subagents.planner import PlannerSubAgent
from src.agents.subagents.code_reviewer import CodeReviewerSubAgent
from src.agents.subagents.test_runner import TestRunnerSubAgent


@dataclass
class SubAgentExecution:
    """Record of a sub-agent execution."""
    agent_name: str
    objective: str
    result: SubAgentResult
    context_id: str
    started_at: datetime
    completed_at: datetime


class SubAgentManager:
    """
    Manages sub-agent spawning and orchestration.
    
    Implements the "Thin Client, Fat Backend" architecture:
    - Main agent is the "CEO" making high-level decisions
    - Sub-agents are specialized "workers" for specific tasks
    - Context firewall ensures no pollution of main context
    
    Model Routing:
    - Haiku: Fast, cheap operations (explorer, test_runner)
    - Sonnet: Capable analysis (researcher, planner, code_reviewer)
    - Opus: Reserved for main agent and complex reasoning
    
    Example:
        >>> manager = SubAgentManager()
        >>> 
        >>> # Spawn explorer to find files
        >>> result = await manager.spawn_explorer(
        ...     "Find all authentication-related files"
        ... )
        >>> print(result.summary)  # Only summary, not raw search results
        >>> 
        >>> # Spawn researcher for deep analysis
        >>> result = await manager.spawn_researcher(
        ...     "Analyze how User authentication works"
        ... )
    """
    
    # Sub-agent type registry
    AGENT_TYPES: Dict[str, Type[BaseSubAgent]] = {
        "explorer": ExplorerSubAgent,
        "researcher": ResearcherSubAgent,
        "planner": PlannerSubAgent,
        "code-reviewer": CodeReviewerSubAgent,
        "test-runner": TestRunnerSubAgent,
    }
    
    def __init__(
        self,
        firewall: Optional[ContextFirewall] = None,
        max_concurrent: int = 3,
    ):
        """
        Initialize the Sub-Agent Manager.
        
        Args:
            firewall: Context firewall for isolation. Creates one if not provided.
            max_concurrent: Maximum concurrent sub-agents.
        """
        self.firewall = firewall or ContextFirewall()
        self.max_concurrent = max_concurrent
        
        self._active_agents: Dict[str, BaseSubAgent] = {}
        self._execution_history: List[SubAgentExecution] = []
        
        # Callbacks
        self._on_spawn: Optional[Callable[[str, str], None]] = None
        self._on_complete: Optional[Callable[[SubAgentExecution], None]] = None
    
    async def spawn(
        self,
        agent_type: str,
        objective: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> SubAgentResult:
        """
        Spawn a sub-agent for a specific task.
        
        This creates an isolated context, runs the sub-agent,
        and returns only the distilled summary.
        
        Args:
            agent_type: Type of sub-agent to spawn.
            objective: What the sub-agent should accomplish.
            context: Optional additional context.
            parent_id: ID of parent context (for nested sub-agents).
            
        Returns:
            SubAgentResult with distilled findings.
        """
        if agent_type not in self.AGENT_TYPES:
            raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(self.AGENT_TYPES.keys())}")
        
        # Check capacity
        if len(self._active_agents) >= self.max_concurrent:
            raise RuntimeError(
                f"Maximum concurrent sub-agents ({self.max_concurrent}) reached. "
                f"Wait for existing sub-agents to complete."
            )
        
        # Create sub-agent
        agent_class = self.AGENT_TYPES[agent_type]
        agent = agent_class()
        
        # Create isolated context
        isolated_context = self.firewall.create_isolated_context(
            objective=objective,
            parent_id=parent_id,
            allowed_tools=agent.config.tools,
            max_tokens=agent.config.max_tokens,
            max_turns=agent.config.max_turns,
            timeout_seconds=agent.config.timeout_seconds,
        )
        
        # Track active agent
        self._active_agents[isolated_context.id] = agent
        
        if self._on_spawn:
            self._on_spawn(agent_type, objective)
        
        started_at = datetime.utcnow()
        
        try:
            # Execute sub-agent
            result = await agent.execute(objective, context)
            
            # Complete isolated context (kill switch)
            self.firewall.complete_context(
                isolated_context.id,
                summary=result.summary,
                findings=result.findings,
                file_references=result.file_references,
                artifacts=result.artifacts,
                tokens_consumed=result.tokens_consumed,
                turns_used=result.turns_used,
                error=result.error,
            )
            
            # Record execution
            execution = SubAgentExecution(
                agent_name=agent_type,
                objective=objective,
                result=result,
                context_id=isolated_context.id,
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )
            self._execution_history.append(execution)
            
            if self._on_complete:
                self._on_complete(execution)
            
            return result
            
        finally:
            # Always remove from active (kill switch)
            if isolated_context.id in self._active_agents:
                del self._active_agents[isolated_context.id]
    
    async def spawn_explorer(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Spawn an explorer sub-agent for fast codebase search.
        
        Uses Haiku model - optimized for speed.
        
        Args:
            objective: What to search for.
            context: Optional additional context.
            
        Returns:
            SubAgentResult with found locations.
        """
        return await self.spawn("explorer", objective, context=context)
    
    async def spawn_researcher(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Spawn a researcher sub-agent for deep analysis.
        
        Uses Sonnet model - optimized for capability.
        
        Args:
            objective: What to analyze.
            context: Optional additional context.
            
        Returns:
            SubAgentResult with analysis findings.
        """
        return await self.spawn("researcher", objective, context=context)
    
    async def spawn_planner(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Spawn a planner sub-agent for planning research.
        
        Uses Sonnet model - gathers context for planning.
        
        Args:
            objective: What we're planning.
            context: Optional additional context.
            
        Returns:
            SubAgentResult with planning context.
        """
        return await self.spawn("planner", objective, context=context)
    
    async def spawn_code_reviewer(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Spawn a code reviewer sub-agent.
        
        Uses Sonnet model - thorough code review.
        
        Args:
            objective: What to review.
            context: Optional additional context.
            
        Returns:
            SubAgentResult with review findings.
        """
        return await self.spawn("code-reviewer", objective, context=context)
    
    async def spawn_test_runner(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubAgentResult:
        """
        Spawn a test runner sub-agent.
        
        Uses Haiku model - fast test execution.
        
        Args:
            objective: What tests to run.
            context: Optional additional context (test command, etc.).
            
        Returns:
            SubAgentResult with test results.
        """
        return await self.spawn("test-runner", objective, context=context)
    
    async def spawn_parallel(
        self,
        tasks: List[Dict[str, Any]],
    ) -> List[SubAgentResult]:
        """
        Spawn multiple sub-agents in parallel.
        
        Following HumanLayer's pattern of parallel research tasks.
        
        Args:
            tasks: List of task dicts with 'type', 'objective', and optional 'context'.
            
        Returns:
            List of SubAgentResult in same order as tasks.
        """
        async def run_task(task: Dict[str, Any]) -> SubAgentResult:
            return await self.spawn(
                task["type"],
                task["objective"],
                context=task.get("context"),
            )
        
        results = await asyncio.gather(
            *[run_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(SubAgentResult(
                    success=False,
                    summary=f"Task failed: {str(result)}",
                    error=str(result),
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_active_agents(self) -> List[str]:
        """Get list of active agent context IDs."""
        return list(self._active_agents.keys())
    
    def get_execution_history(
        self,
        agent_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[SubAgentExecution]:
        """
        Get execution history.
        
        Args:
            agent_type: Optional filter for agent type.
            limit: Maximum entries to return.
            
        Returns:
            List of SubAgentExecution records.
        """
        history = self._execution_history
        
        if agent_type:
            history = [e for e in history if e.agent_name == agent_type]
        
        return history[-limit:]
    
    def get_total_tokens_consumed(self) -> int:
        """Get total tokens consumed by all sub-agents."""
        return sum(e.result.tokens_consumed for e in self._execution_history)
    
    # Callback setters
    def on_spawn(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for sub-agent spawn."""
        self._on_spawn = callback
    
    def on_complete(self, callback: Callable[[SubAgentExecution], None]) -> None:
        """Set callback for sub-agent completion."""
        self._on_complete = callback


__all__ = [
    "SubAgentManager",
    "SubAgentExecution",
]

