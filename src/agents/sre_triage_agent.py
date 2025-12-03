"""SRE-Triage agent for incident investigation and monitoring.

Uses centralized options builder for consistent SDK configuration.
Handles incidents, performance issues, capacity planning, and health checks.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.agents.runner import AgentResult, run_agent


# SRE task prompts
PROMPTS = {
    "incident": """
    Investigate and triage a production incident.
    
    ## Skills to Apply
    Use the following skills for incident response:
    - implementing-unleash-featureops: For feature flag management during incidents
    
    ## Steps
    1. Gather incident context (error messages, affected services)
    2. Use trace-analyzer subagent to analyze distributed traces
    3. Check metrics from context7://metrics resource
    4. Query Langfuse for LLM quality issues with check_langfuse_score
    5. Identify root cause through log analysis
    6. Determine mitigation strategy:
       a. If feature-related: disable via toggle_feature_flag
       b. If deployment-related: coordinate rollback
       c. If data-related: identify corrupted records
    7. Implement mitigation
    8. Create Linear issue for post-incident review
    
    ## Incident Severity Levels
    - SEV1: Complete service outage, >50% users affected
    - SEV2: Partial outage or degraded performance, >10% users affected
    - SEV3: Minor issue, <10% users affected
    - SEV4: No user impact, internal only
    """,
    "performance": """
    Investigate performance degradation.
    
    ## Steps
    1. Query current metrics from context7://metrics
    2. Identify which service/endpoint is slow
    3. Use trace-analyzer subagent on slow requests
    4. Check database query performance
    5. Analyze resource utilization (CPU, memory)
    6. Identify bottleneck (network, CPU, I/O, external dependency)
    7. Recommend optimization or scaling action
    
    ## Performance Thresholds
    - API response time p99 < 500ms
    - Database query time p99 < 100ms
    - Error rate < 0.1%
    """,
    "capacity": """
    Analyze capacity and scaling needs.
    
    ## Steps
    1. Query current resource utilization
    2. Analyze usage trends over past 30 days
    3. Project future capacity needs
    4. Identify services approaching limits
    5. Recommend scaling actions (horizontal/vertical)
    6. Calculate cost impact of scaling
    7. Create capacity planning report
    """,
    "health_check": """
    Perform system health check.
    
    ## Steps
    1. Query all service health endpoints
    2. Check database connectivity and replication lag
    3. Verify cache hit rates and connection pools
    4. Check message queue depths
    5. Verify external dependency status
    6. Check certificate expiration dates
    7. Generate health summary report
    8. Create issues for any degraded services
    """,
}


async def run_sre_triage_agent(
    task_type: str = "incident",
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AgentResult:
    """
    Run the SRE-Triage agent for operational tasks.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration.
    
    Args:
        task_type: Type of SRE task.
            Options: "incident", "performance", "capacity", "health_check"
        resume: Optional session ID to resume.
        permission_mode: Override permission mode.
    
    Returns:
        AgentResult containing session_id for potential resumption.
    """
    prompt = PROMPTS.get(task_type, PROMPTS["incident"])
    
    return await run_agent(
        agent_id="sre-triage",
        prompt=prompt,
        resume=resume,
        permission_mode_override=permission_mode,
    )


if __name__ == "__main__":
    asyncio.run(run_sre_triage_agent("incident"))
