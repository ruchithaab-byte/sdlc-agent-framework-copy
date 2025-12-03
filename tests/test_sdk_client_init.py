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

import pytest
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from config.agent_config import resolve_model_config, PROJECT_ROOT as CONFIG_PROJECT_ROOT

@pytest.mark.asyncio
async def test_validate_client_init():
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
    
    # Initialize client
    async with ClaudeSDKClient(options=options) as client:
        assert client is not None
        print("  ✅ Client initialized successfully")

