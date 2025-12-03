#!/usr/bin/env python3
"""
Script to create a comprehensive Linear epic for the Simple Greeting Application project.
This uses the detailed PRD content provided by the user.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
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
        print("\nTo configure Linear integration:")
        print("1. Uncomment LINEAR_API_KEY and LINEAR_TEAM_ID in your .env file")
        print("2. Add your Linear API key (get it from https://linear.app/settings/api)")
        print("3. Add your Linear Team ID (found in your team's URL)")
        return 1

    # Create Linear client
    client = LinearMCPServer(api_key=api_key, team_id=team_id)

    # Epic details based on PRD
    title = "Simple Greeting Application - Say Hello and Stop"

    description = """## Executive Summary

This defines requirements for a minimal greeting application that demonstrates best practices in application lifecycle management. The application will provide a simple "hello" greeting and clean stop functionality, serving as a reference implementation for basic CLI application patterns.

## Key Objectives

**P0 Priority:**
- Create a minimal application that greets users and exits cleanly
- Demonstrate proper signal handling and graceful shutdown

**P1 Priority:**
- Provide a reference implementation for CLI application patterns

## User Stories

### Critical Path (P0)
- **US-001**: User receives greeting on startup
- **US-002**: User can stop application via command
- **US-003**: User can interrupt with Ctrl+C

### Enhanced Features (P1)
- **US-004**: User receives help information

## Success Metrics

- Application starts and displays greeting within 100ms
- Clean shutdown on stop command with exit code 0
- Graceful handling of SIGINT (Ctrl+C) with proper cleanup
- Help documentation accessible via standard flags (--help, -h)
- Zero memory leaks or resource cleanup issues

## Timeline & Milestones

**Week 1: Basic Implementation**
- Core greeting functionality
- Stop command implementation
- Signal handling setup

**Week 2: Polish and Testing**
- Edge case handling
- Unit and integration tests
- Performance validation

**Week 3: Documentation and Release**
- User documentation
- Code documentation
- Release preparation

## Technical Considerations

This epic will track the development of a simple yet well-designed greeting application that serves as a reference implementation for:
- Proper application lifecycle management
- Signal handling best practices
- User-friendly CLI design
- Clean code architecture
"""

    try:
        # Create the epic
        print(f"Creating epic: {title}")
        print("\nEpic Description Preview:")
        print("="*80)
        print(description[:500] + "..." if len(description) > 500 else description)
        print("="*80)
        print("\nSending request to Linear...")

        result = await client.create_epic(title, description)

        # Extract epic information
        epic_data = result.get("issueCreate", {}).get("issue", {})
        epic_id = epic_data.get("id")
        epic_identifier = epic_data.get("identifier")
        epic_url = epic_data.get("url")

        print("\n" + "="*80)
        print("EPIC CREATED SUCCESSFULLY!")
        print("="*80)
        print(f"Epic ID: {epic_id}")
        print(f"Epic Identifier: {epic_identifier}")
        print(f"Epic URL: {epic_url}")
        print("="*80)
        print("\nYou can now view and manage your epic in Linear.")

        return 0

    except Exception as e:
        print(f"\nError creating epic: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting tips:")
        print("- Verify your LINEAR_API_KEY is correct and starts with 'lin_api_'")
        print("- Verify your LINEAR_TEAM_ID is correct")
        print("- Check that your API key has permission to create issues")
        print("- Ensure your .env file is properly formatted")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
