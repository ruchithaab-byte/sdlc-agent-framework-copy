"""
ArchGuard Agent Output Schema.

Structured output for architecture reviews, design assessments,
and technical debt analysis.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.schemas.base import ActionItem, FileReference, MetricValue, Severity


class ArchitectureViolation(BaseModel):
    """An architecture rule or pattern violation."""
    id: str = Field(description="Violation identifier")
    title: str = Field(description="Short violation title")
    description: str = Field(description="Detailed description")
    severity: Severity = Field(description="Violation severity")
    rule: str = Field(description="Architecture rule violated")
    location: FileReference = Field(description="Location of violation")
    recommendation: str = Field(description="How to fix this violation")


class DependencyIssue(BaseModel):
    """A dependency-related issue."""
    type: str = Field(description="Issue type: circular, outdated, vulnerable, unused")
    source: str = Field(description="Source module/package")
    target: Optional[str] = Field(default=None, description="Target module (for circular)")
    description: str = Field(description="Issue description")
    severity: Severity = Field(description="Issue severity")


class LayerAnalysis(BaseModel):
    """Analysis of an architecture layer."""
    name: str = Field(description="Layer name: presentation, business, data, etc.")
    components: List[str] = Field(description="Components in this layer")
    violations: int = Field(default=0, description="Number of violations in this layer")
    coupling_score: Optional[float] = Field(default=None, description="Coupling metric")
    cohesion_score: Optional[float] = Field(default=None, description="Cohesion metric")


class TechnicalDebtItem(BaseModel):
    """A technical debt item."""
    id: str = Field(description="Debt item identifier")
    title: str = Field(description="Debt title")
    description: str = Field(description="What the debt is")
    impact: str = Field(description="Impact if not addressed")
    effort_hours: Optional[float] = Field(default=None, description="Estimated effort to fix")
    priority: str = Field(description="Priority: critical, high, medium, low")
    files: List[str] = Field(default_factory=list, description="Affected files")


class ArchitectureReviewResult(BaseModel):
    """
    Complete output from ArchGuard agent.
    
    This schema captures architecture analysis including
    violations, dependencies, and technical debt.
    """
    # Summary
    summary: str = Field(description="Executive summary of architecture review")
    architecture_score: float = Field(ge=0, le=100, description="Overall architecture health score")
    review_status: str = Field(description="PASSED, FAILED, or NEEDS_ATTENTION")
    
    # Violations
    violations: List[ArchitectureViolation] = Field(
        default_factory=list,
        description="Architecture violations found"
    )
    violations_by_severity: dict = Field(
        default_factory=dict,
        description="Count by severity"
    )
    
    # Layer Analysis
    layers: List[LayerAnalysis] = Field(
        default_factory=list,
        description="Analysis per architecture layer"
    )
    
    # Dependencies
    dependency_issues: List[DependencyIssue] = Field(
        default_factory=list,
        description="Dependency-related issues"
    )
    circular_dependencies: List[dict] = Field(
        default_factory=list,
        description="Circular dependency chains"
    )
    
    # Metrics
    metrics: List[MetricValue] = Field(
        default_factory=list,
        description="Architecture metrics: coupling, cohesion, complexity"
    )
    
    # Technical Debt
    technical_debt: List[TechnicalDebtItem] = Field(
        default_factory=list,
        description="Technical debt items"
    )
    total_debt_hours: float = Field(default=0, description="Total estimated debt hours")
    
    # Compliance
    patterns_detected: List[str] = Field(
        default_factory=list,
        description="Architecture patterns detected in codebase"
    )
    recommended_patterns: List[str] = Field(
        default_factory=list,
        description="Patterns recommended for adoption"
    )
    
    # Recommendations
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="Recommended architecture improvements"
    )
    
    # Diagrams/Visualizations (paths to generated files)
    generated_diagrams: List[str] = Field(
        default_factory=list,
        description="Paths to generated architecture diagrams"
    )


__all__ = [
    "ArchitectureViolation",
    "DependencyIssue",
    "LayerAnalysis",
    "TechnicalDebtItem",
    "ArchitectureReviewResult",
]

