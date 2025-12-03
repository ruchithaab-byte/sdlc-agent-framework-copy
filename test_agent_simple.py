#!/usr/bin/env python3
"""Simple test script for agent functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure environment variables are set
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(PROJECT_ROOT / 'config/credentials/google-service-account.json')

from src.agents.productspec_agent import run_productspec_agent

async def test_agent():
    """Test the ProductSpec agent with a simple request."""
    print("🚀 Testing ProductSpec Agent...")
    print(f"Credentials: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

    try:
        count = 0
        async for message in run_productspec_agent("Create a simple Hello World app"):
            print(f"Message {count}: {type(message).__name__}")
            if hasattr(message, 'content') and message.content:
                if hasattr(message.content, '__iter__') and not isinstance(message.content, str):
                    for content_block in message.content:
                        if hasattr(content_block, 'text'):
                            print(f"  Text: {content_block.text[:100]}...")
                else:
                    print(f"  Content: {str(message.content)[:100]}...")
            count += 1
            if count >= 5:  # Limit output for testing
                print("Limiting output to first 5 messages...")
                break

        print("✅ Agent test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_agent())
    sys.exit(0 if success else 1)