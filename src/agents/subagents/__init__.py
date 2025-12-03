"""
Sub-Agents Package.

Provides specialized sub-agents for isolated task execution:
- Explorer: Fast, read-only codebase search (Haiku)
- Researcher: Deep analysis with full tools (Sonnet)
- Planner: Research for plan mode (Sonnet)
- CodeReviewer: Code review specialist (Sonnet)
- TestRunner: Test execution and failure analysis (Haiku)

Reference: "No Vibes Allowed" - Thin Client, Fat Backend pattern
"""

from src.agents.subagents.explorer import ExplorerSubAgent
from src.agents.subagents.researcher import ResearcherSubAgent
from src.agents.subagents.planner import PlannerSubAgent
from src.agents.subagents.code_reviewer import CodeReviewerSubAgent
from src.agents.subagents.test_runner import TestRunnerSubAgent

__all__ = [
    "ExplorerSubAgent",
    "ResearcherSubAgent",
    "PlannerSubAgent",
    "CodeReviewerSubAgent",
    "TestRunnerSubAgent",
]

