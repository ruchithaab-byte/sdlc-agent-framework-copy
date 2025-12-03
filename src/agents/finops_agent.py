"""FinOps agent for cloud cost management and optimization.

Uses centralized options builder for consistent SDK configuration.
Handles cost analysis, optimization, forecasting, and budget alerts.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.agents.runner import AgentResult, run_agent


# FinOps task prompts
PROMPTS = {
    "analysis": """
    Analyze cloud infrastructure costs.
    
    ## Steps
    1. Use code_execution_cost_analysis to retrieve cost data
    2. Break down costs by:
       a. Service (EC2, RDS, S3, Lambda, etc.)
       b. Environment (production, staging, development)
       c. Team/Cost Center (using tags)
    3. Identify top cost drivers
    4. Compare with previous period
    5. Identify anomalies or unexpected increases
    6. Generate cost analysis report
    
    ## Key Metrics
    - Total monthly spend
    - Cost per environment
    - Cost per service
    - Month-over-month change
    - Budget utilization percentage
    """,
    "optimization": """
    Identify cost optimization opportunities.
    
    ## Steps
    1. Analyze current resource utilization
    2. Identify optimization opportunities:
       a. Right-sizing (underutilized instances)
       b. Reserved Instances / Savings Plans
       c. Spot Instances for non-critical workloads
       d. Storage optimization (lifecycle policies, tiering)
       e. Unused resources (unattached volumes, idle instances)
    3. Calculate potential savings for each recommendation
    4. Prioritize by savings impact and implementation effort
    5. Generate optimization roadmap
    
    ## Optimization Categories
    - Quick Wins: Low effort, immediate savings
    - Medium Term: Moderate effort, significant savings
    - Strategic: High effort, transformational savings
    """,
    "forecast": """
    Forecast future cloud costs.
    
    ## Steps
    1. Analyze historical cost trends
    2. Factor in planned infrastructure changes
    3. Account for expected traffic growth
    4. Model different scenarios:
       a. Conservative growth
       b. Expected growth
       c. Aggressive growth
    5. Project costs for next 3/6/12 months
    6. Compare against budget allocations
    7. Generate forecast report with recommendations
    """,
    "budget_alert": """
    Check budget status and alert on overruns.
    
    ## Steps
    1. Retrieve current spending vs budget
    2. Calculate burn rate
    3. Project end-of-month spend
    4. Identify services exceeding budget
    5. If over budget or projected overrun:
       a. Identify cost spikes
       b. Recommend immediate actions
       c. Alert stakeholders
    6. Generate budget status report
    
    ## Alert Thresholds
    - Warning: >80% budget utilized with >20% month remaining
    - Critical: >90% budget utilized with >10% month remaining
    - Emergency: Budget exceeded
    """,
    "chargeback": """
    Generate cost allocation and chargeback reports.
    
    ## Steps
    1. Query costs grouped by cost center tags
    2. Allocate shared costs (networking, support)
    3. Calculate per-team/project costs
    4. Generate chargeback invoices
    5. Identify untagged resources
    6. Create report for finance team
    
    ## Allocation Rules
    - Direct costs: Attributed to tagged cost center
    - Shared costs: Split by usage percentage or headcount
    - Untagged costs: Flagged for review and attribution
    """,
}


async def run_finops_agent(
    task_type: str = "analysis",
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AgentResult:
    """
    Run the FinOps agent for cost management.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration.
    
    Args:
        task_type: Type of FinOps task.
            Options: "analysis", "optimization", "forecast", "budget_alert", "chargeback"
        resume: Optional session ID to resume.
        permission_mode: Override permission mode.
    
    Returns:
        AgentResult containing session_id for potential resumption.
    """
    prompt = PROMPTS.get(task_type, PROMPTS["analysis"])
    
    return await run_agent(
        agent_id="finops",
        prompt=prompt,
        resume=resume,
        permission_mode_override=permission_mode,
    )


if __name__ == "__main__":
    asyncio.run(run_finops_agent("analysis"))
