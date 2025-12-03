"""
Batch Runner for efficient multi-operation execution.

Implements the Code Execution paradigm from Anthropic's best practices:
- Agent writes a loop in code instead of 100 individual tool calls
- ~98% token reduction for bulk operations
- Intermediate variables stay inside execution environment
- Only filtered results return to context

Reference: "Code execution with MCP: building more efficient AI agents"
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from src.execution.docker_service import (
    DockerExecutionService,
    Container,
    ExecutionResult,
    ContainerError,
)
from src.tracing import trace_run, RunType


@dataclass
class BatchResult:
    """Result from a batch operation."""
    success: bool
    results: List[Any]
    errors: List[str] = field(default_factory=list)
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    execution_time_ms: float = 0.0
    
    # Token savings estimate
    individual_calls_estimate: int = 0  # How many individual calls this would have been
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "results": self.results,
            "errors": self.errors,
            "total_items": self.total_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "execution_time_ms": self.execution_time_ms,
            "individual_calls_estimate": self.individual_calls_estimate,
        }


class BatchRunner:
    """
    Executes batch operations efficiently in containers.
    
    This is the key component that enables the shift from JSON-RPC to Code Execution:
    - 100 file operations → 1 script execution → 1 filtered result
    - ~98% token reduction for bulk operations
    - Logic stays in code, not in prompts
    
    Example:
        >>> runner = BatchRunner(docker_service)
        >>> 
        >>> # Instead of 100 individual read_file calls:
        >>> result = await runner.batch_process_files(
        ...     files=["file1.py", "file2.py", ...],
        ...     operation="count lines containing 'TODO'"
        ... )
        >>> # Returns aggregated result, not 100 individual responses
    """
    
    def __init__(
        self,
        docker_service: Optional[DockerExecutionService] = None,
    ):
        """
        Initialize the Batch Runner.
        
        Args:
            docker_service: Docker execution service. Creates one if not provided.
        """
        self._docker_service = docker_service or DockerExecutionService()
        self._active_container: Optional[Container] = None
    
    async def _ensure_container(self, profile: str = "python-executor") -> Container:
        """Ensure we have an active container for execution."""
        if self._active_container is None or not self._active_container.is_alive():
            self._active_container = await self._docker_service.spawn_container(profile)
        return self._active_container
    
    @trace_run(name="Batch: Process Files", run_type=RunType.TOOL)
    async def batch_process_files(
        self,
        files: List[str],
        operation: str,
        filter_fn: Optional[str] = None,
    ) -> BatchResult:
        """
        Process multiple files with a single script execution.
        
        Instead of N individual tool calls, executes one script that processes
        all files and returns aggregated results.
        
        Args:
            files: List of file paths to process.
            operation: Description of operation to perform.
            filter_fn: Optional Python filter function as string.
            
        Returns:
            BatchResult with aggregated results.
        """
        container = await self._ensure_container()
        
        # Generate batch processing script
        script = self._generate_file_processing_script(files, operation, filter_fn)
        
        start_time = datetime.utcnow()
        result = await self._docker_service.execute_script(container, script, "python")
        
        # Parse results
        if result.success:
            try:
                parsed = json.loads(result.stdout)
                return BatchResult(
                    success=True,
                    results=parsed.get("results", []),
                    errors=parsed.get("errors", []),
                    total_items=len(files),
                    successful_items=parsed.get("successful", 0),
                    failed_items=parsed.get("failed", 0),
                    execution_time_ms=result.execution_time_ms,
                    individual_calls_estimate=len(files),
                )
            except json.JSONDecodeError:
                return BatchResult(
                    success=True,
                    results=[result.stdout],
                    total_items=len(files),
                    successful_items=len(files),
                    execution_time_ms=result.execution_time_ms,
                    individual_calls_estimate=len(files),
                )
        else:
            return BatchResult(
                success=False,
                results=[],
                errors=[result.stderr],
                total_items=len(files),
                failed_items=len(files),
                execution_time_ms=result.execution_time_ms,
                individual_calls_estimate=len(files),
            )
    
    def _generate_file_processing_script(
        self,
        files: List[str],
        operation: str,
        filter_fn: Optional[str],
    ) -> str:
        """Generate Python script for batch file processing."""
        files_json = json.dumps(files)
        filter_code = filter_fn or "lambda x: True"
        
        return f'''
import json
import os
from pathlib import Path

files = {files_json}
filter_fn = {filter_code}

results = []
errors = []
successful = 0
failed = 0

for file_path in files:
    try:
        path = Path(file_path)
        if not path.exists():
            errors.append(f"File not found: {{file_path}}")
            failed += 1
            continue
        
        content = path.read_text()
        
        # Apply filter
        if filter_fn(content):
            # Operation: {operation}
            result = {{
                "file": file_path,
                "lines": len(content.splitlines()),
                "size": len(content),
            }}
            results.append(result)
            successful += 1
        else:
            successful += 1  # Filtered out, not an error
            
    except Exception as e:
        errors.append(f"Error processing {{file_path}}: {{str(e)}}")
        failed += 1

output = {{
    "results": results,
    "errors": errors,
    "successful": successful,
    "failed": failed,
}}

print(json.dumps(output))
'''
    
    @trace_run(name="Batch: Search Codebase", run_type=RunType.TOOL)
    async def batch_search(
        self,
        pattern: str,
        directories: List[str],
        file_types: Optional[List[str]] = None,
    ) -> BatchResult:
        """
        Search across multiple directories with a single execution.
        
        Args:
            pattern: Search pattern (regex or string).
            directories: List of directories to search.
            file_types: Optional list of file extensions to include.
            
        Returns:
            BatchResult with search matches.
        """
        container = await self._ensure_container()
        
        script = self._generate_search_script(pattern, directories, file_types)
        result = await self._docker_service.execute_script(container, script, "python")
        
        if result.success:
            try:
                parsed = json.loads(result.stdout)
                return BatchResult(
                    success=True,
                    results=parsed.get("matches", []),
                    total_items=parsed.get("files_searched", 0),
                    successful_items=len(parsed.get("matches", [])),
                    execution_time_ms=result.execution_time_ms,
                    individual_calls_estimate=parsed.get("files_searched", 0),
                )
            except json.JSONDecodeError:
                return BatchResult(
                    success=False,
                    results=[],
                    errors=["Failed to parse search results"],
                    execution_time_ms=result.execution_time_ms,
                )
        else:
            return BatchResult(
                success=False,
                results=[],
                errors=[result.stderr],
                execution_time_ms=result.execution_time_ms,
            )
    
    def _generate_search_script(
        self,
        pattern: str,
        directories: List[str],
        file_types: Optional[List[str]],
    ) -> str:
        """Generate Python script for batch search."""
        dirs_json = json.dumps(directories)
        types_json = json.dumps(file_types or [])
        
        return f'''
import json
import re
import os
from pathlib import Path

directories = {dirs_json}
file_types = {types_json}
pattern = re.compile(r"{pattern}")

matches = []
files_searched = 0

for directory in directories:
    dir_path = Path(directory)
    if not dir_path.exists():
        continue
    
    for file_path in dir_path.rglob("*"):
        if not file_path.is_file():
            continue
        
        # Filter by file type if specified
        if file_types and file_path.suffix not in file_types:
            continue
        
        files_searched += 1
        
        try:
            content = file_path.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    matches.append({{
                        "file": str(file_path),
                        "line": i,
                        "content": line.strip()[:200],  # Truncate long lines
                    }})
        except Exception:
            pass  # Skip binary files, etc.

output = {{
    "matches": matches,
    "files_searched": files_searched,
}}

print(json.dumps(output))
'''
    
    @trace_run(name="Batch: Execute Custom", run_type=RunType.TOOL)
    async def execute_custom(
        self,
        script: str,
        language: str = "python",
    ) -> ExecutionResult:
        """
        Execute a custom script for complex batch operations.
        
        For operations that don't fit the standard batch patterns,
        agents can write custom scripts.
        
        Args:
            script: The script to execute.
            language: Script language (python, node, bash).
            
        Returns:
            ExecutionResult from the execution.
        """
        container = await self._ensure_container()
        return await self._docker_service.execute_script(container, script, language)
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._active_container:
            await self._docker_service.destroy(self._active_container)
            self._active_container = None


__all__ = [
    "BatchRunner",
    "BatchResult",
]

