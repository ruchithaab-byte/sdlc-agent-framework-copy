"""InfraOps agent for infrastructure deployment and management.

Uses centralized options builder for consistent SDK configuration.
Handles Terraform, Docker, secrets rotation, and deployments.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.agents.runner import AgentResult, run_agent


# Task-specific prompts for infrastructure operations
PROMPTS = {
    "terraform": """
    Analyze and apply Terraform infrastructure changes.
    
    ## Skills to Apply
    Use the following skills for infrastructure best practices:
    - implementing-kong-gateway: For API gateway configuration
    - implementing-kuma-production: For service mesh setup
    - implementing-opa-production: For policy enforcement
    
    ## Steps
    1. Review pending Terraform changes
    2. Use terraform-auditor subagent to analyze security risks
    3. Apply code_execution_terraform_analyze for comprehensive check
    4. Present findings and get approval
    5. Apply changes if approved
    6. Verify deployment status
    
    ## Security Checks Required
    - No public S3 buckets without justification
    - All storage encrypted at rest
    - Security groups follow least privilege
    - Required tags present on all resources
    """,
    "docker": """
    Build and deploy Docker containers.
    
    ## Steps
    1. Validate Dockerfile best practices
    2. Build image using docker_build_push
    3. Run security scan on built image
    4. Push to registry if scan passes
    5. Update Kubernetes deployment
    6. Use deployment-orchestrator subagent for rollout
    
    ## Best Practices
    - Use multi-stage builds
    - Pin base image versions
    - Run as non-root user
    - Minimize layer count
    """,
    "secrets": """
    Rotate secrets and credentials.
    
    ## Steps
    1. Identify secrets requiring rotation
    2. Generate new credentials using rotate_secret
    3. Update dependent services
    4. Verify services can authenticate with new credentials
    5. Deprecate old credentials
    6. Update documentation
    
    ## Security Requirements
    - Never log secret values
    - Use secure random generation
    - Notify affected service owners
    """,
    "deployment": """
    Perform zero-downtime deployment.
    
    ## Steps
    1. Use deployment-orchestrator subagent
    2. Build and push new container images
    3. Update feature flags for canary if needed
    4. Roll out to staging environment
    5. Run smoke tests
    6. Progressive rollout to production
    7. Monitor metrics during rollout
    8. Rollback if issues detected
    """,
}


async def run_infraops_agent(
    task_type: str = "terraform",
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AgentResult:
    """
    Run the InfraOps agent for infrastructure operations.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration. MCP servers are configured in the profile.
    
    Args:
        task_type: Type of infrastructure task.
            Options: "terraform", "docker", "secrets", "deployment"
        resume: Optional session ID to resume.
        permission_mode: Override permission mode.
    
    Returns:
        AgentResult containing session_id for potential resumption.
    """
    prompt = PROMPTS.get(task_type, PROMPTS["terraform"])
    
    return await run_agent(
        agent_id="infraops",
        prompt=prompt,
        resume=resume,
        permission_mode_override=permission_mode,
    )


if __name__ == "__main__":
    asyncio.run(run_infraops_agent("terraform"))
