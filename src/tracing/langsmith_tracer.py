"""
LangSmith Tracer Adapter for SDLC Agent Framework.

Implements a custom tracing layer that adheres strictly to the LangSmith OpenAPI schema
without relying on the unreliable SDK hooks. This provides full observability for agent
execution, tool usage, and SDLC workflow tracking.

Architecture:
- LangSmithTracer: Singleton class for raw HTTP communication with LangSmith API
- @trace_run: Decorator using contextvars for automatic trace hierarchy management
"""

from __future__ import annotations

import asyncio
import contextvars
import functools
import os
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from uuid import UUID, uuid4

import httpx

# Context variable for managing trace hierarchy
_parent_run_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "_parent_run_id", default=None
)

# Context variable for current run ID
_current_run_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "_current_run_id", default=None
)

F = TypeVar("F", bound=Callable[..., Any])


class RunType(str, Enum):
    """Run types matching LangSmith RunTypeEnum."""

    CHAIN = "chain"
    LLM = "llm"
    TOOL = "tool"
    RETRIEVER = "retriever"
    EMBEDDING = "embedding"
    PROMPT = "prompt"
    PARSER = "parser"


class LangSmithTracer:
    """
    Singleton adapter for LangSmith API communication.
    
    Manually constructs JSON payloads matching RunCreateSchemaExtended schema
    and handles all HTTP communication with the LangSmith API.
    
    Usage:
        tracer = LangSmithTracer.get_instance()
        run_id = await tracer.create_run(
            name="My Agent",
            run_type=RunType.CHAIN,
            inputs={"prompt": "Hello"},
        )
        await tracer.update_run(run_id, outputs={"result": "World"})
    """

    _instance: Optional[LangSmithTracer] = None
    _lock = False

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        project_name: Optional[str] = None,
    ):
        """
        Initialize the LangSmith tracer.
        
        Args:
            api_key: LangSmith API key. Defaults to LANGSMITH_API_KEY env var.
            api_url: LangSmith API URL. Defaults to https://api.smith.langchain.com
            project_name: Project name for traces. Defaults to LANGSMITH_PROJECT env var.
        """
        # Check if tracing is enabled first
        self._enabled = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
        
        self.api_key = api_key or os.getenv("LANGSMITH_API_KEY")
        # Support both LANGSMITH_ENDPOINT and LANGSMITH_API_URL env vars
        self.api_url = (api_url or 
                       os.getenv("LANGSMITH_ENDPOINT") or 
                       os.getenv("LANGSMITH_API_URL") or 
                       "https://api.smith.langchain.com").rstrip("/")
        # Support both LANGSMITH_PROJECT and LANGCHAIN_PROJECT env vars
        # Priority: explicit parameter > LANGSMITH_PROJECT > LANGCHAIN_PROJECT > default
        self.project_name = (project_name or 
                            os.getenv("LANGSMITH_PROJECT") or 
                            os.getenv("LANGCHAIN_PROJECT") or 
                            "sdlc-agents")
        
        # Only require API key if tracing is enabled
        if self._enabled and not self.api_key:
            raise ValueError(
                "LANGSMITH_API_KEY not found. Set the environment variable or pass api_key parameter. "
                "Alternatively, set LANGSMITH_TRACING=false to disable tracing."
            )
        
        # Initialize HTTP client only if tracing is enabled
        if self._enabled:
            # LangSmith uses x-api-key header (lowercase with hyphens)
            self.client = httpx.AsyncClient(
                base_url=self.api_url,
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        else:
            # Create a dummy client that won't be used
            self.client = None

    @classmethod
    def get_instance(
        cls,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> LangSmithTracer:
        """
        Get or create the singleton instance.
        
        Note: If instance already exists and you pass new parameters, they will be ignored
        unless you reset the singleton first. To use new env vars, set them before
        the first call to get_instance(), or explicitly pass parameters on first call.
        """
        if cls._instance is None:
            cls._instance = cls(api_key, api_url, project_name)
        elif api_key or api_url or project_name:
            # If instance exists but new params provided, update if they differ
            # This allows re-initialization if needed
            if project_name and cls._instance.project_name != project_name:
                cls._instance.project_name = project_name
            if api_key and cls._instance.api_key != api_key:
                cls._instance.api_key = api_key
            if api_url and cls._instance.api_url != api_url:
                cls._instance.api_url = api_url
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance. Useful for testing or re-initialization."""
        cls._instance = None
        cls._lock = False

    def _safe_serialize(self, obj: Any) -> Any:
        """
        Recursively converts objects to JSON-serializable types.
        
        Handles Pydantic models, Enums, complex objects, and nested structures.
        """
        # Primitive types
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        
        # Enums
        if isinstance(obj, Enum):
            return obj.value
        
        # Lists and tuples
        if isinstance(obj, (list, tuple)):
            return [self._safe_serialize(i) for i in obj]
        
        # Dictionaries - recursively serialize values
        if isinstance(obj, dict):
            return {str(k): self._safe_serialize(v) for k, v in obj.items()}
        
        # Pydantic models and objects with to_dict/dict methods
        if hasattr(obj, "model_dump"):
            # Pydantic v2
            return self._safe_serialize(obj.model_dump())
        elif hasattr(obj, "dict"):
            # Pydantic v1
            return self._safe_serialize(obj.dict())
        elif hasattr(obj, "to_dict") and callable(obj.to_dict):
            return self._safe_serialize(obj.to_dict())
        
        # Fallback: Convert complex objects to string representation
        try:
            return str(obj)
        except Exception:
            return repr(obj)
    
    def _serialize_io(self, data: Any) -> Dict[str, Any]:
        """
        Serialize inputs/outputs to dictionary format.
        
        Handles various types to satisfy the schema's anyOf requirements.
        Uses _safe_serialize to handle complex objects.
        """
        # First, safely serialize the data to JSON-compatible types
        serialized = self._safe_serialize(data)
        
        # Then wrap in appropriate format for LangSmith
        if isinstance(serialized, dict):
            return serialized
        elif isinstance(serialized, str):
            return {"content": serialized}
        elif isinstance(serialized, (list, tuple)):
            return {"items": list(serialized)}
        else:
            return {"value": serialized}

    def _format_timestamp(self, dt: Optional[datetime] = None) -> str:
        """Format datetime to ISO 8601 string."""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.isoformat()

    async def create_run(
        self,
        name: str,
        run_type: RunType,
        *,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        parent_run_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        error: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        session_name: Optional[str] = None,
    ) -> str:
        """
        Create a new run in LangSmith.
        
        Args:
            name: Name of the run
            run_type: Type of run (chain, llm, tool, etc.)
            inputs: Input data for the run
            outputs: Output data for the run
            parent_run_id: Parent run ID for hierarchy
            start_time: Start time (defaults to now)
            end_time: End time (if run is complete)
            error: Error message if run failed
            tags: Tags for filtering
            metadata: Additional metadata
            session_id: Session ID for grouping
            session_name: Session name
            
        Returns:
            Run ID (UUID string)
        """
        if not self._enabled:
            return str(uuid4())  # Return dummy ID if disabled
        
        run_id = str(uuid4())
        start_time_str = self._format_timestamp(start_time)
        
        # CRITICAL FIX #3: Ensure RunType enum is serialized to string value
        # Convert enum to string value if it's an Enum instance
        run_type_value = run_type.value if isinstance(run_type, Enum) else run_type
        
        # Build payload matching RunCreateSchemaExtended
        payload: Dict[str, Any] = {
            "id": run_id,
            "name": name,
            "run_type": run_type_value,  # Use string value, not enum object
            "start_time": start_time_str,
        }
        
        # Add optional fields
        if inputs is not None:
            payload["inputs"] = self._serialize_io(inputs)
        
        if outputs is not None:
            payload["outputs"] = self._serialize_io(outputs)
        
        if parent_run_id:
            payload["parent_run_id"] = parent_run_id
        
        if end_time:
            payload["end_time"] = self._format_timestamp(end_time)
        
        if error:
            payload["error"] = error
        
        if tags:
            payload["tags"] = tags
        
        if metadata:
            payload["extra"] = metadata
        
        if session_id:
            payload["session_id"] = session_id
        
        # CRITICAL FIX: Ensure project name is used as the session (project) name
        # In LangSmith API, 'session_name' = Project Name
        # This determines which project folder the run appears in
        payload["session_name"] = session_name or self.project_name
        
        # Add project name as tag if not already present (for filtering within project)
        if tags and self.project_name not in tags:
            payload.setdefault("tags", []).append(self.project_name)
        elif not tags:
            payload["tags"] = [self.project_name]
        
        try:
            response = await self.client.post("/runs", json=payload)
            response.raise_for_status()
            return run_id
        except httpx.HTTPError as e:
            # Log error but don't fail - tracing should be non-blocking
            print(f"⚠️  [LangSmith] Failed to create run: {e}")
            return run_id  # Return ID anyway for local tracking

    async def update_run(
        self,
        run_id: str,
        *,
        outputs: Optional[Dict[str, Any]] = None,
        end_time: Optional[datetime] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update an existing run.
        
        Args:
            run_id: Run ID to update
            outputs: Output data
            end_time: End time (defaults to now)
            error: Error message if run failed
            metadata: Additional metadata
        """
        if not self._enabled:
            return
        
        payload: Dict[str, Any] = {}
        
        if outputs is not None:
            payload["outputs"] = self._serialize_io(outputs)
        
        if end_time:
            payload["end_time"] = self._format_timestamp(end_time)
        elif outputs or error:
            # Auto-set end_time if completing the run
            payload["end_time"] = self._format_timestamp()
        
        if error:
            payload["error"] = error
        
        if metadata:
            payload["extra"] = metadata
        
        if not payload:
            return  # Nothing to update
        
        try:
            response = await self.client.patch(f"/runs/{run_id}", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as e:
            # Log error but don't fail
            print(f"⚠️  [LangSmith] Failed to update run {run_id}: {e}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def trace_run(
    name: Optional[str] = None,
    run_type: RunType = RunType.CHAIN,
    *,
    tags: Optional[list[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Callable[[F], F]:
    """
    Decorator for tracing function execution with automatic hierarchy management.
    
    Uses contextvars to manage trace hierarchy automatically:
    1. Checks for parent_run_id in context
    2. Creates new run linked to parent
    3. Updates context with new run_id
    4. Executes function
    5. Updates run with outputs/error
    6. Restores previous parent_run_id
    
    Args:
        name: Run name (defaults to function name)
        run_type: Type of run (chain, llm, tool)
        tags: Additional tags
        metadata: Additional metadata
        
    Example:
        @trace_run(name="Create Branch", run_type=RunType.TOOL)
        async def create_branch(branch_name: str):
            # Function implementation
            return {"branch": branch_name}
    """
    def decorator(func: F) -> F:
        # CRITICAL FIX: Use functools.wraps to preserve original function's __name__ and __doc__
        # Without this, all decorated functions appear as 'async_wrapper' to the SDK
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = LangSmithTracer.get_instance()
            
            # Get parent run ID from context
            parent_id = _parent_run_id.get(None)
            
            # Generate run name
            run_name = name or f"{func.__module__}.{func.__name__}"
            
            # Prepare inputs
            inputs = {
                "args": str(args) if args else None,
                "kwargs": {k: str(v) for k, v in kwargs.items()} if kwargs else None,
            }
            
            # CRITICAL FIX #3: Ensure RunType enum is serialized to string value
            # Convert enum to string value if it's an Enum instance
            run_type_value = run_type.value if isinstance(run_type, Enum) else run_type
            
            # Create run
            run_id = await tracer.create_run(
                name=run_name,
                run_type=run_type_value,  # Use string value, not enum object
                inputs=inputs,
                parent_run_id=parent_id,
                tags=tags,
                metadata=metadata,
            )
            
            # Update context
            previous_parent = _parent_run_id.get(None)
            previous_current = _current_run_id.get(None)
            _parent_run_id.set(run_id)
            _current_run_id.set(run_id)
            
            try:
                # Execute function
                if callable(func) and not asyncio.iscoroutinefunction(func):
                    result = func(*args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                
                # Serialize outputs - use _safe_serialize to handle complex objects
                if isinstance(result, dict):
                    # Already a dict, but may contain non-serializable objects
                    outputs = tracer._safe_serialize(result)
                else:
                    # Single value - wrap and serialize
                    outputs = {"result": tracer._safe_serialize(result)}
                
                # Update run with outputs
                await tracer.update_run(run_id, outputs=outputs)
                
                return result
                
            except Exception as e:
                # Update run with error
                error_msg = f"{type(e).__name__}: {str(e)}"
                await tracer.update_run(run_id, error=error_msg)
                raise
                
            finally:
                # Restore context
                if previous_parent is not None:
                    _parent_run_id.set(previous_parent)
                else:
                    _parent_run_id.set(None)
                
                if previous_current is not None:
                    _current_run_id.set(previous_current)
                else:
                    _current_run_id.set(None)
        
        # CRITICAL FIX: Also preserve function name for sync wrapper
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, we need to run in event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


# Convenience function for getting current run ID
def get_current_run_id() -> Optional[str]:
    """Get the current run ID from context."""
    return _current_run_id.get(None)


# Convenience function for setting parent run ID
def set_parent_run_id(run_id: Optional[str]) -> None:
    """Set the parent run ID in context."""
    _parent_run_id.set(run_id)

