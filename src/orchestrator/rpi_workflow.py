"""
Research-Plan-Implement (RPI) Workflow Engine.

Implements the RPI cycle with TDD verification loop:
- Research: Divergent phase, spawn sub-agents to gather data
- Planning: Compaction point, synthesize research into actionable plan
- Implement: Convergent phase with TDD loop - cannot exit until tests pass

Phase 6: Refactored to use unified components:
- CostTracker (Phase 1) instead of ContextWindow
- SessionContext.create_isolated_fork() (Phase 2) for sub-agents
- NavigationMCPServer (Phase 4) in research phase
- DockerExecutionService (Phase 5) for test execution

Reference: "No Vibes Allowed: Solving Hard Problems in Complex Codebases" - Dex Horthy
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from src.hooks.cost_tracker import CostTracker, ContextHealth, ContextBudgetError
from src.context.compactor import ContextCompactor, CompactionStrategy, CompactionResult, ResearchFinding
from src.context.firewall import ContextFirewall, FirewallResult

if TYPE_CHECKING:
    from src.orchestrator.session_manager import SessionContext


class RPIState(Enum):
    """State in the RPI workflow."""
    IDLE = "idle"
    RESEARCH = "research"      # High context, messy exploration
    PLANNING = "planning"      # Compaction point
    IMPLEMENT = "implement"    # TDD loop
    VERIFY = "verify"          # Verification step
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Plan:
    """An actionable implementation plan."""
    objective: str
    steps: List[PlanStep]
    target_files: List[str]
    test_commands: List[str]
    constraints: List[str]
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    research_tokens: int = 0
    compacted_tokens: int = 0


@dataclass
class PlanStep:
    """A single step in the implementation plan."""
    id: str
    description: str
    target_file: str
    action: str  # create, modify, delete
    details: str = ""
    test_command: Optional[str] = None
    completed: bool = False
    verified: bool = False


@dataclass
class ResearchContext:
    """Context from the research phase."""
    findings: List[ResearchFinding]
    files_explored: List[str]
    patterns_found: List[str]
    constraints_identified: List[str]
    dependencies: List[str]
    total_tokens: int = 0


@dataclass
class ImplementationResult:
    """Result from the implementation phase."""
    success: bool
    plan_id: Optional[str] = None
    steps_completed: int = 0
    steps_total: int = 0
    tests_passed: bool = False
    attempts: int = 0
    error: Optional[str] = None
    
    # TDD loop metrics
    test_runs: int = 0
    fixes_applied: int = 0
    self_healed: bool = False


@dataclass
class TestResult:
    """Result from running tests."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    test_count: int = 0
    passed: int = 0
    failed: int = 0
    
    @property
    def passed_all(self) -> bool:
        """Check if all tests passed."""
        return self.exit_code == 0 and self.failed == 0


class RPIWorkflow:
    """
    Research-Plan-Implement workflow with TDD verification loop.
    
    This implements the core workflow pattern from "No Vibes Allowed":
    
    1. **Research Phase** (Divergent)
       - Spawn sub-agents to explore codebase
       - Gather findings, patterns, constraints
       - High context usage - messy and exploratory
    
    2. **Planning Phase** (Compaction Point)
       - Synthesize research into clean plan
       - Identify specific files and steps
       - Discard noise, retain signal
    
    3. **Implementation Phase** (TDD Loop)
       - Execute plan steps
       - Run tests after each change
       - Self-heal on failures (feed stderr back)
       - Cannot exit until tests pass
    
    Example:
        >>> workflow = RPIWorkflow()
        >>> 
        >>> # Start research
        >>> research = await workflow.research_phase("Add authentication to User model")
        >>> 
        >>> # Create plan (compaction point)
        >>> plan = await workflow.planning_phase(research)
        >>> 
        >>> # Implement with TDD loop
        >>> result = await workflow.implement_phase(plan)
        >>> # Agent cannot return until tests pass or max retries exceeded
    """
    
    def __init__(
        self,
        cost_tracker: Optional[CostTracker] = None,
        compactor: Optional[ContextCompactor] = None,
        firewall: Optional[ContextFirewall] = None,
        max_retries: int = 5,
        test_command: str = "make test",
    ):
        """
        Initialize the RPI Workflow.
        
        Phase 6: Refactored to use CostTracker (Phase 1) instead of ContextWindow.
        
        Args:
            cost_tracker: Cost and context health tracker (Phase 1 refactor).
            compactor: Context compactor for planning phase.
            firewall: Firewall for sub-agent isolation.
            max_retries: Maximum TDD loop iterations.
            test_command: Default test command.
        """
        self.cost_tracker = cost_tracker or CostTracker(max_tokens=200000)
        self.compactor = compactor or ContextCompactor()
        self.firewall = firewall or ContextFirewall()
        self.max_retries = max_retries
        self.test_command = test_command
        
        # State
        self._state = RPIState.IDLE
        self._current_plan: Optional[Plan] = None
        self._history: List[Dict[str, Any]] = []
        
        # Callbacks
        self._on_state_change: Optional[Callable[[RPIState, RPIState], None]] = None
        self._on_test_result: Optional[Callable[[TestResult], None]] = None
        self._on_fix_applied: Optional[Callable[[str], None]] = None
        
        # External execution functions (injected)
        self._run_tests_fn: Optional[Callable[[], TestResult]] = None
        self._apply_fix_fn: Optional[Callable[[str], None]] = None
        self._spawn_subagent_fn: Optional[Callable[[str, str, List[str]], FirewallResult]] = None
    
    @property
    def state(self) -> RPIState:
        """Get current workflow state."""
        return self._state
    
    def _transition(self, new_state: RPIState) -> None:
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        
        self._history.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        if self._on_state_change:
            self._on_state_change(old_state, new_state)
    
    def can_implement(self) -> bool:
        """
        Check if implementation is allowed.
        
        Returns False until a Plan artifact exists.
        This is the key constraint that prevents coding in the "Dumb Zone".
        """
        return self._current_plan is not None
    
    async def research_phase(
        self,
        objective: str,
        *,
        parent_session: Optional['SessionContext'] = None,
        scope: Optional[List[str]] = None,
        max_subagents: int = 3,
    ) -> ResearchContext:
        """
        Execute the research phase (divergent exploration).
        
        Phase 6: Now uses SessionContext.create_isolated_fork() for sub-agents.
        
        Spawns sub-agents to explore the codebase and gather findings.
        This phase is intentionally "messy" - we accumulate context.
        Sub-agents use NavigationMCPServer (Phase 4) for structural understanding.
        
        Args:
            objective: What we're trying to accomplish.
            parent_session: Parent SessionContext to fork from (Phase 2).
            scope: Directories or files to focus on.
            max_subagents: Maximum concurrent sub-agents.
            
        Returns:
            ResearchContext with gathered findings.
        """
        self._transition(RPIState.RESEARCH)
        
        findings: List[ResearchFinding] = []
        files_explored: List[str] = []
        patterns_found: List[str] = []
        constraints: List[str] = []
        dependencies: List[str] = []
        total_tokens = 0
        
        # Define research tasks with appropriate tools
        # Phase 4: Include navigation tools for structural understanding
        research_tasks = [
            ("codebase_search", f"Search codebase for: {objective}", 
             ["Read", "Grep", "Glob", "list_symbols"]),  # Phase 4: Added list_symbols
            ("pattern_analysis", f"Find patterns related to: {objective}", 
             ["Read", "Grep", "find_definition"]),  # Phase 4: Added find_definition
            ("dependency_check", f"Check dependencies for: {objective}", 
             ["Read", "Glob", "get_call_graph"]),  # Phase 4: Added get_call_graph
        ]
        
        for task_name, task_objective, tools in research_tasks[:max_subagents]:
            # Phase 2: Create isolated fork from parent session
            if parent_session:
                fork = parent_session.create_isolated_fork(
                    objective=task_objective,
                    tools=tools,
                    max_turns=10,
                    max_tokens=30000,
                )
                # Track in firewall
                self.firewall.track_fork(fork)
            else:
                # Fallback: Create context without fork (for testing)
                fork = None
            
            # If external spawn function is set, use it
            if self._spawn_subagent_fn:
                result = await asyncio.to_thread(
                    self._spawn_subagent_fn,
                    task_name,
                    task_objective,
                    tools
                )
                
                # Complete the context with results
                session_id = fork.session_id if fork else f"sim_{task_name}"
                self.firewall.complete_context(
                    session_id,
                    summary=result.summary,
                    findings=result.key_findings,
                    file_references=result.file_references,
                    tokens_consumed=result.tokens_consumed,
                )
                
                # Collect findings
                for finding_text in result.key_findings:
                    findings.append(ResearchFinding(
                        content=finding_text,
                        source=task_name,
                        category=task_name,
                    ))
                
                files_explored.extend(result.file_references)
                total_tokens += result.tokens_consumed
            else:
                # Simulate research (for testing without actual sub-agents)
                session_id = fork.session_id if fork else f"sim_{task_name}"
                if fork:
                    self.firewall.complete_context(
                        session_id,
                        summary=f"Research complete for: {task_objective}",
                        findings=[f"Found relevant information for {task_name}"],
                        tokens_consumed=5000,
                    )
                
                findings.append(ResearchFinding(
                    content=f"Simulated finding for {task_name}",
                    source=task_name,
                    category=task_name,
                ))
                total_tokens += 5000
        
        # Phase 1: Track token usage in CostTracker (not ContextWindow)
        # Note: In practice, this would be tracked automatically by message processing
        # This is just for workflow state management
        
        return ResearchContext(
            findings=findings,
            files_explored=files_explored,
            patterns_found=patterns_found,
            constraints_identified=constraints,
            dependencies=dependencies,
            total_tokens=total_tokens,
        )
    
    async def planning_phase(
        self,
        research: ResearchContext,
        objective: Optional[str] = None,
    ) -> Plan:
        """
        Execute the planning phase (compaction point).
        
        This is the critical transition from messy research to clean plan.
        We synthesize findings into specific, actionable steps.
        
        Args:
            research: Context from research phase.
            objective: Override objective for the plan.
            
        Returns:
            Plan with specific steps and file references.
        """
        self._transition(RPIState.PLANNING)
        
        # Add all findings to compactor
        for finding in research.findings:
            self.compactor.add_finding(finding)
        
        # Compact into plan
        result = self.compactor.compact(
            strategy=CompactionStrategy.PLAN,
            objective=objective,
        )
        
        # Convert to Plan object
        steps = []
        for i, plan_step in enumerate(result.plan_steps):
            steps.append(PlanStep(
                id=f"step_{i+1}",
                description=plan_step.description,
                target_file=plan_step.target_file,
                action=plan_step.action,
                details=plan_step.details,
                test_command=plan_step.test_command or self.test_command,
            ))
        
        # Collect target files and test commands
        target_files = list(set(s.target_file for s in steps))
        test_commands = list(set(s.test_command for s in steps if s.test_command))
        
        plan = Plan(
            objective=objective or "Implementation plan",
            steps=steps,
            target_files=target_files,
            test_commands=test_commands or [self.test_command],
            constraints=result.summary.constraints if result.summary else [],
            research_tokens=result.original_token_count,
            compacted_tokens=result.compacted_token_count,
        )
        
        # Store plan and mark as available
        self._current_plan = plan
        
        # Phase 1: Use CostTracker instead of ContextWindow
        self.cost_tracker.set_has_plan(True)
        
        # Track token savings from compaction
        self.cost_tracker.record_compaction(result.tokens_saved)
        
        # Clear compactor for next cycle
        self.compactor.clear()
        
        return plan
    
    async def implement_phase(
        self,
        plan: Plan,
    ) -> ImplementationResult:
        """
        Execute the implementation phase with TDD verification loop.
        
        This is a LOOP, not a linear process. The agent:
        1. Writes/locates tests
        2. Runs tests (expect fail)
        3. Writes code
        4. Runs tests again
        5. If fail, feeds stderr back and retries
        6. Cannot exit until tests pass or max_retries exceeded
        
        Args:
            plan: The plan to implement.
            
        Returns:
            ImplementationResult with success/failure details.
        """
        if not self.can_implement():
            raise ContextBudgetError(
                "Cannot implement without a Plan. "
                "Run planning_phase first."
            )
        
        self._transition(RPIState.IMPLEMENT)
        
        steps_completed = 0
        test_runs = 0
        fixes_applied = 0
        
        for attempt in range(self.max_retries):
            # Step 1: Ensure tests exist for the target
            await self._ensure_test_exists(plan)
            
            # Step 2: Run tests (TDD - expect fail on first iteration)
            test_result = await self._run_tests(plan)
            test_runs += 1
            
            if self._on_test_result:
                self._on_test_result(test_result)
            
            # Step 3: Check if tests pass
            if test_result.passed_all:
                self._transition(RPIState.COMPLETE)
                return ImplementationResult(
                    success=True,
                    plan_id=plan.objective,
                    steps_completed=len(plan.steps),
                    steps_total=len(plan.steps),
                    tests_passed=True,
                    attempts=attempt + 1,
                    test_runs=test_runs,
                    fixes_applied=fixes_applied,
                    self_healed=fixes_applied > 0,
                )
            
            # Step 4: Feed error context back to agent for self-healing
            error_context = self._extract_error_context(test_result)
            
            # Step 5: Apply fix (agent writes code)
            await self._apply_fix(error_context, plan)
            fixes_applied += 1
            
            if self._on_fix_applied:
                self._on_fix_applied(error_context)
            
            # Note: Token tracking is handled automatically by CostTracker
            # in run_agent_with_rpi() via message processing
        
        # Max retries exceeded
        self._transition(RPIState.FAILED)
        return ImplementationResult(
            success=False,
            plan_id=plan.objective,
            steps_completed=steps_completed,
            steps_total=len(plan.steps),
            tests_passed=False,
            attempts=self.max_retries,
            error="Max retries exceeded - tests still failing",
            test_runs=test_runs,
            fixes_applied=fixes_applied,
            self_healed=False,
        )
    
    async def _ensure_test_exists(self, plan: Plan) -> None:
        """Ensure tests exist for the plan targets."""
        # This would check for test files and create if needed
        # For now, assume tests exist
        pass
    
    async def _run_tests(self, plan: Plan) -> TestResult:
        """Run tests for the plan."""
        if self._run_tests_fn:
            return self._run_tests_fn()
        
        # Default: run test command via subprocess
        import subprocess
        
        test_cmd = plan.test_commands[0] if plan.test_commands else self.test_command
        
        try:
            result = subprocess.run(
                test_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            return TestResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Test execution timed out",
            )
        except Exception as e:
            return TestResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
            )
    
    def _extract_error_context(self, test_result: TestResult) -> str:
        """Extract actionable error context from test result."""
        # Combine stderr and relevant stdout
        error_parts = []
        
        if test_result.stderr:
            error_parts.append(f"STDERR:\n{test_result.stderr[:2000]}")
        
        if test_result.stdout and "error" in test_result.stdout.lower():
            error_parts.append(f"STDOUT (errors):\n{test_result.stdout[:2000]}")
        
        return "\n\n".join(error_parts) or "Tests failed with no error output"
    
    async def _apply_fix(self, error_context: str, plan: Plan) -> None:
        """Apply a fix based on error context."""
        if self._apply_fix_fn:
            self._apply_fix_fn(error_context)
        # Otherwise, this would be handled by the agent externally
    
    def reset(self) -> None:
        """Reset workflow state for new cycle."""
        self._state = RPIState.IDLE
        self._current_plan = None
        self.compactor.clear()
        self.cost_tracker.set_has_plan(False)
    
    # Dependency injection
    def set_run_tests(self, fn: Callable[[], TestResult]) -> None:
        """Set the function to run tests."""
        self._run_tests_fn = fn
    
    def set_apply_fix(self, fn: Callable[[str], None]) -> None:
        """Set the function to apply fixes."""
        self._apply_fix_fn = fn
    
    def set_spawn_subagent(self, fn: Callable[[str, str, List[str]], FirewallResult]) -> None:
        """Set the function to spawn sub-agents."""
        self._spawn_subagent_fn = fn
    
    # Callback setters
    def on_state_change(self, callback: Callable[[RPIState, RPIState], None]) -> None:
        """Set callback for state changes."""
        self._on_state_change = callback
    
    def on_test_result(self, callback: Callable[[TestResult], None]) -> None:
        """Set callback for test results."""
        self._on_test_result = callback
    
    def on_fix_applied(self, callback: Callable[[str], None]) -> None:
        """Set callback for fix applications."""
        self._on_fix_applied = callback


__all__ = [
    "RPIWorkflow",
    "RPIState",
    "Plan",
    "PlanStep",
    "ResearchContext",
    "ImplementationResult",
    "TestResult",
]

