"""
Cost Tracker for SDLC Agents.

Tracks token usage and costs following SDK best practices from TrackingCostAndUsage.md:
- Deduplicate by message ID (same ID = same usage)
- Track per-step usage for detailed billing
- ResultMessage contains authoritative total_cost_usd
- Support budget enforcement

Usage:
    tracker = CostTracker(budget_usd=5.0)
    
    # Process messages as they arrive
    tracker.process_message(message)
    
    # Check budget
    if tracker.is_budget_exceeded():
        # Handle budget exceeded
        pass
    
    # Get final summary
    summary = tracker.get_summary()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ContextHealth(Enum):
    """
    Health status of the context window.
    
    Based on "No Vibes Allowed" - prevents entry into the "Dumb Zone"
    where signal-to-noise ratio drops due to context saturation.
    """
    HEALTHY = "healthy"      # < 70% capacity - normal operation
    WARNING = "warning"      # 70-85% capacity - consider compaction
    CRITICAL = "critical"    # 85-95% capacity - require Plan before code
    SATURATED = "saturated"  # > 95% capacity - force compaction


# Claude API pricing (as of 2024) - can be updated
# These are approximate - actual costs from total_cost_usd in ResultMessage are authoritative
PRICING = {
    "claude-sonnet-4-20250514": {
        "input_per_1k": 0.003,
        "output_per_1k": 0.015,
        "cache_read_per_1k": 0.0003,
        "cache_create_per_1k": 0.00375,
    },
    "claude-3-5-sonnet-20241022": {
        "input_per_1k": 0.003,
        "output_per_1k": 0.015,
        "cache_read_per_1k": 0.0003,
        "cache_create_per_1k": 0.00375,
    },
    "claude-3-opus-20240229": {
        "input_per_1k": 0.015,
        "output_per_1k": 0.075,
        "cache_read_per_1k": 0.0015,
        "cache_create_per_1k": 0.01875,
    },
    "claude-3-haiku-20240307": {
        "input_per_1k": 0.00025,
        "output_per_1k": 0.00125,
        "cache_read_per_1k": 0.00003,
        "cache_create_per_1k": 0.0003,
    },
    # Default pricing (Sonnet-level)
    "default": {
        "input_per_1k": 0.003,
        "output_per_1k": 0.015,
        "cache_read_per_1k": 0.0003,
        "cache_create_per_1k": 0.00375,
    },
}


@dataclass
class StepUsage:
    """Usage data for a single step (request/response pair)."""
    message_id: str
    timestamp: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class CostSummary:
    """Summary of cost tracking for an agent session."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cache_creation_tokens: int = 0
    estimated_cost_usd: float = 0.0
    actual_cost_usd: Optional[float] = None  # From ResultMessage.total_cost_usd
    step_count: int = 0
    budget_usd: Optional[float] = None
    budget_exceeded: bool = False
    budget_remaining_usd: Optional[float] = None
    
    # Context health tracking (Phase 1: "No Vibes" integration)
    context_health: Optional[ContextHealth] = None
    max_tokens: Optional[int] = None
    utilization_pct: Optional[float] = None


class CostTracker:
    """
    Track costs and context health for an agent session.
    
    SDK Best Practices Applied (per TrackingCostAndUsage.md):
    - Use Message IDs for Deduplication
    - Monitor the Result Message for authoritative total
    - Track partial usage even if conversation fails
    - Implement budget enforcement
    
    Context Engineering (per "No Vibes Allowed"):
    - Track token utilization vs. max context window
    - Prevent "Dumb Zone" entry (>85% capacity)
    - Enforce Plan requirement in CRITICAL state
    
    Example:
        >>> tracker = CostTracker(
        ...     budget_usd=5.0,
        ...     model="claude-sonnet-4-20250514",
        ...     max_tokens=200000
        ... )
        >>> # In message loop:
        >>> tracker.process_message(message)
        >>> 
        >>> # Check budget
        >>> if tracker.is_budget_exceeded():
        ...     raise BudgetExceededError(tracker.get_summary())
        >>> 
        >>> # Check context health (Gap 3: TDD Loop requirement)
        >>> health = tracker.check_context_health()
        >>> if health == ContextHealth.CRITICAL:
        ...     tracker.enforce_plan_requirement(has_plan=True)
    """
    
    def __init__(
        self,
        budget_usd: Optional[float] = None,
        model: str = "default",
        session_id: Optional[str] = None,
        max_tokens: int = 200000,
    ):
        """
        Initialize cost tracker.
        
        Args:
            budget_usd: Optional budget limit in USD
            model: Model name for pricing lookup
            session_id: Session ID for logging
            max_tokens: Maximum context window size (for health tracking)
        """
        self.budget_usd = budget_usd
        self.model = model
        self.session_id = session_id
        self.max_tokens = max_tokens
        
        # Get pricing for this model
        self._pricing = PRICING.get(model, PRICING["default"])
        
        # Track processed message IDs (SDK: same ID = same usage)
        self._processed_ids: Set[str] = set()
        
        # Step-by-step usage
        self._step_usages: List[StepUsage] = []
        
        # Running totals
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cache_read_tokens = 0
        self._total_cache_creation_tokens = 0
        self._estimated_cost_usd = 0.0
        
        # Authoritative cost from ResultMessage
        self._actual_cost_usd: Optional[float] = None
        
        # Context health tracking (Phase 1: "No Vibes" integration)
        self._has_plan = False
        self._compaction_count = 0
        self._health_history: List[ContextHealth] = []
    
    def process_message(self, message: Any) -> Optional[StepUsage]:
        """
        Process a message and track its usage.
        
        SDK Best Practice: Only process assistant messages with usage,
        deduplicate by message ID.
        
        Args:
            message: Message from agent stream
            
        Returns:
            StepUsage if new usage was tracked, None if skipped
        """
        # Check for ResultMessage with final cost
        # ResultMessage contains both total_cost_usd AND usage with tokens
        if hasattr(message, 'total_cost_usd') and message.total_cost_usd is not None:
            self._actual_cost_usd = message.total_cost_usd
            
            # Also extract usage tokens from ResultMessage if available
            # This ensures we capture the actual token counts from the final message
            if hasattr(message, 'usage') and message.usage is not None:
                usage = message.usage
                if isinstance(usage, dict):
                    input_tokens = usage.get('input_tokens', 0)
                    output_tokens = usage.get('output_tokens', 0)
                    cache_read = usage.get('cache_read_input_tokens', 0)
                    cache_create = usage.get('cache_creation_input_tokens', 0)
                else:
                    # Handle object with attributes
                    input_tokens = getattr(usage, 'input_tokens', 0)
                    output_tokens = getattr(usage, 'output_tokens', 0)
                    cache_read = getattr(usage, 'cache_read_input_tokens', 0)
                    cache_create = getattr(usage, 'cache_creation_input_tokens', 0)
                
                # Update totals with ResultMessage usage (authoritative)
                # This ensures we have the correct token counts even if intermediate messages were missed
                self._total_input_tokens = input_tokens
                self._total_output_tokens = output_tokens
                self._total_cache_read_tokens = cache_read
                self._total_cache_creation_tokens = cache_create
                
                # Recalculate estimated cost based on actual tokens
                self._estimated_cost_usd = self._calculate_cost(
                    input_tokens, output_tokens, cache_read, cache_create
                )
            
            return None
        
        # Only process assistant messages with usage
        if not hasattr(message, 'usage') or message.usage is None:
            return None
        
        # Get message ID for deduplication
        message_id = getattr(message, 'id', None)
        if not message_id:
            return None
        
        # SDK: Same ID = same usage, skip if already processed
        if message_id in self._processed_ids:
            return None
        
        self._processed_ids.add(message_id)
        
        # Extract usage data
        usage = message.usage
        if isinstance(usage, dict):
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            cache_read = usage.get('cache_read_input_tokens', 0)
            cache_create = usage.get('cache_creation_input_tokens', 0)
        else:
            # Handle object with attributes
            input_tokens = getattr(usage, 'input_tokens', 0)
            output_tokens = getattr(usage, 'output_tokens', 0)
            cache_read = getattr(usage, 'cache_read_input_tokens', 0)
            cache_create = getattr(usage, 'cache_creation_input_tokens', 0)
        
        # Calculate estimated cost for this step
        step_cost = self._calculate_cost(input_tokens, output_tokens, cache_read, cache_create)
        
        # Create step usage record
        step = StepUsage(
            message_id=message_id,
            timestamp=datetime.utcnow().isoformat(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read,
            cache_creation_input_tokens=cache_create,
            estimated_cost_usd=step_cost,
        )
        self._step_usages.append(step)
        
        # Update running totals
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_cache_read_tokens += cache_read
        self._total_cache_creation_tokens += cache_create
        self._estimated_cost_usd += step_cost
        
        return step
    
    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_read: int,
        cache_create: int,
    ) -> float:
        """Calculate estimated cost for token usage."""
        return (
            (input_tokens / 1000) * self._pricing["input_per_1k"]
            + (output_tokens / 1000) * self._pricing["output_per_1k"]
            + (cache_read / 1000) * self._pricing["cache_read_per_1k"]
            + (cache_create / 1000) * self._pricing["cache_create_per_1k"]
        )
    
    def is_budget_exceeded(self) -> bool:
        """
        Check if current usage exceeds budget.
        
        Uses actual cost if available, otherwise estimated cost.
        """
        if self.budget_usd is None:
            return False
        
        current_cost = self._actual_cost_usd or self._estimated_cost_usd
        return current_cost >= self.budget_usd
    
    def get_current_cost(self) -> float:
        """Get current cost (actual if available, otherwise estimated)."""
        return self._actual_cost_usd or self._estimated_cost_usd
    
    def get_budget_remaining(self) -> Optional[float]:
        """Get remaining budget, or None if no budget set."""
        if self.budget_usd is None:
            return None
        return max(0, self.budget_usd - self.get_current_cost())
    
    def get_total_tokens(self) -> int:
        """Get total tokens (input + output + cache)."""
        return (
            self._total_input_tokens
            + self._total_output_tokens
            + self._total_cache_read_tokens
            + self._total_cache_creation_tokens
        )
    
    def get_token_utilization(self) -> float:
        """
        Get context window utilization as a percentage (0.0 to 1.0).
        
        Returns:
            Utilization ratio (e.g., 0.85 = 85% full)
        """
        if self.max_tokens == 0:
            return 0.0
        return self.get_total_tokens() / self.max_tokens
    
    def check_context_health(self) -> ContextHealth:
        """
        Check the health of the context window.
        
        Based on "No Vibes Allowed" - prevents entry into the "Dumb Zone"
        where the context is saturated with noise.
        
        Thresholds:
        - HEALTHY: < 70% (normal operation)
        - WARNING: 70-85% (consider compaction)
        - CRITICAL: 85-95% (require Plan before code generation)
        - SATURATED: > 95% (force compaction)
        
        Returns:
            Current ContextHealth status
        """
        utilization = self.get_token_utilization()
        
        if utilization >= 0.95:
            health = ContextHealth.SATURATED
        elif utilization >= 0.85:
            health = ContextHealth.CRITICAL
        elif utilization >= 0.70:
            health = ContextHealth.WARNING
        else:
            health = ContextHealth.HEALTHY
        
        # Track history
        self._health_history.append(health)
        
        return health
    
    def enforce_plan_requirement(self, has_plan: bool = False) -> None:
        """
        Enforce the Plan requirement in CRITICAL/SATURATED states.
        
        This is the key constraint from "No Vibes Allowed" - the agent
        cannot proceed to implementation when in the "Dumb Zone" without
        first creating a Plan artifact to organize its thoughts.
        
        Args:
            has_plan: Whether a Plan artifact exists
            
        Raises:
            ContextBudgetError: If in CRITICAL/SATURATED state without Plan
        """
        health = self.check_context_health()
        
        if health in (ContextHealth.CRITICAL, ContextHealth.SATURATED):
            if not has_plan and not self._has_plan:
                raise ContextBudgetError(
                    f"Context is {health.value} ({self.get_token_utilization():.1%} full). "
                    f"Cannot proceed to implementation without a Plan. "
                    f"Run planning phase first to compact research findings."
                )
    
    def set_has_plan(self, has_plan: bool = True) -> None:
        """
        Mark that a Plan artifact exists.
        
        This allows the agent to proceed to implementation even
        in CRITICAL state, as the Plan represents compacted context.
        
        Args:
            has_plan: Whether a Plan now exists
        """
        self._has_plan = has_plan
    
    def record_compaction(self, tokens_saved: int) -> None:
        """
        Record that a context compaction occurred.
        
        Compaction is the transition from messy research to clean plan.
        This reduces token count and improves signal-to-noise ratio.
        
        Args:
            tokens_saved: Number of tokens freed by compaction
        """
        self._compaction_count += 1
        
        # Reduce total tokens (simulating context cleanup)
        # In practice, this would be handled by the RPI workflow
        # creating a new context with just the Plan
        self._total_input_tokens = max(0, self._total_input_tokens - tokens_saved)
        self._total_cache_read_tokens = max(0, self._total_cache_read_tokens - tokens_saved // 2)
    
    def should_compact(self) -> bool:
        """
        Check if context compaction is recommended.
        
        Returns:
            True if in CRITICAL or SATURATED state
        """
        health = self.check_context_health()
        return health in (ContextHealth.CRITICAL, ContextHealth.SATURATED)
    
    def get_summary(self) -> CostSummary:
        """Get complete cost summary with context health."""
        health = self.check_context_health()
        utilization = self.get_token_utilization()
        
        return CostSummary(
            total_input_tokens=self._total_input_tokens,
            total_output_tokens=self._total_output_tokens,
            total_cache_read_tokens=self._total_cache_read_tokens,
            total_cache_creation_tokens=self._total_cache_creation_tokens,
            estimated_cost_usd=self._estimated_cost_usd,
            actual_cost_usd=self._actual_cost_usd,
            step_count=len(self._step_usages),
            budget_usd=self.budget_usd,
            budget_exceeded=self.is_budget_exceeded(),
            budget_remaining_usd=self.get_budget_remaining(),
            # Context health fields
            context_health=health,
            max_tokens=self.max_tokens,
            utilization_pct=utilization,
        )
    
    def get_step_usages(self) -> List[StepUsage]:
        """Get all step-level usage records."""
        return self._step_usages.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        summary = self.get_summary()
        return {
            "session_id": self.session_id,
            "model": self.model,
            "total_input_tokens": summary.total_input_tokens,
            "total_output_tokens": summary.total_output_tokens,
            "total_cache_read_tokens": summary.total_cache_read_tokens,
            "total_cache_creation_tokens": summary.total_cache_creation_tokens,
            "estimated_cost_usd": summary.estimated_cost_usd,
            "actual_cost_usd": summary.actual_cost_usd,
            "step_count": summary.step_count,
            "budget_usd": summary.budget_usd,
            "budget_exceeded": summary.budget_exceeded,
            "budget_remaining_usd": summary.budget_remaining_usd,
        }


class BudgetExceededError(Exception):
    """Raised when agent exceeds its budget."""
    
    def __init__(self, summary: CostSummary, message: Optional[str] = None):
        self.summary = summary
        default_msg = (
            f"Budget exceeded: ${summary.actual_cost_usd or summary.estimated_cost_usd:.4f} "
            f"of ${summary.budget_usd:.4f} used"
        )
        super().__init__(message or default_msg)


class ContextBudgetError(Exception):
    """
    Raised when context budget is exceeded without required artifacts.
    
    This enforces the "No Vibes Allowed" constraint that agents cannot
    proceed to implementation in CRITICAL state without a Plan.
    """
    pass


__all__ = [
    "CostTracker",
    "CostSummary",
    "StepUsage",
    "ContextHealth",
    "BudgetExceededError",
    "ContextBudgetError",
    "PRICING",
]

