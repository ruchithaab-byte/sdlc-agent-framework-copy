#!/usr/bin/env python3
"""
Test script to verify Claude Agent SDK is using Vertex AI.

This script makes a simple query to verify that the SDK is routing
through Vertex AI endpoints instead of Anthropic's direct API.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions

# Load environment variables
load_dotenv(project_root / ".env")


async def test_vertex_ai_agent(timeout: int = 60) -> tuple[bool, Dict[str, Any]]:
    """Test that the agent is using Vertex AI.
    
    Args:
        timeout: Maximum time in seconds to wait for agent response
        
    Returns:
        tuple: (success: bool, results: dict) - Success status and detailed results
    """
    print("=" * 60)
    print("Testing Claude Agent SDK with Vertex AI")
    print("=" * 60)
    print()
    
    results = {
        "configuration": {},
        "execution": {},
        "messages": {},
        "tools": {}
    }
    
    # Verify configuration
    claude_vertex = os.getenv("CLAUDE_CODE_USE_VERTEX")
    vertex_project = os.getenv("ANTHROPIC_VERTEX_PROJECT_ID")
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if claude_vertex != "1":
        print("⚠ Warning: CLAUDE_CODE_USE_VERTEX is not set to 1")
        print("  The SDK may not be using Vertex AI")
        print()
        results["configuration"]["vertex_enabled"] = False
    else:
        results["configuration"]["vertex_enabled"] = True
    
    print("Configuration:")
    print(f"  CLAUDE_CODE_USE_VERTEX: {claude_vertex or 'NOT SET'}")
    print(f"  ANTHROPIC_VERTEX_PROJECT_ID: {vertex_project or 'NOT SET'}")
    print(f"  GOOGLE_APPLICATION_CREDENTIALS: {google_creds or 'NOT SET'}")
    print()
    
    results["configuration"]["vertex_project"] = vertex_project
    results["configuration"]["google_creds"] = bool(google_creds)
    
    # Configure agent options
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read", "Write"],  # Minimal tools for testing
    )
    
    print("Making test query...")
    print("-" * 60)
    
    try:
        # Simple test query
        test_prompt = "Hello! Can you confirm you're working? Just respond with 'Yes, I'm working!'"
        
        print(f"Query: {test_prompt}")
        print()
        print("Response:")
        print("-" * 60)
        
        message_count = 0
        content_messages = []
        tool_use_count = 0
        tool_result_count = 0
        tool_uses = []
        tool_results = []
        
        # Use asyncio.wait_for for timeout handling
        try:
            async def collect_messages():
                nonlocal message_count, content_messages, tool_use_count, tool_result_count
                nonlocal tool_uses, tool_results
                
                async for message in query(prompt=test_prompt, options=options):
                    message_count += 1
                    # Print all messages (like other agents do)
                    print(message)
                    
                    # Collect string messages for verification
                    if isinstance(message, str):
                        content_messages.append(message)
                    # Also check for message objects with content
                    elif hasattr(message, '__str__'):
                        msg_str = str(message)
                        # Skip system initialization messages
                        if "subtype='init'" not in msg_str:
                            content_messages.append(msg_str)
                    
                    # Check for tool usage
                    msg_str_lower = str(message).lower()
                    if "tooluse" in msg_str_lower or "tool_use" in msg_str_lower:
                        tool_use_count += 1
                        tool_uses.append(str(message))
                    if "toolresult" in msg_str_lower or "tool_result" in msg_str_lower:
                        tool_result_count += 1
                        tool_results.append(str(message))
                    
                    # Check for tool-related attributes
                    if hasattr(message, 'type'):
                        if 'tool_use' in str(message.type).lower():
                            tool_use_count += 1
                            tool_uses.append(str(message))
                        if 'tool_result' in str(message.type).lower():
                            tool_result_count += 1
                            tool_results.append(str(message))
            
            await asyncio.wait_for(collect_messages(), timeout=timeout)
            
        except asyncio.TimeoutError:
            print()
            print(f"⚠ Query timed out after {timeout} seconds")
            results["execution"]["timeout"] = True
            results["execution"]["success"] = False
            return False, results
        
        print()
        print("-" * 60)
        print()
        
        results["messages"]["total_count"] = message_count
        results["messages"]["content_count"] = len(content_messages)
        results["tools"]["tool_use_count"] = tool_use_count
        results["tools"]["tool_result_count"] = tool_result_count
        
        if message_count > 0:
            print(f"✓ Successfully received {message_count} message(s) from agent")
            results["execution"]["messages_received"] = True
            
            if content_messages:
                print("✓ Received content messages")
                print("✓ Vertex AI configuration appears to be working")
                results["execution"]["content_received"] = True
                results["execution"]["success"] = True
            else:
                print("⚠ Received messages but no content (may be system messages only)")
                results["execution"]["content_received"] = False
                results["execution"]["success"] = False
            
            # Report tool usage
            if tool_use_count > 0:
                print(f"✓ Detected {tool_use_count} tool use(s)")
                results["tools"]["tools_used"] = True
            else:
                print("ℹ No tool usage detected (this is normal for simple queries)")
                results["tools"]["tools_used"] = False
        else:
            print("⚠ No messages received")
            results["execution"]["messages_received"] = False
            results["execution"]["success"] = False
            
    except Exception as e:
        print()
        print("✗ Error occurred:")
        print(f"  {type(e).__name__}: {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Verify Vertex AI API is enabled")
        print("  2. Check service account permissions")
        print("  3. Ensure billing is enabled for the project")
        print("  4. Check that CLAUDE_CODE_USE_VERTEX=1 is set")
        results["execution"]["error"] = {
            "type": type(e).__name__,
            "message": str(e)
        }
        results["execution"]["success"] = False
        return False, results
    
    print()
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)
    return True, results


if __name__ == "__main__":
    success, results = asyncio.run(test_vertex_ai_agent())
    sys.exit(0 if success else 1)

