"""
SRE-Triage Agent Output Schema.

Structured output for incident triage, root cause analysis,
and remediation recommendations.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.schemas.base import ActionItem, Severity


class IncidentTimeline(BaseModel):
    """An event in the incident timeline."""
    timestamp: str = Field(description="Event timestamp (ISO format)")
    event: str = Field(description="What happened")
    source: str = Field(description="Source: logs, metrics, alerts, user_report")
    significance: str = Field(description="Why this event matters")


class AffectedSystem(BaseModel):
    """A system or service affected by the incident."""
    name: str = Field(description="System/service name")
    impact_level: str = Field(description="Impact: critical, major, minor, none")
    symptoms: List[str] = Field(description="Observed symptoms")
    metrics_affected: List[str] = Field(default_factory=list, description="Metrics showing impact")


class RootCauseHypothesis(BaseModel):
    """A potential root cause hypothesis."""
    id: str = Field(description="Hypothesis identifier")
    description: str = Field(description="Root cause description")
    confidence: str = Field(description="Confidence: high, medium, low")
    evidence: List[str] = Field(description="Supporting evidence")
    contradictions: List[str] = Field(default_factory=list, description="Contradicting evidence")


class RemediationStep(BaseModel):
    """A remediation action."""
    order: int = Field(description="Execution order")
    action: str = Field(description="Action to take")
    command: Optional[str] = Field(default=None, description="Command to run if applicable")
    verification: str = Field(description="How to verify success")
    rollback: Optional[str] = Field(default=None, description="Rollback procedure")
    risk_level: str = Field(description="Risk of this action: high, medium, low")


class IncidentTriageResult(BaseModel):
    """
    Complete output from SRE-Triage agent.
    
    This schema captures incident analysis including
    timeline, root cause, and remediation plan.
    """
    # Incident Info
    incident_id: str = Field(description="Incident identifier")
    title: str = Field(description="Incident title")
    severity: Severity = Field(description="Incident severity")
    status: str = Field(description="Status: investigating, identified, monitoring, resolved")
    
    # Summary
    summary: str = Field(description="Executive summary of the incident")
    impact_summary: str = Field(description="Impact on users/business")
    
    # Timeline
    timeline: List[IncidentTimeline] = Field(
        default_factory=list,
        description="Chronological event timeline"
    )
    detection_time: str = Field(description="When incident was first detected")
    start_time: Optional[str] = Field(default=None, description="Estimated incident start")
    resolution_time: Optional[str] = Field(default=None, description="When resolved")
    
    # Affected Systems
    affected_systems: List[AffectedSystem] = Field(
        default_factory=list,
        description="Systems affected by the incident"
    )
    blast_radius: str = Field(description="Blast radius: isolated, service, region, global")
    
    # Root Cause Analysis
    root_cause_hypotheses: List[RootCauseHypothesis] = Field(
        default_factory=list,
        description="Potential root causes"
    )
    confirmed_root_cause: Optional[str] = Field(
        default=None,
        description="Confirmed root cause if identified"
    )
    contributing_factors: List[str] = Field(
        default_factory=list,
        description="Contributing factors"
    )
    
    # Remediation
    immediate_actions: List[RemediationStep] = Field(
        default_factory=list,
        description="Immediate remediation steps"
    )
    long_term_fixes: List[ActionItem] = Field(
        default_factory=list,
        description="Long-term fixes to prevent recurrence"
    )
    
    # Metrics & Evidence
    key_metrics: dict = Field(
        default_factory=dict,
        description="Key metrics during incident"
    )
    log_patterns: List[str] = Field(
        default_factory=list,
        description="Relevant log patterns found"
    )
    
    # Communication
    stakeholder_update: str = Field(description="Status update for stakeholders")
    technical_summary: str = Field(description="Technical summary for engineering")
    
    # Post-Incident
    lessons_learned: List[str] = Field(
        default_factory=list,
        description="Lessons from this incident"
    )
    follow_up_items: List[ActionItem] = Field(
        default_factory=list,
        description="Follow-up action items"
    )


__all__ = [
    "IncidentTimeline",
    "AffectedSystem",
    "RootCauseHypothesis",
    "RemediationStep",
    "IncidentTriageResult",
]

