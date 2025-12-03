#!/usr/bin/env python3
"""
Script to create a Linear epic for the Advanced Analytics Dashboard project.
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
    title = "Advanced Analytics Dashboard with AI-Powered Insights"
    description = """## Project Overview
Enterprise-grade analytics dashboard with AI-powered insights, real-time data visualization, and automated reporting capabilities. This project aims to deliver a comprehensive analytics solution that empowers teams to make data-driven decisions with confidence.

## Key Objectives
- **Enable Data-Driven Decision Making**: Provide intuitive visualizations and actionable insights that help stakeholders understand complex data patterns
- **Provide Predictive Analytics**: Leverage AI/ML models to forecast trends, identify anomalies, and suggest optimization opportunities
- **Automate Report Generation**: Streamline reporting workflows with intelligent automation that delivers insights on schedule

## Target Users
- **Enterprise Customers**: Large organizations requiring comprehensive analytics capabilities
- **Data Analysts**: Professionals who need advanced tools for deep data exploration and analysis
- **Business Intelligence Teams**: Teams responsible for strategic insights and reporting across the organization

## Success Metrics
- **User Engagement**: Track active users, session duration, and feature adoption rates
- **Report Generation Efficiency**: Measure time saved through automation and reduction in manual reporting tasks
- **Insight Accuracy**: Validate prediction accuracy and user confidence in AI-generated insights

## Technical Scope
This epic encompasses:
- Real-time data ingestion and processing pipelines
- Interactive visualization components with drill-down capabilities
- AI/ML integration for predictive analytics
- Automated report scheduling and distribution
- Role-based access control and data security
- Performance optimization for large datasets"""

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
