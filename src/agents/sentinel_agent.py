"""Sentinel agent for security monitoring and compliance.

Uses centralized options builder for consistent SDK configuration.
Handles threat monitoring, compliance audits, vulnerability scans, and access reviews.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.agents.runner import AgentResult, run_agent


# Security task prompts
PROMPTS = {
    "threat_monitor": """
    Monitor and respond to security threats.
    
    ## Skills to Apply
    Use the following skills for security best practices:
    - implementing-opa-production: For policy enforcement patterns
    - implementing-permitio-authorization: For authorization checks
    
    ## Steps
    1. Query GuardDuty findings from aws://guardduty/findings resource
    2. Analyze severity and potential impact
    3. For critical findings:
       a. Create Linear issue with create_linear_issue
       b. Initiate incident response if needed
       c. Rotate affected credentials with rotate_secret
    4. For high/medium findings:
       a. Document in security log
       b. Schedule remediation
    5. Generate daily security summary
    
    ## Response Priorities
    - Critical: Immediate response within 15 minutes
    - High: Response within 1 hour
    - Medium: Response within 24 hours
    - Low: Track and remediate in next sprint
    """,
    "compliance_audit": """
    Perform compliance audit of infrastructure and code.
    
    ## Steps
    1. Scan infrastructure for compliance violations
    2. Check encryption at rest for all data stores
    3. Verify TLS configuration for all endpoints
    4. Audit IAM policies for least privilege
    5. Check logging and audit trail coverage
    6. Generate compliance report
    7. Create Linear issues for violations
    
    ## Compliance Frameworks
    - SOC 2 Type II controls
    - GDPR data protection requirements
    - PCI-DSS if handling payment data
    """,
    "vulnerability_scan": """
    Scan for security vulnerabilities.
    
    ## Steps
    1. Scan dependencies for known CVEs
    2. Check container images for vulnerabilities
    3. Review code for security anti-patterns
    4. Check for exposed secrets in code
    5. Verify security headers on all endpoints
    6. Generate vulnerability report
    7. Prioritize and create remediation tasks
    
    ## Priority Scoring
    - CVSS 9.0+: Critical - immediate fix required
    - CVSS 7.0-8.9: High - fix within 7 days
    - CVSS 4.0-6.9: Medium - fix within 30 days
    - CVSS < 4.0: Low - fix in next release
    """,
    "access_review": """
    Review and audit access controls.
    
    ## Steps
    1. List all IAM users and roles
    2. Identify unused credentials (no activity > 90 days)
    3. Review service account permissions
    4. Check for overly permissive policies
    5. Verify MFA enforcement
    6. Generate access review report
    7. Create remediation tasks for issues
    """,
}


async def run_sentinel_agent(
    task_type: str = "threat_monitor",
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AgentResult:
    """
    Run the Sentinel agent for security operations.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration.
    
    Args:
        task_type: Type of security task.
            Options: "threat_monitor", "compliance_audit", "vulnerability_scan", "access_review"
        resume: Optional session ID to resume.
        permission_mode: Override permission mode.
    
    Returns:
        AgentResult containing session_id for potential resumption.
    """
    prompt = PROMPTS.get(task_type, PROMPTS["threat_monitor"])
    
    return await run_agent(
        agent_id="sentinel",
        prompt=prompt,
        resume=resume,
        permission_mode_override=permission_mode,
    )


if __name__ == "__main__":
    asyncio.run(run_sentinel_agent("threat_monitor"))
