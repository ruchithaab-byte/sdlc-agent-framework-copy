"""
Shared Agent Runner for SDLC Agents.

Provides common execution logic for running agents, handling:
- Session ID capture and management
- Message streaming
- Result aggregation
- Structured output validation (Phase 2)
- Cost tracking with budget enforcement (Phase 3)
- Error handling
- Project context injection for prompt rendering

SDK Best Practices Applied (per python-sdk.md, StructuredOutputs.md, TrackingCostAndUsage.md):
- Use async context manager for ClaudeSDKClient
- Capture session_id from init message for resumption
- Don't use break in message iteration (causes asyncio cleanup issues)
- Let iteration complete naturally
- Validate structured_output with Pydantic model_validate()
- Deduplicate cost tracking by message ID
- Use total_cost_usd from ResultMessage as authoritative
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from pydantic import BaseModel

from claude_agent_sdk import ClaudeSDKClient, create_sdk_mcp_server, tool

from config.agent_profiles import get_agent_profile
from src.agents.options_builder import build_agent_options
from src.hooks import CostTracker, CostSummary, ContextBudgetError, clear_active_tracker, set_project_path
from src.logging.execution_logger import ExecutionLogger
from src.schemas import SCHEMA_REGISTRY, validate_output
from src.utils.prompt_renderer import load_and_render_prompt, get_default_context
from src.config.project_config import ProjectConfig, load_project_config
from src.tracing import trace_run, RunType


@dataclass
class AgentResult:
    """
    Result from an agent execution.
    
    Contains the session ID for resumption, structured output (if schema defined),
    cost information, and optionally collected messages.
    
    Attributes:
        session_id: Session ID for resumption via `resume` parameter
        structured_output: Validated Pydantic model (if agent has output_schema)
        raw_output: Raw structured output dict before validation
        cost_usd: Total cost in USD (actual if available, else estimated)
        cost_summary: Full cost breakdown with tokens and budget info
        messages: All messages if collect_messages=True
        error: Error message if execution failed
        budget_exceeded: True if agent exceeded its budget
    """
    
    session_id: Optional[str] = None
    
    # Phase 2: Structured output (validated Pydantic model)
    structured_output: Optional[BaseModel] = None
    raw_output: Optional[Dict[str, Any]] = None
    
    # Phase 3: Cost tracking
    cost_usd: float = 0.0
    cost_summary: Optional[CostSummary] = None
    budget_exceeded: bool = False
    
    # Collected messages (if requested)
    messages: List[Any] = field(default_factory=list)
    
    # Error info
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """
        Check if execution was successful.
        
        Returns True if no error occurred.
        For RPI workflow, also checks if structured_output indicates success.
        """
        if self.error:
            return False
        
        # For RPI workflow results, check structured_output
        if self.structured_output and hasattr(self.structured_output, 'success'):
            return self.structured_output.success
        
        return True


def get_project_context(target_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get project context for prompt template rendering.
    
    Args:
        target_dir: Optional path to target project directory
        
    Returns:
        Dictionary with project context suitable for Jinja2 rendering
    """
    if target_dir:
        config = load_project_config(target_dir)
        if config:
            return config.to_context_dict()
    
    # Return default context if no project config found
    return get_default_context()


def render_agent_prompt(
    agent_id: str,
    target_dir: Optional[Path] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Render the prompt template for an agent with project context.
    
    Args:
        agent_id: Agent identifier (productspec, archguard, codecraft, etc.)
        target_dir: Optional path to target project directory
        extra_context: Additional context to merge with project context
        
    Returns:
        Rendered prompt string
        
    Raises:
        TemplateNotFound: If no prompt template found for the agent
    """
    context = get_project_context(target_dir)
    
    if extra_context:
        context.update(extra_context)
    
    return load_and_render_prompt(agent_id, context, target_dir)


@trace_run(name="Agent Execution", run_type=RunType.CHAIN)
async def run_agent(
    agent_id: str,
    prompt: str,
    *,
    target_dir: Optional[Path] = None,
    resume: Optional[str] = None,
    permission_mode_override: Optional[str] = None,
    on_message: Optional[Callable[[Any], None]] = None,
    collect_messages: bool = False,
    session_context: Optional[Any] = None,  # SessionContext from orchestrator
) -> AgentResult:
    """
    Run an agent with standard execution pattern.
    
    This is the common execution logic for all SDLC agents, handling:
    - Options building from AGENT_PROFILES
    - Session ID capture for resumption
    - Message streaming with optional callback
    - Cost tracking and budget enforcement
    - Structured output validation
    - Result aggregation
    
    Args:
        agent_id: Agent identifier from AGENT_PROFILES
        prompt: The prompt to send to the agent
        target_dir: Optional target project directory for logging context
        resume: Optional session ID to resume previous conversation
        permission_mode_override: Override permission mode from profile
        on_message: Optional callback for each message (default: print)
        collect_messages: If True, collect all messages in result.messages
        
    Returns:
        AgentResult with session_id, cost info, and optionally collected messages
        
    Example:
        >>> result = await run_agent(
        ...     "codecraft",
        ...     "Build the authentication module",
        ...     target_dir=Path("/path/to/project"),
        ...     on_message=lambda m: logger.info(m)
        ... )
        >>> print(f"Session ID: {result.session_id}")
        >>> print(f"Cost: ${result.cost_usd:.4f}")
        >>> if result.budget_exceeded:
        ...     print("Warning: Budget was exceeded!")
        
    SDK Best Practice:
        Don't use `break` in message iteration - let it complete naturally.
        The SDK handles cleanup properly when iteration completes.
    """
    # Set project path for execution logging
    if target_dir:
        set_project_path(str(target_dir))
    
    # CRITICAL FIX #1: Inject Context into Tools BEFORE Building Options
    # ------------------------------------------------------------
    # The SDK uses MCP servers, not direct tool instances. We need to:
    # 1. Inject context into the server instances that own the tools
    # 2. Create an SDK MCP server from session_context.tools
    # 3. Add it to the agent options so the SDK uses the context-injected tools
    
    # Extract context data from session (if provided)
    context_data = {}
    session_tools_mcp_server = None
    
    if session_context:
        # Extract context data from session
        repo_url = getattr(session_context, 'repo_url', None) or session_context.repo_config.github_url
        repo_owner = getattr(session_context, 'repo_owner', None)
        repo_name = getattr(session_context, 'repo_name', None) or session_context.repo_id
        current_branch = getattr(session_context, 'current_branch', None) or session_context.repo_config.branch or "main"
        linear_ticket_id = getattr(session_context, 'linear_ticket_id', None)
        
        context_data = {
            "repo_url": repo_url,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "current_branch": current_branch,
            "linear_ticket_id": linear_ticket_id,
        }
        
        # CRITICAL: Inject context into the server instances that own the tools
        # The tools in session_context.tools are bound methods (self.create_branch, etc.)
        # These methods reference 'self' (the server instance), so setting context on the
        # server instance ensures the tools use the injected context.
        if hasattr(session_context, 'github_server') and session_context.github_server:
            session_context.github_server.set_context({
                "repo_url": repo_url,
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "current_branch": current_branch,
            })
        
        if hasattr(session_context, 'linear_server') and session_context.linear_server:
            session_context.linear_server.set_context({
                "linear_ticket_id": linear_ticket_id,
            })
        
        # CRITICAL: Create SDK MCP server from session_context.tools
        # This ensures the SDK uses the context-injected tools, not separate instances
        # The tools are bound methods from server instances with context already injected
        if hasattr(session_context, 'tools') and session_context.tools:
            from typing import Any, Dict
            import inspect
            
            wrapped_tools = []
            for tool_func in session_context.tools:
                # Get tool metadata
                tool_name = tool_func.__name__
                tool_doc = tool_func.__doc__ or f"Tool: {tool_name}"
                
                # Extract parameter schema from function signature
                sig = inspect.signature(tool_func)
                param_schema = {}
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                    # Convert type hints to simple types for SDK
                    if param_type == Optional[str] or param_type == str:
                        param_schema[param_name] = str
                    elif param_type == Optional[int] or param_type == int:
                        param_schema[param_name] = int
                    else:
                        param_schema[param_name] = str  # Default to str
                
                # Create a wrapper function that preserves the bound method's context
                # CRITICAL FIX: Each wrapper must have a unique function name to avoid
                # "Tool names must be unique" API error
                # Use exec to create a function with the actual tool name as its Python name
                # This ensures the SDK sees unique names: create_branch, create_commit, etc.
                
                # Capture variables to avoid closure issues
                original_tool = tool_func
                tool_name_safe = tool_name.replace("-", "_").replace(".", "_")  # Sanitize for Python identifier
                tool_doc_final = tool_doc
                param_schema_final = param_schema
                
                # Create the wrapper function with the tool's actual name using exec
                # This ensures each function has a unique __name__ attribute
                wrapper_code = f"""
async def {tool_name_safe}(args: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"{tool_doc_final}\"\"\"
    # Call the original bound method with context already injected
    # The bound method will use self._context from the server instance
    # Filter out None values to match optional parameters
    filtered_args = {{k: v for k, v in args.items() if v is not None}}
    return await original_tool(**filtered_args)
"""
                
                # Execute in a namespace with required imports
                namespace = {
                    'Dict': Dict,
                    'Any': Any,
                    'original_tool': original_tool,
                }
                exec(wrapper_code, namespace)
                unique_wrapper = namespace[tool_name_safe]
                
                # Apply the @tool decorator with explicit name parameter
                # The decorator should use the 'name' parameter for the tool name
                decorated_tool = tool(tool_name, tool_doc_final, param_schema_final)(unique_wrapper)
                
                wrapped_tools.append(decorated_tool)
            
            # Create SDK MCP server from wrapped tools
            if wrapped_tools:
                try:
                    session_tools_mcp_server = create_sdk_mcp_server(
                        name="sdlc-tools",
                        version="1.0.0",
                        tools=wrapped_tools
                    )
                except Exception as e:
                    print(f"⚠️  Failed to create SDK MCP server from session tools: {e}")
                    print(f"   Tools will use context from server instances (bound methods)")
                    session_tools_mcp_server = None
    
    # Set CURRENT_AGENT_ID environment variable for hooks to access
    import os
    os.environ["CURRENT_AGENT_ID"] = agent_id
    
    # Build options with cost tracker
    # If we have session tools, we'll merge them with profile MCP servers
    options, cost_tracker = build_agent_options(
        agent_id,
        resume=resume,
        permission_mode_override=permission_mode_override,
        cwd_override=str(target_dir) if target_dir else None,
    )
    
    # CRITICAL: Merge session tools MCP server into options
    # This ensures the SDK uses our context-injected tools
    if session_tools_mcp_server and hasattr(options, 'mcp_servers') and session_context:
        if options.mcp_servers is None:
            options.mcp_servers = {}
        options.mcp_servers["sdlc-tools"] = session_tools_mcp_server
        
        # Add tool names to allowed_tools
        if hasattr(options, 'allowed_tools') and hasattr(session_context, 'tools') and session_context.tools:
            for tool_func in session_context.tools:
                tool_name = f"mcp__sdlc-tools__{tool_func.__name__}"
                if tool_name not in options.allowed_tools:
                    options.allowed_tools.append(tool_name)
    
    # Get profile to check if structured output is expected
    profile = get_agent_profile(agent_id)
    
    result = AgentResult()
    
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            
            async for message in client.receive_response():
                # Capture session ID from init or result message (SDK best practice)
                if hasattr(message, 'subtype') and message.subtype == 'init':
                    result.session_id = getattr(message, 'session_id', None)
                    # Update tracker session ID for hooks
                    if cost_tracker and result.session_id:
                        cost_tracker.session_id = result.session_id

                # Also capture from ResultMessage if not already set
                if hasattr(message, 'session_id') and not result.session_id:
                    result.session_id = getattr(message, 'session_id', None)
                    if cost_tracker and result.session_id:
                        cost_tracker.session_id = result.session_id
                
                # Phase 3: Track costs via CostTracker
                # SDK Best Practice: Deduplicate by message ID
                if cost_tracker:
                    cost_tracker.process_message(message)
                
                # Phase 2: Capture and validate structured output
                # SDK Best Practice: Check for structured_output in result message
                if hasattr(message, 'structured_output') and message.structured_output:
                    result.raw_output = message.structured_output
                    
                    # Validate with Pydantic if schema is defined
                    if profile.output_schema and profile.output_schema in SCHEMA_REGISTRY:
                        try:
                            result.structured_output = validate_output(
                                profile.output_schema,
                                message.structured_output
                            )
                        except Exception as e:
                            # Log validation error but don't fail - raw output still available
                            print(f"⚠️  Structured output validation failed: {e}")
                            result.error = f"Validation error: {e}"
                
                # Capture error from result message
                if hasattr(message, 'subtype') and message.subtype == 'error':
                    result.error = getattr(message, 'error', str(message))
                
                # Also check ResultMessage with is_error=True (even if subtype='success')
                if hasattr(message, 'subtype') and message.subtype == 'success':
                    if hasattr(message, 'is_error') and message.is_error:
                        # Extract error from result field
                        error_msg = getattr(message, 'result', str(message))
                        if 'API Error' in error_msg or 'error' in error_msg.lower():
                            result.error = error_msg
                
                # Invoke callback or default to print
                if on_message:
                    on_message(message)
                else:
                    print(message)
                
                # Optionally collect messages
                if collect_messages:
                    result.messages.append(message)
    finally:
        # Extract final cost summary
        if cost_tracker:
            summary = cost_tracker.get_summary()
            result.cost_usd = summary.actual_cost_usd or summary.estimated_cost_usd
            result.cost_summary = summary
            result.budget_exceeded = summary.budget_exceeded

            # Log agent performance to database
            # Always log if we have cost data, even for failed agents
            if result.session_id and (summary.step_count > 0 or result.cost_usd > 0):
                try:
                    logger = ExecutionLogger()
                    logger.log_agent_performance(
                        session_id=result.session_id,
                        agent_name=agent_id,
                        phase="execution",  # Could be more specific based on context
                        total_turns=summary.step_count,
                        total_tokens=summary.total_input_tokens + summary.total_output_tokens + summary.total_cache_read_tokens + summary.total_cache_creation_tokens,
                        total_cost_usd=result.cost_usd,
                        success=result.error is None,
                    )
                    print(f"💾 [Database] Logged agent performance: {agent_id} - ${result.cost_usd:.6f}")
                except Exception as e:
                    print(f"⚠️  [Database] Failed to log agent performance: {e}")
                    import traceback
                    traceback.print_exc()

            # Clean up tracker
            if result.session_id:
                clear_active_tracker(result.session_id)

    return result


async def run_agent_streaming(
    agent_id: str,
    prompt: str,
    *,
    target_dir: Optional[Path] = None,
    resume: Optional[str] = None,
    permission_mode_override: Optional[str] = None,
) -> AsyncIterator[Any]:
    """
    Run an agent and yield messages as they arrive.

    This is useful for agents like ProductSpec that need to stream
    responses back to callers. The session_id can be extracted from
    the init message in the stream.

    Note: Cost tracking is active via hooks. This function will automatically
    log agent performance to the database when streaming completes.

    Args:
        agent_id: Agent identifier from AGENT_PROFILES
        prompt: The prompt to send to the agent
        target_dir: Optional target project directory for logging context
        resume: Optional session ID to resume
        permission_mode_override: Override permission mode

    Yields:
        Messages from the agent as they arrive

    Example:
        >>> async for message in run_agent_streaming("productspec", requirements):
        ...     if hasattr(message, 'subtype') and message.subtype == 'init':
        ...         session_id = message.session_id
        ...     yield message
    """
    # Set project path for execution logging
    if target_dir:
        set_project_path(str(target_dir))
    
    # Set CURRENT_AGENT_ID environment variable for hooks to access
    import os
    os.environ["CURRENT_AGENT_ID"] = agent_id
    
    options, cost_tracker = build_agent_options(
        agent_id,
        resume=resume,
        permission_mode_override=permission_mode_override,
    )
    
    session_id = None
    
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            
            async for message in client.receive_response():
                # Track session ID for cleanup
                if hasattr(message, 'subtype') and message.subtype == 'init':
                    session_id = getattr(message, 'session_id', None)
                    if cost_tracker and session_id:
                        cost_tracker.session_id = session_id

                # Also capture from ResultMessage if not already set
                if hasattr(message, 'session_id') and not session_id:
                    session_id = getattr(message, 'session_id', None)
                    if cost_tracker and session_id:
                        cost_tracker.session_id = session_id
                
                # Track costs
                if cost_tracker:
                    cost_tracker.process_message(message)
                
                yield message
    finally:
        # Log agent performance to database
        if cost_tracker and session_id:
            try:
                summary = cost_tracker.get_summary()
                cost_usd = summary.actual_cost_usd or summary.estimated_cost_usd
                if summary.step_count > 0 or cost_usd > 0:
                    logger = ExecutionLogger()
                    logger.log_agent_performance(
                        session_id=session_id,
                        agent_name=agent_id,
                        phase="streaming",
                        total_turns=summary.step_count,
                        total_tokens=summary.total_input_tokens + summary.total_output_tokens + summary.total_cache_read_tokens + summary.total_cache_creation_tokens,
                        total_cost_usd=cost_usd,
                        success=True,  # Streaming completed without exceptions
                    )
                    print(f"💾 [Database] Logged streaming agent performance: {agent_id} - ${cost_usd:.6f}")
            except Exception as e:
                print(f"⚠️  [Database] Failed to log streaming agent performance: {e}")
                import traceback
                traceback.print_exc()

        # Clean up tracker
        if session_id:
            clear_active_tracker(session_id)


async def run_agent_with_continuation(
    agent_id: str,
    prompts: List[str],
    *,
    resume: Optional[str] = None,
    permission_mode_override: Optional[str] = None,
    on_message: Optional[Callable[[Any], None]] = None,
) -> AgentResult:
    """
    Run an agent with multiple sequential prompts in the same session.
    
    This is useful for multi-turn conversations where you want to
    send follow-up prompts based on previous responses.
    
    Cost tracking accumulates across all prompts in the session.
    
    Args:
        agent_id: Agent identifier from AGENT_PROFILES
        prompts: List of prompts to send sequentially
        resume: Optional session ID to resume
        permission_mode_override: Override permission mode
        on_message: Optional callback for each message
        
    Returns:
        AgentResult with final session_id and accumulated costs
        
    Example:
        >>> result = await run_agent_with_continuation(
        ...     "codecraft",
        ...     [
        ...         "Analyze the codebase structure",
        ...         "Now implement the authentication module",
        ...         "Add unit tests for the module",
        ...     ]
        ... )
        >>> print(f"Total cost: ${result.cost_usd:.4f}")
    """
    options, cost_tracker = build_agent_options(
        agent_id,
        resume=resume,
        permission_mode_override=permission_mode_override,
    )
    
    result = AgentResult()
    
    try:
        async with ClaudeSDKClient(options=options) as client:
            for prompt in prompts:
                await client.query(prompt)
                
                async for message in client.receive_response():
                    # Capture session ID
                    if hasattr(message, 'subtype') and message.subtype == 'init':
                        result.session_id = getattr(message, 'session_id', None)
                        if cost_tracker and result.session_id:
                            cost_tracker.session_id = result.session_id
                    
                    # Track costs
                    if cost_tracker:
                        cost_tracker.process_message(message)
                    
                    if on_message:
                        on_message(message)
                    else:
                        print(message)
    finally:
        # Extract final cost summary
        if cost_tracker:
            summary = cost_tracker.get_summary()
            result.cost_usd = summary.actual_cost_usd or summary.estimated_cost_usd
            result.cost_summary = summary
            result.budget_exceeded = summary.budget_exceeded
            
            # Clean up tracker
            if result.session_id:
                clear_active_tracker(result.session_id)
    
    return result


async def run_agent_with_rpi(
    agent_id: str,
    objective: str,
    *,
    target_dir: Optional[Path] = None,
    session_context: Optional[Any] = None,
    permission_mode_override: Optional[str] = None,
    on_message: Optional[Callable[[Any], None]] = None,
) -> AgentResult:
    """
    Run an agent with Research-Plan-Implement (RPI) workflow.
    
    Phase 6: Integrates the complete RPI cycle with all refactored components:
    - CostTracker (Phase 1) for context health
    - SessionContext.create_isolated_fork() (Phase 2) for sub-agents
    - ToolRegistry (Phase 3) for progressive disclosure
    - NavigationMCPServer (Phase 4) for structural understanding
    - DockerExecutionService (Phase 5) for batch operations
    
    The workflow:
    1. **Research Phase:** Spawn sub-agents to explore codebase (high context)
    2. **Planning Phase:** Compact research into clean plan (compaction point)
    3. **Implement Phase:** Execute plan with TDD loop (must pass tests)
    
    Args:
        agent_id: Agent identifier from AGENT_PROFILES
        objective: The high-level objective to accomplish
        target_dir: Optional target project directory
        session_context: Optional SessionContext from orchestrator
        permission_mode_override: Override permission mode
        on_message: Optional callback for each message
        
    Returns:
        AgentResult with session_id, cost info, and implementation status
        
    Example:
        >>> from src.orchestrator.session_manager import ContextOrchestrator
        >>> 
        >>> # Prepare session
        >>> orchestrator = ContextOrchestrator(registry)
        >>> session = orchestrator.prepare_session("Add auth to User model")
        >>> 
        >>> # Run with RPI workflow
        >>> result = await run_agent_with_rpi(
        ...     "codecraft",
        ...     "Add authentication to User model",
        ...     session_context=session
        ... )
        >>> 
        >>> # Check results
        >>> print(f"Tests passed: {result.tests_passed}")
        >>> print(f"Context health: {result.cost_summary.context_health}")
    """
    from src.orchestrator.rpi_workflow import RPIWorkflow, RPIState
    from src.hooks import CostTracker
    
    # Initialize components
    cost_tracker = CostTracker(
        budget_usd=10.0,  # Default budget, can be configured
        max_tokens=200000,  # Claude Sonnet 4 context window
        model="claude-sonnet-4-20250514",
    )
    
    # Initialize RPI workflow with refactored components
    workflow = RPIWorkflow(
        cost_tracker=cost_tracker,  # Phase 1: Use CostTracker
        max_retries=5,
        test_command="make test",
    )
    
    result = AgentResult()
    
    try:
        # RESEARCH Phase: Spawn sub-agents to gather context
        print(f"🔬 [RPI] Starting Research Phase for: {objective}")
        research = await workflow.research_phase(
            objective,
            parent_session=session_context,  # Phase 2: Fork from parent
            max_subagents=3,
        )
        print(f"✅ [RPI] Research complete: {len(research.findings)} findings, {research.total_tokens} tokens")
        
        # Check context health after research
        health = cost_tracker.check_context_health()
        print(f"📊 [RPI] Context health after research: {health.value}")
        
        # PLANNING Phase: Compact research into clean plan
        print(f"📋 [RPI] Starting Planning Phase (Compaction Point)")
        plan = await workflow.planning_phase(research, objective=objective)
        print(f"✅ [RPI] Plan created: {len(plan.steps)} steps")
        print(f"   Token compaction: {plan.research_tokens} → {plan.compacted_tokens} "
              f"({100 * (1 - plan.compacted_tokens/plan.research_tokens):.1f}% reduction)")
        
        # IMPLEMENT Phase: Execute plan with TDD loop
        print(f"🔨 [RPI] Starting Implementation Phase (TDD Loop)")
        impl_result = await workflow.implement_phase(plan)
        
        if impl_result.success:
            print(f"✅ [RPI] Implementation complete:")
            print(f"   Steps: {impl_result.steps_completed}/{impl_result.steps_total}")
            print(f"   Tests passed: {impl_result.tests_passed}")
            print(f"   Attempts: {impl_result.attempts}")
            print(f"   Self-healed: {impl_result.self_healed} "
                  f"({impl_result.fixes_applied} fixes applied)")
        else:
            print(f"❌ [RPI] Implementation failed:")
            print(f"   Reason: {impl_result.error}")
            print(f"   Attempts: {impl_result.attempts}")
            result.error = impl_result.error
        
        # Final context health check
        final_health = cost_tracker.check_context_health()
        final_summary = cost_tracker.get_summary()
        
        print(f"📊 [RPI] Final Summary:")
        print(f"   Context health: {final_health.value}")
        print(f"   Utilization: {final_summary.utilization_pct:.1%}")
        print(f"   Total tokens: {cost_tracker.get_total_tokens()}")
        print(f"   Estimated cost: ${final_summary.estimated_cost_usd:.4f}")
        
        # Populate result
        result.cost_summary = final_summary
        result.cost_usd = final_summary.estimated_cost_usd
        result.budget_exceeded = final_summary.budget_exceeded
        
        # Store implementation status in result
        result.structured_output = impl_result
        
    except ContextBudgetError as e:
        print(f"❌ [RPI] Context budget error: {e}")
        result.error = str(e)
    except Exception as e:
        print(f"❌ [RPI] Workflow error: {e}")
        result.error = str(e)
        import traceback
        traceback.print_exc()
    
    return result


__all__ = [
    "AgentResult",
    "run_agent",
    "run_agent_streaming",
    "run_agent_with_continuation",
    "run_agent_with_rpi",  # Phase 6: RPI workflow integration
    "get_project_context",
    "render_agent_prompt",
]
