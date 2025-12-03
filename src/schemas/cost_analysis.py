"""
FinOps Agent Output Schema.

Structured output for cost analysis, resource optimization,
and budget recommendations.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.schemas.base import ActionItem, MetricValue


class CostBreakdown(BaseModel):
    """Cost breakdown for a category or service."""
    category: str = Field(description="Cost category: compute, storage, network, etc.")
    service: Optional[str] = Field(default=None, description="Specific service")
    current_cost: float = Field(description="Current period cost in USD")
    previous_cost: Optional[float] = Field(default=None, description="Previous period cost")
    change_percentage: Optional[float] = Field(default=None, description="Percent change")
    forecast: Optional[float] = Field(default=None, description="Forecasted cost")


class ResourceOptimization(BaseModel):
    """A resource optimization opportunity."""
    id: str = Field(description="Opportunity identifier")
    resource_type: str = Field(description="Resource type: ec2, rds, lambda, etc.")
    resource_id: str = Field(description="Resource identifier")
    current_config: str = Field(description="Current configuration")
    recommended_config: str = Field(description="Recommended configuration")
    current_cost_monthly: float = Field(description="Current monthly cost")
    estimated_savings_monthly: float = Field(description="Estimated monthly savings")
    implementation_effort: str = Field(description="Effort: low, medium, high")
    risk: str = Field(description="Risk level: low, medium, high")


class UnusedResource(BaseModel):
    """An unused or idle resource."""
    resource_type: str = Field(description="Resource type")
    resource_id: str = Field(description="Resource identifier")
    region: Optional[str] = Field(default=None, description="Region")
    last_used: Optional[str] = Field(default=None, description="Last activity timestamp")
    monthly_cost: float = Field(description="Monthly cost")
    recommendation: str = Field(description="Terminate, downsize, or review")


class BudgetStatus(BaseModel):
    """Budget tracking status."""
    budget_name: str = Field(description="Budget name")
    budget_amount: float = Field(description="Budget amount")
    current_spend: float = Field(description="Current spend")
    forecasted_spend: float = Field(description="Forecasted end-of-period spend")
    utilization_percentage: float = Field(ge=0, description="Budget utilization")
    status: str = Field(description="Status: on_track, warning, exceeded")
    days_remaining: Optional[int] = Field(default=None, description="Days in period")


class CostAnomaly(BaseModel):
    """A cost anomaly or spike."""
    date: str = Field(description="Date of anomaly")
    service: str = Field(description="Service with anomaly")
    expected_cost: float = Field(description="Expected cost")
    actual_cost: float = Field(description="Actual cost")
    deviation_percentage: float = Field(description="Deviation from expected")
    possible_cause: str = Field(description="Possible cause")


class CostAnalysisResult(BaseModel):
    """
    Complete output from FinOps agent.
    
    This schema captures cost analysis including
    breakdowns, optimizations, and budget status.
    """
    # Summary
    summary: str = Field(description="Executive cost summary")
    analysis_period: str = Field(description="Period analyzed: daily, weekly, monthly")
    total_cost: float = Field(description="Total cost for the period")
    cost_change_percentage: Optional[float] = Field(default=None, description="Change from previous")
    
    # Cost Breakdown
    cost_by_category: List[CostBreakdown] = Field(
        default_factory=list,
        description="Costs broken down by category"
    )
    cost_by_service: List[CostBreakdown] = Field(
        default_factory=list,
        description="Costs broken down by service"
    )
    cost_by_team: List[CostBreakdown] = Field(
        default_factory=list,
        description="Costs broken down by team/project"
    )
    
    # Optimization Opportunities
    optimizations: List[ResourceOptimization] = Field(
        default_factory=list,
        description="Resource optimization opportunities"
    )
    total_potential_savings: float = Field(default=0, description="Total potential monthly savings")
    
    # Unused Resources
    unused_resources: List[UnusedResource] = Field(
        default_factory=list,
        description="Unused or idle resources"
    )
    unused_resources_cost: float = Field(default=0, description="Monthly cost of unused resources")
    
    # Budget Status
    budgets: List[BudgetStatus] = Field(
        default_factory=list,
        description="Budget tracking status"
    )
    overall_budget_health: str = Field(description="Overall: healthy, warning, critical")
    
    # Anomalies
    anomalies: List[CostAnomaly] = Field(
        default_factory=list,
        description="Cost anomalies detected"
    )
    
    # Metrics
    metrics: List[MetricValue] = Field(
        default_factory=list,
        description="Cost efficiency metrics"
    )
    
    # Forecast
    forecast_next_month: Optional[float] = Field(default=None, description="Next month forecast")
    forecast_confidence: Optional[str] = Field(default=None, description="Forecast confidence")
    
    # Recommendations
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="Cost optimization recommendations"
    )
    quick_wins: List[str] = Field(
        default_factory=list,
        description="Easy savings opportunities"
    )


__all__ = [
    "CostBreakdown",
    "ResourceOptimization",
    "UnusedResource",
    "BudgetStatus",
    "CostAnomaly",
    "CostAnalysisResult",
]

