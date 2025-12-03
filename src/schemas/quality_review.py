"""
QualityGuard Agent Output Schema.

Structured output for code quality reviews, test coverage analysis,
and quality gate assessments.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.schemas.base import ActionItem, FileReference, MetricValue, Severity


class QualityIssue(BaseModel):
    """A code quality issue found during review."""
    id: str = Field(description="Unique issue identifier")
    title: str = Field(description="Short issue title")
    description: str = Field(description="Detailed description of the issue")
    severity: Severity = Field(description="Issue severity level")
    category: str = Field(description="Issue category: code_smell, bug, vulnerability, duplication, etc.")
    file: FileReference = Field(description="File location of the issue")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix")
    rule_id: Optional[str] = Field(default=None, description="Linting rule or standard violated")


class TestCoverageReport(BaseModel):
    """Test coverage summary."""
    overall_percentage: float = Field(ge=0, le=100, description="Overall code coverage percentage")
    line_coverage: float = Field(ge=0, le=100, description="Line coverage percentage")
    branch_coverage: Optional[float] = Field(default=None, ge=0, le=100, description="Branch coverage")
    function_coverage: Optional[float] = Field(default=None, ge=0, le=100, description="Function coverage")
    uncovered_files: List[str] = Field(default_factory=list, description="Files with low/no coverage")
    new_code_coverage: Optional[float] = Field(default=None, ge=0, le=100, description="Coverage for new code")


class QualityGate(BaseModel):
    """Quality gate check result."""
    name: str = Field(description="Gate name")
    passed: bool = Field(description="Whether the gate passed")
    actual_value: Optional[float] = Field(default=None, description="Actual measured value")
    threshold: Optional[float] = Field(default=None, description="Required threshold")
    message: Optional[str] = Field(default=None, description="Gate status message")


class QualityReviewResult(BaseModel):
    """
    Complete output from QualityGuard agent.
    
    This schema captures code quality analysis results including
    issues found, test coverage, and quality gate status.
    """
    # Summary
    summary: str = Field(description="Executive summary of the quality review")
    overall_score: float = Field(ge=0, le=100, description="Overall quality score (0-100)")
    review_status: str = Field(description="PASSED, FAILED, or WARNING")
    
    # Issues
    issues: List[QualityIssue] = Field(default_factory=list, description="Quality issues found")
    issues_by_severity: dict = Field(
        default_factory=dict,
        description="Count of issues by severity: {critical: N, high: N, ...}"
    )
    
    # Coverage
    test_coverage: Optional[TestCoverageReport] = Field(
        default=None,
        description="Test coverage report"
    )
    
    # Quality Gates
    quality_gates: List[QualityGate] = Field(
        default_factory=list,
        description="Quality gate check results"
    )
    all_gates_passed: bool = Field(description="Whether all quality gates passed")
    
    # Metrics
    metrics: List[MetricValue] = Field(
        default_factory=list,
        description="Quality metrics: complexity, duplication, etc."
    )
    
    # Recommendations
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="Recommended actions to improve quality"
    )
    
    # Files analyzed
    files_analyzed: int = Field(description="Number of files analyzed")
    files_with_issues: List[str] = Field(
        default_factory=list,
        description="Files that have quality issues"
    )


__all__ = [
    "QualityIssue",
    "TestCoverageReport",
    "QualityGate",
    "QualityReviewResult",
]

