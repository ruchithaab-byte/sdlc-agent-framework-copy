"""
Context Firewall for Sub-Agent Isolation.

Implements the "Context Firewall" pattern from HumanLayer:
- Sub-agents operate in isolated context forks (using SessionContext)
- Only distilled summaries return to the main agent
- Prevents context pollution from search/research operations

Phase 2 Refactoring: Now uses SessionContext instead of IsolatedContext

Reference: "No Vibes Allowed: Solving Hard Problems in Complex Codebases" - Dex Horthy
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from src.orchestrator.session_manager import SessionContext


class IsolationLevel(Enum):
    """Level of context isolation for sub-agents."""
    NONE = "none"           # Share full context (not recommended)
    PARTIAL = "partial"     # Share system prompt and objective only
    FULL = "full"           # Completely isolated context
    STRICT = "strict"       # Isolated + output filtering


@dataclass
class FirewallResult:
    """Result from a firewalled sub-agent execution."""
    success: bool
    context_id: str
    
    # The distilled output (only this goes to parent context)
    summary: str
    key_findings: List[str] = field(default_factory=list)
    file_references: List[str] = field(default_factory=list)
    
    # Metrics
    tokens_consumed: int = 0
    tokens_returned: int = 0  # Always << tokens_consumed
    execution_time_ms: float = 0.0
    turns_used: int = 0
    
    # Error info
    error: Optional[str] = None
    
    @property
    def compression_ratio(self) -> float:
        """How much context was filtered out."""
        if self.tokens_consumed == 0:
            return 0.0
        return 1.0 - (self.tokens_returned / self.tokens_consumed)


class ContextFirewall:
    """
    Manages isolated context forks for sub-agents.
    
    Phase 2 Refactoring: Now uses SessionContext.create_isolated_fork()
    instead of creating separate IsolatedContext objects.
    
    The Context Firewall ensures that:
    1. Sub-agents operate in isolated context (no pollution to main agent)
    2. Only distilled summaries return to the parent
    3. Raw search results, failed queries, etc. never enter main context
    
    This is critical for the "Thin Client, Fat Backend" pattern where
    the main agent stays focused while sub-agents do heavy lifting.
    
    Example:
        >>> from src.orchestrator.session_manager import SessionContext
        >>> firewall = ContextFirewall()
        >>> 
        >>> # Create isolated fork from parent session
        >>> parent_session = SessionContext(...)
        >>> fork = parent_session.create_isolated_fork(
        ...     objective="Find the User class definition",
        ...     tools=["Read", "Grep", "Glob", "list_symbols"],
        ... )
        >>> 
        >>> # Track the fork in firewall
        >>> firewall.track_fork(fork)
        >>> 
        >>> # Sub-agent executes in isolation...
        >>> # (grep, read files, search, etc.)
        >>> 
        >>> # Only summary returns to main agent
        >>> result = firewall.complete_context(
        ...     fork.session_id,
        ...     summary="User class is in src/models/user.ts:45-200",
        ...     findings=["Handles authentication", "Has role checking"],
        ... )
        >>> 
        >>> # Main agent gets: "User class is in src/models/user.ts:45-200"
        >>> # Main agent does NOT get: 50 grep results, failed searches, etc.
    """
    
    def __init__(
        self,
        default_isolation: IsolationLevel = IsolationLevel.FULL,
        max_active_contexts: int = 10,
    ):
        """
        Initialize the Context Firewall.
        
        Args:
            default_isolation: Default isolation level for new contexts.
            max_active_contexts: Maximum concurrent isolated contexts.
        """
        self.default_isolation = default_isolation
        self.max_active_contexts = max_active_contexts
        
        # Track active SessionContext forks (Phase 2: using SessionContext now)
        self._active_forks: Dict[str, 'SessionContext'] = {}
        self._completed_results: Dict[str, FirewallResult] = {}
        
        # Callbacks
        self._on_context_created: Optional[Callable[['SessionContext'], None]] = None
        self._on_context_completed: Optional[Callable[[FirewallResult], None]] = None
    
    def track_fork(self, fork: 'SessionContext') -> None:
        """
        Track a SessionContext fork created by create_isolated_fork().
        
        Args:
            fork: The SessionContext fork to track
            
        Raises:
            FirewallError: If max active contexts exceeded
        """
        if len(self._active_forks) >= self.max_active_contexts:
            raise FirewallError(
                f"Maximum active contexts ({self.max_active_contexts}) exceeded. "
                f"Complete or cancel existing sub-agent contexts first."
            )
        
        if not fork.is_subagent:
            raise FirewallError("Can only track sub-agent forks")
        
        self._active_forks[fork.session_id] = fork
        
        if self._on_context_created:
            self._on_context_created(fork)
    
    def create_isolated_context(
        self,
        parent_session: 'SessionContext',
        objective: str,
        *,
        allowed_tools: Optional[List[str]] = None,
        max_tokens: int = 30000,
        max_turns: int = 10,
    ) -> 'SessionContext':
        """
        Create an isolated context fork for a sub-agent.
        
        Phase 2: Now delegates to SessionContext.create_isolated_fork()
        
        Args:
            parent_session: Parent SessionContext to fork from
            objective: What the sub-agent should accomplish
            allowed_tools: Tools the sub-agent can use
            max_tokens: Token budget for the sub-agent
            max_turns: Maximum conversation turns
            
        Returns:
            SessionContext fork for the sub-agent
            
        Raises:
            FirewallError: If max active contexts exceeded
        """
        # Use SessionContext.create_isolated_fork() (Phase 2)
        fork = parent_session.create_isolated_fork(
            objective=objective,
            tools=allowed_tools or [],
            max_turns=max_turns,
            max_tokens=max_tokens,
        )
        
        # Track the fork
        self.track_fork(fork)
        
        return fork
    
    def complete_context(
        self,
        session_id: str,
        summary: str,
        *,
        findings: Optional[List[str]] = None,
        file_references: Optional[List[str]] = None,
        artifacts: Optional[Dict[str, str]] = None,
        tokens_consumed: int = 0,
        turns_used: int = 0,
        error: Optional[str] = None,
    ) -> FirewallResult:
        """
        Complete an isolated context and return filtered results.
        
        This is the "Kill Switch" - the sub-agent terminates and only
        the distilled summary returns to the parent context.
        
        Phase 2: Now works with SessionContext forks
        
        Args:
            session_id: Session ID of the fork to complete
            summary: Distilled summary for parent context
            findings: List of key findings
            file_references: List of file:line references
            artifacts: Any artifacts to pass back (e.g., code snippets)
            tokens_consumed: Tokens used by the sub-agent
            turns_used: Conversation turns used
            error: Error message if execution failed
            
        Returns:
            FirewallResult with filtered output
        """
        if session_id not in self._active_forks:
            raise FirewallError(f"Fork {session_id} not found in active forks")
        
        fork = self._active_forks[session_id]
        created_at = datetime.utcnow()  # Approximate (could track in fork)
        completed_at = datetime.utcnow()
        
        # Remove from active forks (Kill Switch - fork dies here)
        del self._active_forks[session_id]
        
        # Estimate tokens returned (summary + findings + references)
        tokens_returned = len(summary.split()) * 1.3
        for finding in (findings or []):
            tokens_returned += len(finding.split()) * 1.3
        for ref in (file_references or []):
            tokens_returned += len(ref.split()) * 1.3
        
        result = FirewallResult(
            success=error is None,
            context_id=session_id,
            summary=summary,
            key_findings=findings or [],
            file_references=file_references or [],
            tokens_consumed=tokens_consumed,
            tokens_returned=int(tokens_returned),
            execution_time_ms=(completed_at - created_at).total_seconds() * 1000,
            turns_used=turns_used,
            error=error,
        )
        
        self._completed_results[session_id] = result
        
        if self._on_context_completed:
            self._on_context_completed(result)
        
        return result
    
    def cancel_context(self, session_id: str) -> None:
        """
        Cancel an active fork without returning results.
        
        Args:
            session_id: Session ID of fork to cancel
        """
        if session_id in self._active_forks:
            del self._active_forks[session_id]
    
    def get_fork(self, session_id: str) -> Optional['SessionContext']:
        """Get a fork by session ID."""
        return self._active_forks.get(session_id)
    
    def get_result(self, context_id: str) -> Optional[FirewallResult]:
        """Get the result of a completed context."""
        return self._completed_results.get(context_id)
    
    def get_active_forks(self) -> List['SessionContext']:
        """Get all active forks."""
        return list(self._active_forks.values())
    
    def cleanup_old_results(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old completed results.
        
        Args:
            max_age_seconds: Maximum age of results to keep
            
        Returns:
            Number of results cleaned up
        """
        # Phase 2: Simplified - just clean up old results
        # Active forks are managed by complete_context() and cancel_context()
        now = datetime.utcnow()
        to_remove = []
        
        for session_id, result in self._completed_results.items():
            # Results don't have timestamps, so we'll keep them all for now
            # In production, you'd add a timestamp to FirewallResult
            pass
        
        return len(to_remove)
    
    def get_summary_for_parent(self, context_id: str) -> str:
        """
        Get the summary string to inject into parent context.
        
        This is the filtered output that goes back to the main agent.
        
        Args:
            context_id: ID of completed context.
            
        Returns:
            Formatted summary string.
        """
        result = self._completed_results.get(context_id)
        if not result:
            return ""
        
        parts = [f"## Sub-Agent Result: {context_id}"]
        parts.append(f"\n{result.summary}")
        
        if result.key_findings:
            parts.append("\n### Findings:")
            for finding in result.key_findings:
                parts.append(f"- {finding}")
        
        if result.file_references:
            parts.append("\n### References:")
            for ref in result.file_references:
                parts.append(f"- `{ref}`")
        
        return "\n".join(parts)
    
    # Callback setters
    def on_context_created(self, callback: Callable[['SessionContext'], None]) -> None:
        """Set callback for fork creation."""
        self._on_context_created = callback
    
    def on_context_completed(self, callback: Callable[[FirewallResult], None]) -> None:
        """Set callback for fork completion."""
        self._on_context_completed = callback


class FirewallError(Exception):
    """Raised when firewall operations fail."""
    pass


__all__ = [
    "ContextFirewall",
    "IsolatedContext",
    "IsolationLevel",
    "FirewallResult",
    "FirewallError",
]

