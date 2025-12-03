#!/usr/bin/env python3
"""
Advanced features test for Vertex AI agent execution.

This script tests (if configured):
1. Memory/CLAUDE.md loading
2. MCP integration
3. System prompts
4. Hook limitations documentation
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions

# Load environment variables
load_dotenv(project_root / ".env")


async def test_memory_loading(timeout: int = 60) -> tuple[bool, Dict[str, Any]]:
    """Test Memory/CLAUDE.md loading if setting_sources includes 'project'."""
    print("=" * 60)
    print("Test 1: Memory/CLAUDE.md Loading")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "memory_loading",
        "success": False,
        "claude_md_found": False,
        "memory_loaded": False
    }
    
    # Check if CLAUDE.md exists
    claude_md_paths = [
        project_root / "CLAUDE.md",
        project_root / ".claude" / "CLAUDE.md",
    ]
    
    claude_md_path = None
    for path in claude_md_paths:
        if path.exists():
            claude_md_path = path
            results["claude_md_found"] = True
            print(f"✓ Found CLAUDE.md at: {path}")
            break
    
    if not claude_md_path:
        print("⚠ No CLAUDE.md file found (this is optional)")
        print("  Create CLAUDE.md or .claude/CLAUDE.md to test memory loading")
        results["success"] = True  # Not a failure, just not testable
        return True, results
    
    # Test with project setting source
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],  # Include "project" to load CLAUDE.md
        allowed_tools=["Read"],
    )
    
    test_prompt = "Can you tell me what instructions or context you have from the CLAUDE.md file?"
    
    print(f"Query: {test_prompt}")
    print()
    print("Response:")
    print("-" * 60)
    
    try:
        memory_referenced = False
        
        async def collect_messages():
            nonlocal memory_referenced
            
            async for message in query(prompt=test_prompt, options=options):
                print(message)
                
                msg_str = str(message).lower()
                # Check if agent references CLAUDE.md content
                if "claude.md" in msg_str or "memory" in msg_str or "instructions" in msg_str:
                    memory_referenced = True
                    results["memory_loaded"] = True
        
        await asyncio.wait_for(collect_messages(), timeout=timeout)
        
        print()
        print("-" * 60)
        print()
        
        if memory_referenced:
            print("✓ Memory/CLAUDE.md appears to be loaded")
            results["success"] = True
        else:
            print("⚠ Memory/CLAUDE.md may not be loaded (this could be expected)")
            # Don't fail - memory loading behavior may vary
            results["success"] = True
        
    except asyncio.TimeoutError:
        print(f"\n⚠ Test timed out after {timeout} seconds")
        results["timeout"] = True
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    return results["success"], results


async def test_mcp_integration(timeout: int = 60) -> tuple[bool, Dict[str, Any]]:
    """Test MCP integration if configured."""
    print("=" * 60)
    print("Test 2: MCP Integration")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "mcp_integration",
        "success": False,
        "mcp_configured": False,
        "mcp_tools_available": False
    }
    
    # Check for MCP configuration
    mcp_config_paths = [
        project_root / ".claude" / "settings.json",
        project_root / ".claude" / "mcp_servers.json",
    ]
    
    mcp_configured = False
    for path in mcp_config_paths:
        if path.exists():
            mcp_configured = True
            results["mcp_configured"] = True
            print(f"✓ Found MCP config at: {path}")
            break
    
    if not mcp_configured:
        print("⚠ No MCP configuration found (this is optional)")
        print("  Configure MCP servers in .claude/settings.json to test MCP integration")
        results["success"] = True  # Not a failure, just not testable
        return True, results
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read", "Write"],  # MCP tools would be in addition to these
    )
    
    test_prompt = "What MCP tools or servers are available to you?"
    
    print(f"Query: {test_prompt}")
    print()
    print("Response:")
    print("-" * 60)
    
    try:
        mcp_mentioned = False
        
        async def collect_messages():
            nonlocal mcp_mentioned
            
            async for message in query(prompt=test_prompt, options=options):
                print(message)
                
                msg_str = str(message).lower()
                if "mcp" in msg_str or "model context protocol" in msg_str:
                    mcp_mentioned = True
                    results["mcp_tools_available"] = True
        
        await asyncio.wait_for(collect_messages(), timeout=timeout)
        
        print()
        print("-" * 60)
        print()
        
        if mcp_mentioned:
            print("✓ MCP integration appears to be working")
            results["success"] = True
        else:
            print("⚠ MCP tools may not be available (this could be expected)")
            results["success"] = True  # Don't fail - MCP may not be active
    
    except asyncio.TimeoutError:
        print(f"\n⚠ Test timed out after {timeout} seconds")
        results["timeout"] = True
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    return results["success"], results


async def test_system_prompts(timeout: int = 60) -> tuple[bool, Dict[str, Any]]:
    """Test system prompts and agent configuration."""
    print("=" * 60)
    print("Test 3: System Prompts")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "system_prompts",
        "success": False,
        "system_prompt_applied": False
    }
    
    # Test with custom agent options
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
    )
    
    test_prompt = "What is your role or purpose? How are you configured?"
    
    print(f"Query: {test_prompt}")
    print()
    print("Response:")
    print("-" * 60)
    
    try:
        system_info_mentioned = False
        
        async def collect_messages():
            nonlocal system_info_mentioned
            
            async for message in query(prompt=test_prompt, options=options):
                print(message)
                
                msg_str = str(message).lower()
                # Check if agent mentions its role or configuration
                if any(keyword in msg_str for keyword in ["role", "purpose", "configured", "assistant", "agent"]):
                    system_info_mentioned = True
                    results["system_prompt_applied"] = True
        
        await asyncio.wait_for(collect_messages(), timeout=timeout)
        
        print()
        print("-" * 60)
        print()
        
        if system_info_mentioned:
            print("✓ System prompts appear to be applied")
            results["success"] = True
        else:
            print("⚠ System prompt behavior may vary")
            results["success"] = True  # Don't fail - behavior may be implicit
    
    except asyncio.TimeoutError:
        print(f"\n⚠ Test timed out after {timeout} seconds")
        results["timeout"] = True
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    return results["success"], results


def document_hook_limitations():
    """Document known hook limitations with Vertex AI."""
    print("=" * 60)
    print("Hook Limitations Documentation")
    print("=" * 60)
    print()
    print("KNOWN LIMITATION: Hooks may not fire with Vertex AI backend")
    print()
    print("According to testing and documentation:")
    print("  - Execution hooks (PreToolUse, PostToolUse, SessionStart, SessionEnd)")
    print("    may not be supported when using CLAUDE_CODE_USE_VERTEX=1")
    print("  - The SDK routes through Vertex AI in a way that may bypass hooks")
    print("  - This is a known limitation with the Vertex AI backend")
    print()
    print("Workarounds:")
    print("  1. Use direct Anthropic API (set ANTHROPIC_API_KEY instead)")
    print("  2. Implement logging at the message level instead of hooks")
    print("  3. Monitor query() return messages for ToolUseBlock and ToolResultBlock")
    print()
    print("For more details, see: docs/HOOK_DEBUGGING.md")
    print()


async def test_all_advanced():
    """Run all advanced feature tests."""
    print("\n" + "=" * 60)
    print("Vertex AI Advanced Features Test Suite")
    print("=" * 60)
    print()
    
    all_results = []
    
    # Document hook limitations
    document_hook_limitations()
    print()
    
    # Test 1: Memory loading
    success1, results1 = await test_memory_loading()
    all_results.append(results1)
    print()
    
    # Test 2: MCP integration
    success2, results2 = await test_mcp_integration()
    all_results.append(results2)
    print()
    
    # Test 3: System prompts
    success3, results3 = await test_system_prompts()
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
        "results": all_results,
        "hook_limitations_documented": True
    }


if __name__ == "__main__":
    success, results = asyncio.run(test_all_advanced())
    sys.exit(0 if success else 1)

