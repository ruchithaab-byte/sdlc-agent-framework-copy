"""
SprintMaster Agent Output Schema.

Structured output for sprint planning, capacity analysis,
and work item management.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.schemas.base import Priority, Status


class StoryPoints(BaseModel):
    """Story point allocation."""
    estimated: float = Field(description="Estimated story points")
    completed: Optional[float] = Field(default=None, description="Completed story points")
    remaining: Optional[float] = Field(default=None, description="Remaining story points")


class TeamMember(BaseModel):
    """Team member with capacity info."""
    name: str = Field(description="Team member name")
    email: Optional[str] = Field(default=None, description="Team member email")
    role: str = Field(description="Role: developer, qa, designer, etc.")
    capacity_hours: float = Field(description="Available capacity in hours")
    allocated_points: float = Field(default=0, description="Points allocated to this member")


class WorkItem(BaseModel):
    """A work item (story, task, bug) in the sprint."""
    id: str = Field(description="Work item ID from Linear/Jira")
    title: str = Field(description="Work item title")
    type: str = Field(description="Type: story, task, bug, spike")
    priority: Priority = Field(description="Priority level")
    status: Status = Field(description="Current status")
    story_points: Optional[float] = Field(default=None, description="Estimated story points")
    assignee: Optional[str] = Field(default=None, description="Assigned team member")
    labels: List[str] = Field(default_factory=list, description="Labels/tags")
    dependencies: List[str] = Field(default_factory=list, description="IDs of blocking items")
    acceptance_criteria: Optional[str] = Field(default=None, description="Acceptance criteria summary")


class SprintGoal(BaseModel):
    """Sprint goal or objective."""
    description: str = Field(description="Goal description")
    key_deliverables: List[str] = Field(description="Key deliverables for this goal")
    progress_percentage: Optional[float] = Field(default=None, ge=0, le=100, description="Progress")


class Risk(BaseModel):
    """Sprint risk or blocker."""
    id: str = Field(description="Risk identifier")
    title: str = Field(description="Risk title")
    description: str = Field(description="Risk description")
    probability: str = Field(description="Probability: high, medium, low")
    impact: str = Field(description="Impact: high, medium, low")
    mitigation: Optional[str] = Field(default=None, description="Mitigation strategy")
    owner: Optional[str] = Field(default=None, description="Risk owner")


class SprintPlanResult(BaseModel):
    """
    Complete output from SprintMaster agent.
    
    This schema captures sprint planning results including
    work item assignments, capacity analysis, and risk assessment.
    """
    # Sprint Info
    sprint_name: str = Field(description="Sprint name or identifier")
    sprint_number: Optional[int] = Field(default=None, description="Sprint number")
    start_date: str = Field(description="Sprint start date (ISO format)")
    end_date: str = Field(description="Sprint end date (ISO format)")
    duration_days: int = Field(description="Sprint duration in days")
    
    # Goals
    sprint_goals: List[SprintGoal] = Field(
        default_factory=list,
        description="Sprint goals and objectives"
    )
    
    # Capacity
    team_capacity: StoryPoints = Field(description="Total team capacity")
    team_members: List[TeamMember] = Field(
        default_factory=list,
        description="Team members and their capacity"
    )
    capacity_utilization: float = Field(
        ge=0, le=100,
        description="Capacity utilization percentage"
    )
    
    # Work Items
    work_items: List[WorkItem] = Field(
        default_factory=list,
        description="Work items planned for the sprint"
    )
    items_by_type: dict = Field(
        default_factory=dict,
        description="Count by type: {story: N, bug: N, task: N}"
    )
    items_by_priority: dict = Field(
        default_factory=dict,
        description="Count by priority: {P0: N, P1: N, ...}"
    )
    
    # Points Summary
    total_points: float = Field(description="Total story points in sprint")
    points_by_assignee: dict = Field(
        default_factory=dict,
        description="Points allocated per assignee"
    )
    
    # Dependencies & Risks
    dependencies_graph: List[dict] = Field(
        default_factory=list,
        description="Dependency relationships"
    )
    risks: List[Risk] = Field(
        default_factory=list,
        description="Identified risks and blockers"
    )
    
    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list,
        description="Planning recommendations"
    )
    carryover_items: List[str] = Field(
        default_factory=list,
        description="Items recommended to defer to next sprint"
    )
    
    # Summary
    summary: str = Field(description="Sprint planning summary")
    health_status: str = Field(description="Sprint health: healthy, at_risk, critical")


__all__ = [
    "StoryPoints",
    "TeamMember",
    "WorkItem",
    "SprintGoal",
    "Risk",
    "SprintPlanResult",
]

