"""
Base Sub-Agent Class.

Provides the foundation for specialized sub-agents with:
- Context isolation (firewall pattern)
- Model routing (Haiku for fast, Sonnet for complex)
- Automatic termination (kill switch)
- Result distillation (only summaries return to parent)

Reference: HumanLayer codebase-analyzer and codebase-locator agents
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SubAgentModel(Enum):
    """Model options for sub-agents."""
    HAIKU = "haiku"      # Fast, cheap - for exploration
    SONNET = "sonnet"    # Capable - for analysis
    OPUS = "opus"        # Most capable - for complex reasoning


@dataclass
class SubAgentConfig:
    """Configuration for a sub-agent."""
    name: str
    model: SubAgentModel
    tools: List[str]
    system_prompt: str
    max_turns: int = 20
    max_tokens: int = 30000
    timeout_seconds: int = 300
    
    # Behavior
    read_only: bool = False  # If True, cannot modify files
    terminate_on_complete: bool = True  # Kill switch


@dataclass
class SubAgentResult:
    """Result from a sub-agent execution."""
    success: bool
    summary: str
    findings: List[str] = field(default_factory=list)
    file_references: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)
    
    # Metrics
    tokens_consumed: int = 0
    turns_used: int = 0
    execution_time_ms: float = 0.0
    
    # Error info
    error: Optional[str] = None
    
    def to_context_string(self) -> str:
        """Convert to a string for parent context injection."""
        parts = [f"## Sub-Agent Result\n{self.summary}"]
        
        if self.findings:
            parts.append("\n### Findings:")
            for finding in self.findings:
                parts.append(f"- {finding}")
        
        if self.file_references:
            parts.append("\n### References:")
            for ref in self.file_references:
                parts.append(f"- `{ref}`")
        
        return "\n".join(parts)


class BaseSubAgent(ABC):
    """
    Base class for all sub-agents.
    
    Sub-agents are specialized AI assistants that:
    1. Operate in isolated context (context firewall)
    2. Use specific tools for their task
    3. Return only distilled summaries to parent
    4. Terminate after completing their task (kill switch)
    
    This implements the "Thin Client, Fat Backend" pattern where
    the main agent stays focused while sub-agents handle heavy lifting.
    """
    
    def __init__(self, config: SubAgentConfig):
        """
        Initialize the sub-agent.
        
        Args:
            config: Configuration for this sub-agent.
        """
        self.config = config
        self._is_active = False
        self._start_time: Optional[datetime] = None
        self._turns_used = 0
        self._tokens_consumed = 0
    
    @property
    def name(self) -> str:
        """Get the sub-agent name."""
        return self.config.name
    
    @property
    def model(self) -> SubAgentModel:
        """Get the model used by this sub-agent."""
        return self.config.model
    
    @property
    def is_active(self) -> bool:
        """Check if the sub-agent is currently running."""
        return self._is_active
    
    @abstractmethod
    async def execute(self, objective: str, context: Optional[Dict[str, Any]] = None) -> SubAgentResult:
        """
        Execute the sub-agent task.
        
        This method must be implemented by each sub-agent type.
        
        Args:
            objective: What the sub-agent should accomplish.
            context: Optional additional context.
            
        Returns:
            SubAgentResult with distilled findings.
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this sub-agent.
        
        Each sub-agent type has a specialized prompt that guides
        its behavior and output format.
        """
        pass
    
    async def _start(self) -> None:
        """Start the sub-agent execution."""
        self._is_active = True
        self._start_time = datetime.utcnow()
        self._turns_used = 0
        self._tokens_consumed = 0
    
    async def _stop(self) -> None:
        """
        Stop the sub-agent execution (kill switch).
        
        This ensures the sub-agent terminates and doesn't
        maintain persistent history that could pollute context.
        """
        self._is_active = False
    
    def _track_turn(self, tokens: int = 0) -> None:
        """Track a turn and token usage."""
        self._turns_used += 1
        self._tokens_consumed += tokens
    
    def _get_execution_time_ms(self) -> float:
        """Get execution time in milliseconds."""
        if not self._start_time:
            return 0.0
        return (datetime.utcnow() - self._start_time).total_seconds() * 1000


# Common prompts for sub-agents
EXPLORER_PROMPT = """
You are an Explorer agent - a fast, read-only specialist for codebase search.

## Core Rules
1. ONLY read and search - DO NOT modify any files
2. Be fast and focused - don't over-analyze
3. Return concrete file:line references
4. Summarize findings concisely

## Available Tools
- Read: Read file contents
- Grep: Search for patterns
- Glob: Find files by pattern
- list_symbols: Get symbols in a file

## Output Format
Return a concise summary with:
- Key locations found (file:line)
- Brief description of what's there
- Relevance to the objective
"""

RESEARCHER_PROMPT = """
You are a Researcher agent - a deep analysis specialist.

## Core Rules
1. Analyze implementation details thoroughly
2. Trace data flow and connections
3. Return file:line references for ALL claims
4. Focus on HOW code works, not suggesting changes

## Available Tools
- Read, Grep, Glob (standard tools)
- find_definition: Jump to symbol definition
- find_references: Find all usages
- get_call_graph: Map function dependencies

## Output Format
Return a detailed analysis with:
- Implementation explanation
- Data flow documentation
- Key patterns and connections
- Specific file:line references
"""

PLANNER_PROMPT = """
You are a Planner agent - a research specialist for plan mode.

## Core Rules
1. Gather context needed for planning
2. Identify constraints and dependencies
3. Map the affected files and components
4. DO NOT suggest implementations yet

## Available Tools
- Read, Grep, Glob
- get_call_graph: Map dependencies

## Output Format
Return planning context with:
- Files that will need changes
- Constraints discovered
- Dependencies to consider
- Patterns to follow
"""

CODE_REVIEWER_PROMPT = """
You are a Code Reviewer agent - a code review specialist.

## Core Rules
1. Review code for quality and correctness
2. Check for security issues
3. Verify patterns and conventions
4. Provide specific, actionable feedback

## Output Format
Return review findings organized by:
- Critical issues (must fix)
- Warnings (should fix)
- Suggestions (consider improving)
"""

TEST_RUNNER_PROMPT = """
You are a Test Runner agent - a test execution specialist.

## Core Rules
1. Run tests and capture results
2. Analyze failures and identify root causes
3. Return actionable error context
4. Be fast - use Haiku model

## Output Format
Return test results with:
- Pass/fail status
- Failure details with stack traces
- Root cause analysis
- Suggested fixes
"""


__all__ = [
    "BaseSubAgent",
    "SubAgentConfig",
    "SubAgentModel",
    "SubAgentResult",
    "EXPLORER_PROMPT",
    "RESEARCHER_PROMPT",
    "PLANNER_PROMPT",
    "CODE_REVIEWER_PROMPT",
    "TEST_RUNNER_PROMPT",
]

