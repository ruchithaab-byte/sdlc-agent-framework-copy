"""DocuScribe agent for documentation generation and publishing.

Uses centralized options builder for consistent SDK configuration.
Generates API docs, architecture docs, user guides, and READMEs.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from src.agents.runner import AgentResult, run_agent


# Documentation type prompts
PROMPTS = {
    "api": """
    Generate API documentation for the authentication microservice.
    
    ## Skills to Apply
    Use the following skills for documentation best practices:
    - mintlify-documentation: For Mintlify setup and configuration
    - configuring-mintlify: For theming and customization
    
    ## Steps
    1. Load architecture plan from `.sdlc/memories/architecture_plan.xml`
    2. Scan source code for API endpoints and schemas
    3. Generate OpenAPI specification if not present
    4. Create Mintlify-compatible markdown documentation
    5. Add code examples for each endpoint
    6. Publish to Backstage TechDocs using publish_techdocs
    
    ## Documentation Standards
    - Include request/response examples
    - Document all error codes and responses
    - Add authentication requirements for each endpoint
    - Include rate limiting information
    """,
    "architecture": """
    Generate architecture documentation for the system.
    
    ## Steps
    1. Load architecture plan from memory
    2. Create architecture overview with diagrams (Mermaid)
    3. Document component interactions
    4. Create deployment topology documentation
    5. Document data flow and security boundaries
    6. Publish to TechDocs
    """,
    "user_guide": """
    Generate user guide documentation.
    
    ## Steps
    1. Identify target user personas
    2. Create getting started guide
    3. Document common use cases with examples
    4. Create troubleshooting section
    5. Add FAQ based on common issues
    6. Publish to TechDocs
    """,
    "readme": """
    Generate or update project README.
    
    ## Steps
    1. Create project overview
    2. Add installation instructions
    3. Document configuration options
    4. Add usage examples
    5. Include contributing guidelines
    6. Add license and contact information
    """,
}


async def run_docuscribe_agent(
    doc_type: str = "api",
    resume: Optional[str] = None,
    permission_mode: Optional[str] = None,
) -> AgentResult:
    """
    Run the DocuScribe agent to generate and publish documentation.
    
    Uses centralized options builder from AGENT_PROFILES for consistent
    SDK configuration.
    
    Args:
        doc_type: Type of documentation to generate.
            Options: "api", "architecture", "user_guide", "readme"
        resume: Optional session ID to resume.
        permission_mode: Override permission mode (default from profile: acceptEdits).
    
    Returns:
        AgentResult containing session_id for potential resumption.
    """
    prompt = PROMPTS.get(doc_type, PROMPTS["api"])
    
    return await run_agent(
        agent_id="docuscribe",
        prompt=prompt,
        resume=resume,
        permission_mode_override=permission_mode,
    )


if __name__ == "__main__":
    asyncio.run(run_docuscribe_agent("api"))
