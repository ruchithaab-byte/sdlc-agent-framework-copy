"""
Structured Output Schemas for SDLC Agents.

This module provides Pydantic schemas for type-safe agent outputs.
Each agent can optionally specify an output_schema in its profile
to get validated, structured results.

SDK Best Practices Applied (per StructuredOutputs.md):
- Use Pydantic BaseModel for Python type safety
- Use model_json_schema() for SDK output_format
- Use model_validate() for runtime validation
- Clean separation: output schema independent of task instructions

Usage:
    from src.schemas import SCHEMA_REGISTRY, get_output_format
    
    # Get JSON Schema for ClaudeAgentOptions
    output_format = get_output_format("quality_review")
    
    # Validate structured output from agent
    from src.schemas.quality_review import QualityReviewResult
    result = QualityReviewResult.model_validate(message.structured_output)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

# Import all schema models
from src.schemas.quality_review import QualityReviewResult
from src.schemas.sprint_plan import SprintPlanResult
from src.schemas.code_craft import CodeCraftResult
from src.schemas.architecture import ArchitectureReviewResult
from src.schemas.security import SecurityScanResult
from src.schemas.incident import IncidentTriageResult
from src.schemas.cost_analysis import CostAnalysisResult


# Registry mapping schema names to Pydantic models
SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = {
    "quality_review": QualityReviewResult,
    "sprint_plan": SprintPlanResult,
    "code_craft": CodeCraftResult,
    "architecture_review": ArchitectureReviewResult,
    "security_scan": SecurityScanResult,
    "incident_triage": IncidentTriageResult,
    "cost_analysis": CostAnalysisResult,
}


def get_output_format(schema_name: str) -> Optional[Dict[str, Any]]:
    """
    Get SDK output_format configuration for a schema.
    
    Args:
        schema_name: Name of the schema from SCHEMA_REGISTRY
        
    Returns:
        Dict with type and schema for ClaudeAgentOptions.output_format,
        or None if schema_name is None or not found
        
    Example:
        >>> output_format = get_output_format("quality_review")
        >>> options = ClaudeAgentOptions(output_format=output_format)
    """
    if not schema_name or schema_name not in SCHEMA_REGISTRY:
        return None
    
    model = SCHEMA_REGISTRY[schema_name]
    return {
        "type": "json_schema",
        "schema": model.model_json_schema()
    }


def validate_output(schema_name: str, data: Dict[str, Any]) -> BaseModel:
    """
    Validate structured output against a schema.
    
    Args:
        schema_name: Name of the schema from SCHEMA_REGISTRY
        data: Raw structured output from agent
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        KeyError: If schema_name not in registry
        ValidationError: If data doesn't match schema
        
    Example:
        >>> result = validate_output("quality_review", message.structured_output)
        >>> print(result.overall_score)
    """
    model = SCHEMA_REGISTRY[schema_name]
    return model.model_validate(data)


__all__ = [
    "SCHEMA_REGISTRY",
    "get_output_format",
    "validate_output",
    # Individual schemas
    "QualityReviewResult",
    "SprintPlanResult",
    "CodeCraftResult",
    "ArchitectureReviewResult",
    "SecurityScanResult",
    "IncidentTriageResult",
    "CostAnalysisResult",
]

