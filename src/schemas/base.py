"""
Base types and mixins for SDLC agent schemas.

These provide common fields and patterns used across multiple agent outputs.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Standard severity levels used across agents."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Status(str, Enum):
    """Standard status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Priority(str, Enum):
    """Standard priority levels."""
    P0 = "P0"  # Critical/Emergency
    P1 = "P1"  # High
    P2 = "P2"  # Medium
    P3 = "P3"  # Low
    P4 = "P4"  # Backlog


class FileReference(BaseModel):
    """Reference to a file with optional location info."""
    path: str = Field(description="File path relative to repository root")
    line_start: Optional[int] = Field(default=None, description="Starting line number")
    line_end: Optional[int] = Field(default=None, description="Ending line number")
    snippet: Optional[str] = Field(default=None, description="Code snippet for context")


class ActionItem(BaseModel):
    """A recommended action or task."""
    title: str = Field(description="Short action title")
    description: str = Field(description="Detailed description of the action")
    priority: Priority = Field(default=Priority.P2, description="Action priority")
    assignee: Optional[str] = Field(default=None, description="Suggested assignee")
    due_date: Optional[str] = Field(default=None, description="Suggested due date")
    files: List[FileReference] = Field(default_factory=list, description="Related files")


class MetricValue(BaseModel):
    """A metric with value and optional thresholds."""
    name: str = Field(description="Metric name")
    value: float = Field(description="Metric value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    threshold_warning: Optional[float] = Field(default=None, description="Warning threshold")
    threshold_critical: Optional[float] = Field(default=None, description="Critical threshold")
    trend: Optional[str] = Field(default=None, description="Trend indicator: up, down, stable")


class AgentMetadata(BaseModel):
    """Metadata about agent execution (optional in output)."""
    agent_id: str = Field(description="Agent that produced this output")
    execution_timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="When this output was generated"
    )
    session_id: Optional[str] = Field(default=None, description="Session ID for tracing")
    version: str = Field(default="1.0.0", description="Schema version")


__all__ = [
    "Severity",
    "Status",
    "Priority",
    "FileReference",
    "ActionItem",
    "MetricValue",
    "AgentMetadata",
]

