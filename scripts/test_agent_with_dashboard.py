#!/usr/bin/env python3
"""
Test script to run a minimal agent execution and verify hooks are working.
This will generate events that should appear in the dashboard.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.productspec_agent import run_productspec_agent


async def main():
    """Run a quick agent test to generate dashboard events."""
    print("🚀 Running ProductSpec Agent Test...")
    print("=" * 60)
    print("📊 Watch the dashboard at http://localhost:8000")
    print("=" * 60)
    print()
    
    try:
        count = 0
        async for message in run_productspec_agent("Create a simple hello world app"):
            count += 1
            if count <= 5:  # Show first 5 messages
                print(f"📨 Message {count}: {str(message)[:100]}...")
        
        print()
        print("=" * 60)
        print("✅ Agent execution completed!")
        print("📊 Check the dashboard to see execution events")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

