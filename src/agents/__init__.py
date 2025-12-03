"""Agent exports for easy CLI usage.

This module exports:
- Individual agent run functions for direct invocation
- Centralized options builder for consistent SDK configuration
- Shared runner for common execution patterns
"""

# Agent run functions
from .archguard_agent import run_archguard_agent
from .codecraft_agent import run_codecraft_agent
from .docuscribe_agent import run_docuscribe_agent
from .finops_agent import run_finops_agent
from .infraops_agent import run_infraops_agent
from .productspec_agent import run_productspec_agent
from .qualityguard_agent import run_qualityguard_agent
from .sentinel_agent import run_sentinel_agent
from .sprintmaster_agent import run_sprintmaster_agent
from .sre_triage_agent import run_sre_triage_agent

# Centralized infrastructure (Phase 1)
from .options_builder import build_agent_options, build_agent_options_from_profile
from .runner import AgentResult, run_agent, run_agent_streaming, run_agent_with_continuation

__all__ = [
    # Agent functions
    "run_archguard_agent",
    "run_codecraft_agent",
    "run_docuscribe_agent",
    "run_finops_agent",
    "run_infraops_agent",
    "run_productspec_agent",
    "run_qualityguard_agent",
    "run_sentinel_agent",
    "run_sprintmaster_agent",
    "run_sre_triage_agent",
    # Centralized infrastructure
    "build_agent_options",
    "build_agent_options_from_profile",
    "AgentResult",
    "run_agent",
    "run_agent_streaming",
    "run_agent_with_continuation",
]
