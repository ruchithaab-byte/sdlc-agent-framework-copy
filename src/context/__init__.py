"""
Context Engineering Module.

Implements the Context Engineering discipline from Anthropic's best practices:
- ContextCompactor: Synthesizes research into clean plans (compaction point)
- ContextFirewall: Isolates sub-agent context from main agent

Phase 1: Context health tracking moved to src.hooks.CostTracker
Phase 2: IsolatedContext removed - now uses SessionContext from orchestrator

Reference: "The Cognitive Architecture of Agency" - Dex Horthy, HumanLayer
"""

from src.context.compactor import (
    ContextCompactor,
    CompactionResult,
    ResearchSummary,
)
from src.context.firewall import (
    ContextFirewall,
    FirewallResult,
)

# Re-export ContextHealth from hooks for backward compatibility
from src.hooks.cost_tracker import ContextHealth, ContextBudgetError

__all__ = [
    # Compactor
    "ContextCompactor",
    "CompactionResult",
    "ResearchSummary",
    # Firewall
    "ContextFirewall",
    "FirewallResult",
    # Re-exports from hooks
    "ContextHealth",
    "ContextBudgetError",
]

