"""
CodeCraft Agent Output Schema.

Structured output for code generation, implementation,
and development tasks.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.schemas.base import FileReference, Status


class GeneratedFile(BaseModel):
    """A file created or modified by the agent."""
    path: str = Field(description="File path relative to repository root")
    action: str = Field(description="Action taken: created, modified, deleted")
    language: Optional[str] = Field(default=None, description="Programming language")
    lines_added: Optional[int] = Field(default=None, description="Lines added")
    lines_removed: Optional[int] = Field(default=None, description="Lines removed")
    description: str = Field(description="Brief description of changes")


class TestResult(BaseModel):
    """Test execution result."""
    name: str = Field(description="Test name or file")
    status: str = Field(description="Status: passed, failed, skipped")
    duration_ms: Optional[int] = Field(default=None, description="Execution time in ms")
    error_message: Optional[str] = Field(default=None, description="Error if failed")


class Implementation(BaseModel):
    """An implemented feature or component."""
    name: str = Field(description="Feature/component name")
    description: str = Field(description="What was implemented")
    files: List[GeneratedFile] = Field(description="Files involved")
    patterns_used: List[str] = Field(default_factory=list, description="Design patterns applied")
    dependencies_added: List[str] = Field(default_factory=list, description="New dependencies")


class CodeCraftResult(BaseModel):
    """
    Complete output from CodeCraft agent.
    
    This schema captures code generation results including
    files changed, implementations completed, and verification status.
    """
    # Summary
    summary: str = Field(description="Summary of what was built/modified")
    task_type: str = Field(description="Task type: frontend, backend, data, fullstack")
    status: Status = Field(description="Overall task status")
    
    # Implementations
    implementations: List[Implementation] = Field(
        default_factory=list,
        description="Features/components implemented"
    )
    
    # Files
    files_changed: List[GeneratedFile] = Field(
        default_factory=list,
        description="All files created, modified, or deleted"
    )
    total_files_changed: int = Field(description="Count of files changed")
    total_lines_added: int = Field(default=0, description="Total lines added")
    total_lines_removed: int = Field(default=0, description="Total lines removed")
    
    # Skills Applied (from Julley platform)
    skills_applied: List[str] = Field(
        default_factory=list,
        description="Platform skills used: implementing-nextjs-14-production, etc."
    )
    
    # Dependencies
    dependencies_added: List[str] = Field(
        default_factory=list,
        description="New package dependencies added"
    )
    dependencies_updated: List[str] = Field(
        default_factory=list,
        description="Dependencies that were updated"
    )
    
    # Verification
    tests_run: List[TestResult] = Field(
        default_factory=list,
        description="Tests that were executed"
    )
    tests_passed: int = Field(default=0, description="Number of tests passed")
    tests_failed: int = Field(default=0, description="Number of tests failed")
    build_status: Optional[str] = Field(default=None, description="Build status: success, failed")
    lint_status: Optional[str] = Field(default=None, description="Lint status: clean, warnings, errors")
    
    # Architecture Compliance
    patterns_followed: List[str] = Field(
        default_factory=list,
        description="Architecture patterns followed"
    )
    anti_patterns_avoided: List[str] = Field(
        default_factory=list,
        description="Anti-patterns that were avoided"
    )
    
    # Related Files
    related_files: List[FileReference] = Field(
        default_factory=list,
        description="Files referenced but not modified"
    )
    
    # Next Steps
    next_steps: List[str] = Field(
        default_factory=list,
        description="Recommended next steps"
    )
    
    # Warnings/Notes
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings or considerations"
    )


__all__ = [
    "GeneratedFile",
    "TestResult",
    "Implementation",
    "CodeCraftResult",
]

