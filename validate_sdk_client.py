#!/usr/bin/env python3
"""
Validation script for ClaudeSDKClient.
Verifies that the SDK Client can be initialized and used with the current configuration structure.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure environment variables are set
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(PROJECT_ROOT / 'config/credentials/google-service-account.json')

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from config.agent_config import resolve_model_config, PROJECT_ROOT as CONFIG_PROJECT_ROOT

async def validate_client():
    """Test ClaudeSDKClient initialization and basic connection."""
    print("🚀 Validating ClaudeSDKClient...")
    
    # Resolve configuration
    model_config = resolve_model_config("strategy")
    
    options = ClaudeAgentOptions(
        cwd=str(CONFIG_PROJECT_ROOT),
        model=model_config.name,
        allowed_tools=model_config.allowed_tools,
        setting_sources=["user", "project"]
    )
    
    print(f"  Configuration loaded for model: {options.model}")
    print(f"  Allowed tools: {len(options.allowed_tools)}")
    
    try:
        # Initialize client
        async with ClaudeSDKClient(options=options) as client:
            print("  ✅ Client initialized successfully")
            
            # We won't actually send a query to save cost/time and avoid side effects, 
            # but initialization proves the options structure is valid.
            # If we wanted to test connectivity:
            # await client.query("Hello")
            # async for message in client.receive_response():
            #    pass
            
            print("  ✅ Client context manager entered successfully")
            
        print("✅ ClaudeSDKClient validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error validating ClaudeSDKClient: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(validate_client())
    sys.exit(0 if success else 1)

