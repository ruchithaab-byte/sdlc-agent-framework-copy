"""
Execution module for Docker-based code execution.

Provides secure, isolated execution environments following the Docker MCP Toolkit pattern.
Key components:
- DockerExecutionService: Container lifecycle management
- BatchRunner: Execute agent-written scripts instead of individual tool calls
- PrivacyFilter: PII tokenization and filtering

Reference: "Code execution with MCP: building more efficient AI agents" - Anthropic
"""

from src.execution.docker_service import (
    DockerExecutionService,
    Container,
    ContainerConfig,
    ExecutionResult,
    ContainerError,
)
from src.execution.batch_runner import BatchRunner, BatchResult
from src.execution.privacy_filter import PrivacyFilter, TokenizationResult

__all__ = [
    "DockerExecutionService",
    "Container",
    "ContainerConfig",
    "ExecutionResult",
    "ContainerError",
    "BatchRunner",
    "BatchResult",
    "PrivacyFilter",
    "TokenizationResult",
]

