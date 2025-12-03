#!/usr/bin/env python3
"""
Test script to verify agent tool execution via Vertex AI.

This script tests:
1. Agent can use Read tool
2. Agent can use Write tool
3. Tool permissions work correctly
4. Tool results are processed correctly
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions

# Load environment variables
load_dotenv(project_root / ".env")


async def test_read_tool(timeout: int = 60) -> tuple[bool, Dict[str, Any]]:
    """Test that agent can use Read tool."""
    print("=" * 60)
    print("Test 1: Read Tool Execution")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "read_tool",
        "success": False,
        "tool_used": False,
        "tool_result_received": False,
        "content_found": False
    }
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
    )
    
    # Create a test file to read
    test_file = project_root / "README.md"
    if not test_file.exists():
        test_file = project_root / "main.py"
    
    test_prompt = f"Please read the file '{test_file.name}' and tell me what it contains."
    
    print(f"Query: {test_prompt}")
    print()
    print("Response:")
    print("-" * 60)
    
    try:
        message_count = 0
        tool_use_detected = False
        tool_result_detected = False
        content_received = False
        
        async def collect_messages():
            nonlocal message_count, tool_use_detected, tool_result_detected, content_received
            
            async for message in query(prompt=test_prompt, options=options):
                message_count += 1
                print(message)
                
                msg_str = str(message).lower()
                if "tooluse" in msg_str or "tool_use" in msg_str or "read" in msg_str:
                    tool_use_detected = True
                    results["tool_used"] = True
                
                if "toolresult" in msg_str or "tool_result" in msg_str:
                    tool_result_detected = True
                    results["tool_result_received"] = True
                
                if isinstance(message, str) and len(message.strip()) > 10:
                    content_received = True
                    results["content_found"] = True
        
        await asyncio.wait_for(collect_messages(), timeout=timeout)
        
        print()
        print("-" * 60)
        print()
        
        if tool_use_detected:
            print("✓ Read tool was used")
        else:
            print("⚠ Read tool usage not clearly detected")
        
        if tool_result_detected:
            print("✓ Tool result was received")
        else:
            print("⚠ Tool result not clearly detected")
        
        if content_received:
            print("✓ Content was received from agent")
            results["success"] = True
        else:
            print("⚠ No content received")
        
    except asyncio.TimeoutError:
        print(f"\n⚠ Test timed out after {timeout} seconds")
        results["timeout"] = True
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    return results["success"], results


async def test_write_tool(timeout: int = 60) -> tuple[bool, Dict[str, Any]]:
    """Test that agent can use Write tool."""
    print("=" * 60)
    print("Test 2: Write Tool Execution")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "write_tool",
        "success": False,
        "tool_used": False,
        "tool_result_received": False,
        "file_created": False
    }
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, dir=project_root) as f:
        test_file_path = Path(f.name)
        test_file_name = test_file_path.name
    
    try:
        options = ClaudeAgentOptions(
            cwd=str(project_root),
            setting_sources=["user", "project"],
            allowed_tools=["Write"],
        )
        
        test_prompt = f"Create a file named '{test_file_name}' with the content 'This is a test file created by Vertex AI agent.'"
        
        print(f"Query: {test_prompt}")
        print()
        print("Response:")
        print("-" * 60)
        
        message_count = 0
        tool_use_detected = False
        tool_result_detected = False
        
        async def collect_messages():
            nonlocal message_count, tool_use_detected, tool_result_detected
            
            async for message in query(prompt=test_prompt, options=options):
                message_count += 1
                print(message)
                
                msg_str = str(message).lower()
                if "tooluse" in msg_str or "tool_use" in msg_str or "write" in msg_str:
                    tool_use_detected = True
                    results["tool_used"] = True
                
                if "toolresult" in msg_str or "tool_result" in msg_str:
                    tool_result_detected = True
                    results["tool_result_received"] = True
        
        await asyncio.wait_for(collect_messages(), timeout=timeout)
        
        print()
        print("-" * 60)
        print()
        
        # Check if file was created
        if test_file_path.exists():
            print(f"✓ File '{test_file_name}' was created")
            results["file_created"] = True
            results["success"] = True
        else:
            print(f"⚠ File '{test_file_name}' was not created")
        
        if tool_use_detected:
            print("✓ Write tool was used")
        else:
            print("⚠ Write tool usage not clearly detected")
        
        if tool_result_detected:
            print("✓ Tool result was received")
        else:
            print("⚠ Tool result not clearly detected")
        
        # Clean up
        if test_file_path.exists():
            test_file_path.unlink()
            print(f"✓ Cleaned up test file '{test_file_name}'")
        
    except asyncio.TimeoutError:
        print(f"\n⚠ Test timed out after {timeout} seconds")
        results["timeout"] = True
        if test_file_path.exists():
            test_file_path.unlink()
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
        if test_file_path.exists():
            test_file_path.unlink()
    
    return results["success"], results


async def test_tool_permissions(timeout: int = 60) -> tuple[bool, Dict[str, Any]]:
    """Test that tool permissions work correctly."""
    print("=" * 60)
    print("Test 3: Tool Permissions")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "tool_permissions",
        "success": False,
        "disallowed_tool_blocked": False
    }
    
    # Test with disallowed tools
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],  # Only allow Read, not Write
        disallowed_tools=["Write", "Bash"],  # Explicitly disallow Write and Bash
    )
    
    test_prompt = "Try to create a file called 'test_permissions.txt' with some content."
    
    print(f"Query: {test_prompt}")
    print("(Write tool should be blocked)")
    print()
    print("Response:")
    print("-" * 60)
    
    try:
        write_attempted = False
        
        async def collect_messages():
            nonlocal write_attempted
            
            async for message in query(prompt=test_prompt, options=options):
                print(message)
                
                msg_str = str(message).lower()
                # Check if agent tried to use Write tool
                if "write" in msg_str and ("tool" in msg_str or "blocked" in msg_str or "not allowed" in msg_str):
                    write_attempted = True
        
        await asyncio.wait_for(collect_messages(), timeout=timeout)
        
        print()
        print("-" * 60)
        print()
        
        # If Write tool was attempted but blocked, that's success
        # If agent refused without trying, that's also success
        # We consider this a success if the agent doesn't actually create the file
        test_file = project_root / "test_permissions.txt"
        if not test_file.exists():
            print("✓ Write tool was correctly blocked or not used")
            results["disallowed_tool_blocked"] = True
            results["success"] = True
        else:
            print("⚠ Write tool may have been used despite being disallowed")
            test_file.unlink()
        
    except asyncio.TimeoutError:
        print(f"\n⚠ Test timed out after {timeout} seconds")
        results["timeout"] = True
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    return results["success"], results


async def test_all_tools():
    """Run all tool tests."""
    print("\n" + "=" * 60)
    print("Vertex AI Tool Execution Test Suite")
    print("=" * 60)
    print()
    
    all_results = []
    
    # Test 1: Read tool
    success1, results1 = await test_read_tool()
    all_results.append(results1)
    print()
    
    # Test 2: Write tool
    success2, results2 = await test_write_tool()
    all_results.append(results2)
    print()
    
    # Test 3: Tool permissions
    success3, results3 = await test_tool_permissions()
    all_results.append(results3)
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.get("success", False))
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print()
    
    for result in all_results:
        status = "✓" if result.get("success", False) else "✗"
        print(f"{status} {result.get('test_name', 'Unknown test')}")
    
    overall_success = passed_tests == total_tests
    
    return overall_success, {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "results": all_results
    }


if __name__ == "__main__":
    success, results = asyncio.run(test_all_tools())
    sys.exit(0 if success else 1)

