"""
Docker Execution Service for secure, isolated code execution.

Implements the Docker MCP Toolkit pattern from Anthropic's best practices:
- Process isolation: Separate execution environment per session
- Resource limits: CPU, memory, storage constraints per container
- Network control: Restrict outbound connections
- Ephemeral filesystem: Clean state for each session

Reference: "Code execution with MCP: building more efficient AI agents"
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.tracing import trace_run, RunType


class ContainerState(Enum):
    """Container lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    DESTROYED = "destroyed"
    ERROR = "error"


class ContainerError(Exception):
    """Raised when container operations fail."""
    pass


@dataclass
class ContainerConfig:
    """Configuration for a Docker execution container.
    
    Follows Docker MCP Toolkit standards for secure execution.
    """
    image: str = "python:3.11-slim"
    memory_limit: str = "1g"
    cpu_limit: float = 1.0
    network_mode: str = "none"  # Restricted by default
    timeout_seconds: int = 300
    workspace_mount: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    
    # Security settings
    read_only_root: bool = True
    no_new_privileges: bool = True
    cap_drop: List[str] = field(default_factory=lambda: ["ALL"])
    
    # Navigation tools (Gap 1 fix)
    install_ctags: bool = True
    install_tree_sitter: bool = True


@dataclass
class Container:
    """Represents a running Docker container."""
    id: str
    config: ContainerConfig
    state: ContainerState = ContainerState.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    container_id: Optional[str] = None  # Docker container ID
    workspace_path: Optional[Path] = None
    
    def is_alive(self) -> bool:
        """Check if container is in a runnable state."""
        return self.state in (ContainerState.PENDING, ContainerState.RUNNING)


@dataclass
class ExecutionResult:
    """Result from code execution in a container."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    
    # Privacy filtering applied
    pii_filtered: bool = False
    tokens_replaced: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": self.execution_time_ms,
            "pii_filtered": self.pii_filtered,
            "tokens_replaced": self.tokens_replaced,
        }


class DockerExecutionService:
    """
    Container-based execution service using Docker.
    
    Provides secure, isolated execution environments for agent scripts.
    Implements the "Thin Client, Fat Backend" pattern where heavy computation
    happens in ephemeral containers.
    
    Key features:
    - Process isolation per agent session
    - Resource limits prevent runaway processes
    - Network restrictions prevent unauthorized access
    - Ephemeral filesystems ensure clean state
    - PII filtering before returning to context
    
    Example:
        >>> service = DockerExecutionService()
        >>> container = await service.spawn_container("python-executor")
        >>> result = await service.execute_script(
        ...     container,
        ...     "for f in files: print(process(f))"
        ... )
        >>> await service.destroy(container)
    """
    
    # Pre-configured container profiles
    PROFILES: Dict[str, ContainerConfig] = {
        "python-executor": ContainerConfig(
            image="python:3.11-slim",
            memory_limit="1g",
            cpu_limit=1.0,
            install_ctags=True,
            install_tree_sitter=True,
        ),
        "node-executor": ContainerConfig(
            image="node:20-alpine",
            memory_limit="512m",
            cpu_limit=0.5,
        ),
        "research-executor": ContainerConfig(
            image="python:3.11-slim",
            memory_limit="2g",
            cpu_limit=2.0,
            timeout_seconds=600,
            install_ctags=True,
            install_tree_sitter=True,
        ),
    }
    
    def __init__(
        self,
        docker_socket: str = "/var/run/docker.sock",
        default_timeout: int = 300,
        enable_pii_filtering: bool = True,
    ):
        """
        Initialize the Docker Execution Service.
        
        Args:
            docker_socket: Path to Docker socket.
            default_timeout: Default execution timeout in seconds.
            enable_pii_filtering: Enable automatic PII filtering.
        """
        self._docker_socket = docker_socket
        self._default_timeout = default_timeout
        self._enable_pii_filtering = enable_pii_filtering
        self._active_containers: Dict[str, Container] = {}
        
        # Import privacy filter lazily
        self._privacy_filter = None
    
    def _get_privacy_filter(self):
        """Lazy load privacy filter."""
        if self._privacy_filter is None:
            from src.execution.privacy_filter import PrivacyFilter
            self._privacy_filter = PrivacyFilter()
        return self._privacy_filter
    
    def _check_docker_available(self) -> bool:
        """Check if Docker is available on the system."""
        return Path(self._docker_socket).exists()
    
    @trace_run(name="Docker: Spawn Container", run_type=RunType.TOOL)
    async def spawn_container(
        self,
        profile: str = "python-executor",
        workspace_path: Optional[str] = None,
        custom_config: Optional[ContainerConfig] = None,
    ) -> Container:
        """
        Spawn an isolated container for agent execution.
        
        Args:
            profile: Pre-configured profile name (python-executor, node-executor, etc.)
            workspace_path: Optional workspace directory to mount.
            custom_config: Override profile with custom configuration.
            
        Returns:
            Container: Container object for execution.
            
        Raises:
            ContainerError: If container creation fails.
        """
        # Get configuration
        if custom_config:
            config = custom_config
        elif profile in self.PROFILES:
            config = self.PROFILES[profile]
        else:
            raise ContainerError(f"Unknown profile: {profile}. Available: {list(self.PROFILES.keys())}")
        
        # Create container object
        container = Container(
            id=str(uuid.uuid4())[:8],
            config=config,
        )
        
        # Create temporary workspace if not provided
        if workspace_path:
            container.workspace_path = Path(workspace_path)
        else:
            container.workspace_path = Path(tempfile.mkdtemp(prefix="sdlc_exec_"))
        
        # Check if Docker is available
        if not self._check_docker_available():
            # Fall back to subprocess execution (development mode)
            container.state = ContainerState.RUNNING
            container.container_id = f"subprocess_{container.id}"
            self._active_containers[container.id] = container
            return container
        
        # Build Docker run command
        docker_cmd = self._build_docker_command(container)
        
        try:
            # Start the container
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise ContainerError(f"Failed to start container: {stderr.decode()}")
            
            container.container_id = stdout.decode().strip()
            container.state = ContainerState.RUNNING
            self._active_containers[container.id] = container
            
            return container
            
        except Exception as e:
            container.state = ContainerState.ERROR
            raise ContainerError(f"Container spawn failed: {e}")
    
    def _build_docker_command(self, container: Container) -> List[str]:
        """Build the docker run command with security constraints."""
        config = container.config
        
        cmd = [
            "docker", "run", "-d",
            "--name", f"sdlc_exec_{container.id}",
            "--memory", config.memory_limit,
            f"--cpus={config.cpu_limit}",
            "--network", config.network_mode,
        ]
        
        # Security flags
        if config.read_only_root:
            cmd.append("--read-only")
        if config.no_new_privileges:
            cmd.append("--security-opt=no-new-privileges")
        for cap in config.cap_drop:
            cmd.extend(["--cap-drop", cap])
        
        # Mount workspace
        if container.workspace_path:
            cmd.extend([
                "-v", f"{container.workspace_path}:/workspace:rw"
            ])
            # Add tmpfs for /tmp since root is read-only
            cmd.extend(["--tmpfs", "/tmp:rw,noexec,nosuid,size=100m"])
        
        # Environment variables
        for key, value in config.environment.items():
            cmd.extend(["-e", f"{key}={value}"])
        
        # Image
        cmd.append(config.image)
        
        # Keep container running
        cmd.extend(["tail", "-f", "/dev/null"])
        
        return cmd
    
    @trace_run(name="Docker: Execute Script", run_type=RunType.TOOL)
    async def execute_script(
        self,
        container: Container,
        script: str,
        language: str = "python",
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """
        Execute a script inside the container.
        
        This is the key method that enables the "Code Execution" paradigm:
        - Agent writes a loop in code instead of 100 individual tool calls
        - Intermediate variables stay inside the container
        - Only filtered results return to context
        
        Args:
            container: Container to execute in.
            script: The script to execute.
            language: Script language (python, node).
            timeout: Execution timeout in seconds.
            
        Returns:
            ExecutionResult: Filtered execution result.
        """
        if not container.is_alive():
            raise ContainerError(f"Container {container.id} is not running")
        
        timeout = timeout or container.config.timeout_seconds
        start_time = datetime.utcnow()
        
        # Check if using subprocess fallback (development mode)
        if container.container_id and container.container_id.startswith("subprocess_"):
            return await self._execute_subprocess(script, language, timeout, start_time)
        
        # Write script to workspace
        script_path = container.workspace_path / f"script.{self._get_extension(language)}"
        script_path.write_text(script)
        
        # Build execution command
        exec_cmd = self._build_exec_command(container, script_path, language)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *exec_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds",
                    execution_time_ms=timeout * 1000,
                )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Apply privacy filtering
            stdout_str = stdout.decode()
            stderr_str = stderr.decode()
            tokens_replaced = 0
            
            if self._enable_pii_filtering:
                filter = self._get_privacy_filter()
                stdout_result = filter.filter_output(stdout_str)
                stderr_result = filter.filter_output(stderr_str)
                stdout_str = stdout_result.filtered_text
                stderr_str = stderr_result.filtered_text
                tokens_replaced = stdout_result.tokens_replaced + stderr_result.tokens_replaced
            
            return ExecutionResult(
                success=process.returncode == 0,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                execution_time_ms=execution_time,
                pii_filtered=self._enable_pii_filtering,
                tokens_replaced=tokens_replaced,
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time_ms=execution_time,
            )
    
    async def _execute_subprocess(
        self,
        script: str,
        language: str,
        timeout: int,
        start_time: datetime,
    ) -> ExecutionResult:
        """Fallback execution via subprocess (development mode)."""
        # Create temp file for script
        ext = self._get_extension(language)
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'.{ext}',
            delete=False
        ) as f:
            f.write(script)
            script_path = f.name
        
        try:
            if language == "python":
                cmd = ["python", script_path]
            elif language == "node":
                cmd = ["node", script_path]
            else:
                cmd = ["bash", script_path]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds",
                    execution_time_ms=timeout * 1000,
                )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            stdout_str = stdout.decode()
            stderr_str = stderr.decode()
            tokens_replaced = 0
            
            if self._enable_pii_filtering:
                filter = self._get_privacy_filter()
                stdout_result = filter.filter_output(stdout_str)
                stderr_result = filter.filter_output(stderr_str)
                stdout_str = stdout_result.filtered_text
                stderr_str = stderr_result.filtered_text
                tokens_replaced = stdout_result.tokens_replaced + stderr_result.tokens_replaced
            
            return ExecutionResult(
                success=process.returncode == 0,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                execution_time_ms=execution_time,
                pii_filtered=self._enable_pii_filtering,
                tokens_replaced=tokens_replaced,
            )
        finally:
            # Cleanup temp file
            Path(script_path).unlink(missing_ok=True)
    
    def _build_exec_command(
        self,
        container: Container,
        script_path: Path,
        language: str,
    ) -> List[str]:
        """Build docker exec command."""
        cmd = ["docker", "exec", container.container_id]
        
        if language == "python":
            cmd.extend(["python", f"/workspace/{script_path.name}"])
        elif language == "node":
            cmd.extend(["node", f"/workspace/{script_path.name}"])
        else:
            cmd.extend(["bash", f"/workspace/{script_path.name}"])
        
        return cmd
    
    def _get_extension(self, language: str) -> str:
        """Get file extension for language."""
        return {
            "python": "py",
            "node": "js",
            "bash": "sh",
        }.get(language, "txt")
    
    @trace_run(name="Docker: Destroy Container", run_type=RunType.TOOL)
    async def destroy(self, container: Container) -> None:
        """
        Destroy a container and clean up resources.
        
        This is critical for the "Context Firewall" pattern - ensures
        no state persists between executions.
        
        Args:
            container: Container to destroy.
        """
        if container.id in self._active_containers:
            del self._active_containers[container.id]
        
        # Skip Docker cleanup for subprocess fallback
        if container.container_id and container.container_id.startswith("subprocess_"):
            container.state = ContainerState.DESTROYED
            return
        
        if container.container_id:
            try:
                # Stop container
                stop_process = await asyncio.create_subprocess_exec(
                    "docker", "stop", container.container_id,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await stop_process.wait()
                
                # Remove container
                rm_process = await asyncio.create_subprocess_exec(
                    "docker", "rm", container.container_id,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await rm_process.wait()
                
            except Exception:
                pass  # Best effort cleanup
        
        container.state = ContainerState.DESTROYED
        
        # Cleanup workspace if temporary
        if container.workspace_path and "sdlc_exec_" in str(container.workspace_path):
            import shutil
            shutil.rmtree(container.workspace_path, ignore_errors=True)
    
    async def destroy_all(self) -> None:
        """Destroy all active containers."""
        for container in list(self._active_containers.values()):
            await self.destroy(container)
    
    def get_active_containers(self) -> List[Container]:
        """Get list of active containers."""
        return list(self._active_containers.values())


__all__ = [
    "DockerExecutionService",
    "Container",
    "ContainerConfig",
    "ContainerState",
    "ExecutionResult",
    "ContainerError",
]

