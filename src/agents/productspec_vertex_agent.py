"""
ProductSpec agent using Vertex AI instead of Claude.

This is an alternative implementation that uses Google Cloud Vertex AI (Gemini)
instead of Anthropic Claude.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import AsyncIterator

# Add project root to path for imports
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.agents.vertex_ai_adapter import VertexAIAgent, create_vertex_ai_options
from config.agent_config import PROJECT_ROOT
from src.utils.constants import MEMORY_PRD_PATH


async def run_productspec_agent_vertex(requirements: str) -> AsyncIterator[str]:
    """
    Run the ProductSpec agent using Vertex AI (Gemini) instead of Claude.
    
    This version uses Google Cloud Vertex AI and requires:
    - Google Cloud service account credentials
    - Vertex AI API enabled in GCP project
    """
    # Create Vertex AI options
    # Note: Update project_id to match your GCP project
    # Current: Using "agents-with-claude" (from service account)
    # Alternative: "aesthetic-genre-476407-e6" (if using different project)
    options = create_vertex_ai_options(
        model="gemini-1.5-pro",  # Use Gemini Pro model
        project_id="agents-with-claude",  # Change to "aesthetic-genre-476407-e6" if needed
        location="us-central1",
    )
    
    # Initialize agent
    agent = VertexAIAgent(options)
    
    # Build prompt
    prompt = f"""
    Analyze the following requirements and produce a PRD stored at {MEMORY_PRD_PATH}.

    Requirements:
    {requirements}

    Steps:
    1. Research similar features and best practices
    2. Analyze competitor implementations
    3. Create a comprehensive PRD with:
       - Executive Summary
       - User Stories
       - Technical Requirements
       - Success Metrics
       - Dependencies
    4. Store the resulting PRD in memory for downstream agents

    Note: You have access to tools for file operations, bash commands, and memory storage.
    """
    
    # Query and stream response
    async for message in agent.query(prompt):
        yield message


if __name__ == "__main__":
    async def _main():
        async for event in run_productspec_agent_vertex("Build authentication microservice with JWT"):
            print(event, end="", flush=True)
        print()

    asyncio.run(_main())

