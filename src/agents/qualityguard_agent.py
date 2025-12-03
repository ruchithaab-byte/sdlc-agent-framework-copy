"""QualityGuard agent implementation.

Uses centralized options builder for consistent SDK configuration.
Performs code reviews, security analysis, and test coverage checks.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.agents.runner import AgentResult, run_agent


# Review type prompts
PROMPTS = {
    "full": """
    Perform a comprehensive quality review:
    1. Use code-reviewer-specialist subagent for detailed code analysis
    2. Use test-generator subagent for comprehensive test coverage
    3. Review recent code changes for issues
    4. Generate and execute regression tests
    5. Run security scanning commands when available
    6. Store QA summary in memory
    """,
    "quick": """
    Perform a quick quality review focusing on critical issues:
    1. Review recent code changes for obvious bugs
    2. Check for security vulnerabilities
    3. Verify basic test coverage exists
    4. Report critical findings only
    """,
    "security": """
    Perform a security-focused review:
    1. Use code-reviewer-specialist with security focus
    2. Run security scanning tools
    3. Check for common vulnerabilities (OWASP Top 10)
    4. Review authentication and authorization code
    5. Check for sensitive data exposure
    6. Generate security report
    """,
}


async def run_qualityguard_agent(
    review_type: str = "full",
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AgentResult:
    """
    Run the QualityGuard agent for quality assurance.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration.
    
    Args:
        review_type: Type of review (full, quick, security).
        resume: Optional session ID to resume.
        permission_mode: Override permission mode.
    
    Returns:
        AgentResult containing session_id for potential resumption.
    """
    prompt = PROMPTS.get(review_type, PROMPTS["full"])
    
    return await run_agent(
        agent_id="qualityguard",
        prompt=prompt,
        resume=resume,
        permission_mode_override=permission_mode,
    )


if __name__ == "__main__":
    asyncio.run(run_qualityguard_agent())
