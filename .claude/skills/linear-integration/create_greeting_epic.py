#!/usr/bin/env python3
"""
Script to create a Linear epic for the Simple Greeting Application project.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from config.agent_config import get_linear_settings
from src.mcp_servers.linear_server import LinearMCPServer


async def main():
    # Get Linear credentials
    linear_config = get_linear_settings()
    api_key = linear_config.get("api_key")
    team_id = linear_config.get("team_id")

    if not api_key or not team_id:
        print("Error: LINEAR_API_KEY and LINEAR_TEAM_ID must be set in .env file")
        print("Please check .env.example for reference")
        return 1

    # Create Linear client
    client = LinearMCPServer(api_key=api_key, team_id=team_id)

    # Epic details
    title = "Simple Greeting Application - Say Hello and Stop"
    description = """A minimal application that demonstrates basic lifecycle management with greeting functionality. The application should:
- Display a greeting message to users upon start
- Provide a clear and simple way to stop/exit the application
- Follow best practices for user experience in CLI applications

Key Features:
1. Immediate greeting on startup
2. Clear exit mechanism (via 'stop' command)
3. Graceful signal handling (Ctrl+C)
4. Proper exit codes
5. Minimal dependencies and fast startup

This epic will track the development of this simple yet well-designed greeting application."""

    try:
        # Create the epic
        print(f"Creating epic: {title}")
        result = await client.create_epic(title, description)

        # Extract epic information
        epic_data = result.get("issueCreate", {}).get("issue", {})
        epic_id = epic_data.get("id")
        epic_identifier = epic_data.get("identifier")
        epic_url = epic_data.get("url")

        print("\n" + "="*80)
        print("Epic created successfully!")
        print("="*80)
        print(f"Epic ID: {epic_id}")
        print(f"Epic Identifier: {epic_identifier}")
        print(f"Epic URL: {epic_url}")
        print("="*80)

        return 0

    except Exception as e:
        print(f"Error creating epic: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
