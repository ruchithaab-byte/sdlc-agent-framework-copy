#!/usr/bin/env python3
"""
Comprehensive hook detection test for Vertex AI backend.

Tests if hooks fire with Vertex AI using multiple independent detection methods:
1. Debug wrapper with print statements
2. File-based logging
3. Database write detection
4. Global state tracking
5. Exception-based detection
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

# Load environment variables
load_dotenv(project_root / ".env")

# Set test user email
os.environ['AGENT_USER_EMAIL'] = 'test-hook-detection@example.com'

# Import hooks after setting environment
from src.hooks import documentation_hooks
from src.logging.execution_logger import ExecutionLogger


# Global state tracking for hooks
hook_call_tracker = {
    "PreToolUse": [],
    "PostToolUse": [],
    "SessionStart": [],
    "SessionEnd": [],
    "Stop": []
}

# File-based detection
hook_detection_files = {}

# Database detection
db_logger = None


def setup_detection_files():
    """Create temporary files for hook detection."""
    global hook_detection_files
    for hook_type in ["PreToolUse", "PostToolUse", "SessionStart", "SessionEnd", "Stop"]:
        fd, path = tempfile.mkstemp(suffix=f"_{hook_type}.txt", prefix="hook_detection_")
        os.close(fd)
        hook_detection_files[hook_type] = Path(path)
    return hook_detection_files


def cleanup_detection_files():
    """Clean up temporary detection files."""
    for path in hook_detection_files.values():
        if path.exists():
            path.unlink()


def create_detection_wrapper(original_func, hook_name: str):
    """Create a wrapper that uses multiple detection methods."""
    async def wrapper(input_data: Dict[str, Any], tool_use_id: Optional[str], context: Any) -> Dict[str, Any]:
        # Method 1: Print statement
        print(f'🔧 [HOOK DETECTED] {hook_name} called!', file=sys.stderr, flush=True)
        
        # Method 2: File-based logging
        if hook_name in hook_detection_files:
            with open(hook_detection_files[hook_name], 'a') as f:
                f.write(f"{time.time()}: {hook_name} called\n")
                f.write(f"  Input data keys: {list(input_data.keys()) if isinstance(input_data, dict) else 'not dict'}\n")
                f.write(f"  Tool use ID: {tool_use_id}\n")
                f.flush()
        
        # Method 3: Global state tracking
        hook_call_tracker[hook_name].append({
            "timestamp": time.time(),
            "input_data_keys": list(input_data.keys()) if isinstance(input_data, dict) else None,
            "tool_use_id": tool_use_id
        })
        
        # Method 4: Database write (if logger available)
        if db_logger:
            try:
                session_id = input_data.get("session_id", "test-session")
                tool_name = input_data.get("tool_name", None)
                db_logger.log_execution(
                    session_id=session_id,
                    hook_event=hook_name,
                    tool_name=tool_name,
                    metadata={"detection_test": True, "hook_fired": True}
                )
            except Exception as e:
                print(f"⚠️  Database write failed: {e}", file=sys.stderr)
        
        # Method 5: Exception-based (optional - only for testing)
        # Uncomment to raise exception and verify hook is called
        # if hook_name == "PreToolUse":
        #     raise Exception(f"Hook detection test exception for {hook_name}")
        
        # Call original function
        try:
            result = await original_func(input_data, tool_use_id, context)
            return result
        except Exception as e:
            print(f'❌ [HOOK ERROR] {hook_name} error: {e}', file=sys.stderr, flush=True)
            return {}
    
    return wrapper


async def test_hook_execution_with_tool(timeout: int = 60) -> Dict[str, Any]:
    """Test hook execution with a tool-using query."""
    print("=" * 60)
    print("Hook Detection Test: Tool-Using Query")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "hook_execution_with_tool",
        "hooks_tested": ["PreToolUse", "PostToolUse", "SessionStart", "SessionEnd"],
        "detection_methods": {
            "print_statements": False,
            "file_logging": False,
            "global_state": False,
            "database_writes": False
        },
        "hook_calls": {}
    }
    
    # Setup detection
    setup_detection_files()
    
    # Wrap hooks with detection
    wrapped_hooks = {
        "PreToolUse": [HookMatcher(hooks=[create_detection_wrapper(
            documentation_hooks.pre_tool_use_logger, "PreToolUse"
        )])],
        "PostToolUse": [HookMatcher(hooks=[create_detection_wrapper(
            documentation_hooks.post_tool_use_logger, "PostToolUse"
        )])],
        "SessionStart": [HookMatcher(hooks=[create_detection_wrapper(
            documentation_hooks.session_start_logger, "SessionStart"
        )])],
        "SessionEnd": [HookMatcher(hooks=[create_detection_wrapper(
            documentation_hooks.session_end_logger, "SessionEnd"
        )])],
    }
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
        hooks=wrapped_hooks,
    )
    
    test_prompt = "Please read the file 'main.py' and tell me what it contains."
    
    print(f"Query: {test_prompt}")
    print()
    print("Monitoring for hook calls...")
    print("-" * 60)
    
    try:
        async for message in query(prompt=test_prompt, options=options):
            # Just collect messages, hooks should fire if they work
            pass
        
        print()
        print("-" * 60)
        print()
        
        # Check detection methods
        print("Checking detection methods...")
        print()
        
        # Method 1: Check print statements (already visible in stderr)
        results["detection_methods"]["print_statements"] = True  # We can't verify this programmatically
        
        # Method 2: Check file-based logging
        for hook_type, file_path in hook_detection_files.items():
            if file_path.exists() and file_path.stat().st_size > 0:
                results["detection_methods"]["file_logging"] = True
                with open(file_path) as f:
                    content = f.read()
                    results["hook_calls"][hook_type] = {
                        "file_detected": True,
                        "file_content": content[:500]  # First 500 chars
                    }
                print(f"✓ {hook_type}: File detection - {file_path.stat().st_size} bytes")
            else:
                results["hook_calls"][hook_type] = {"file_detected": False}
                print(f"✗ {hook_type}: File detection - No file or empty")
        
        # Method 3: Check global state
        for hook_type, calls in hook_call_tracker.items():
            if calls:
                results["detection_methods"]["global_state"] = True
                results["hook_calls"][hook_type]["global_state_detected"] = True
                results["hook_calls"][hook_type]["call_count"] = len(calls)
                print(f"✓ {hook_type}: Global state - {len(calls)} call(s)")
            else:
                if hook_type not in results["hook_calls"]:
                    results["hook_calls"][hook_type] = {}
                results["hook_calls"][hook_type]["global_state_detected"] = False
                print(f"✗ {hook_type}: Global state - No calls")
        
        # Method 4: Check database writes
        if db_logger:
            try:
                # Query database for detection test entries
                test_entries = db_logger.get_user_executions(
                    user_email="test-hook-detection@example.com",
                    limit=100
                )
                detection_entries = [
                    e for e in test_entries
                    if e.get("hook_event") in ["PreToolUse", "PostToolUse", "SessionStart", "SessionEnd"]
                ]
                if detection_entries:
                    results["detection_methods"]["database_writes"] = True
                    results["hook_calls"]["database_entries"] = len(detection_entries)
                    print(f"✓ Database writes: {len(detection_entries)} entries")
                else:
                    print("✗ Database writes: No entries found")
            except Exception as e:
                print(f"⚠️  Database check error: {e}")
        
    except Exception as e:
        print(f"\n✗ Error during test: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()
    
    finally:
        cleanup_detection_files()
    
    # Summary
    print()
    print("=" * 60)
    print("Detection Summary")
    print("=" * 60)
    
    hooks_fired = any(
        results["hook_calls"].get(hook_type, {}).get("file_detected", False) or
        results["hook_calls"].get(hook_type, {}).get("global_state_detected", False)
        for hook_type in ["PreToolUse", "PostToolUse", "SessionStart", "SessionEnd"]
    )
    
    if hooks_fired:
        print("✅ HOOKS ARE FIRING with Vertex AI")
        results["hooks_work"] = True
    else:
        print("❌ HOOKS ARE NOT FIRING with Vertex AI")
        results["hooks_work"] = False
    
    return results


async def test_hook_execution_simple_query(timeout: int = 60) -> Dict[str, Any]:
    """Test hook execution with a simple query (no tools)."""
    print("=" * 60)
    print("Hook Detection Test: Simple Query (No Tools)")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "hook_execution_simple_query",
        "hooks_tested": ["SessionStart", "SessionEnd"],
        "hook_calls": {}
    }
    
    setup_detection_files()
    
    wrapped_hooks = {
        "SessionStart": [HookMatcher(hooks=[create_detection_wrapper(
            documentation_hooks.session_start_logger, "SessionStart"
        )])],
        "SessionEnd": [HookMatcher(hooks=[create_detection_wrapper(
            documentation_hooks.session_end_logger, "SessionEnd"
        )])],
    }
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
        hooks=wrapped_hooks,
    )
    
    test_prompt = "Hello! Just say 'Hello back!'"
    
    print(f"Query: {test_prompt}")
    print()
    print("Monitoring for hook calls...")
    print("-" * 60)
    
    try:
        async for message in query(prompt=test_prompt, options=options):
            pass
        
        # Check detection
        for hook_type in ["SessionStart", "SessionEnd"]:
            file_path = hook_detection_files.get(hook_type)
            if file_path and file_path.exists() and file_path.stat().st_size > 0:
                results["hook_calls"][hook_type] = {"detected": True}
                print(f"✓ {hook_type}: Detected")
            else:
                results["hook_calls"][hook_type] = {"detected": False}
                print(f"✗ {hook_type}: Not detected")
        
        if hook_call_tracker["SessionStart"] or hook_call_tracker["SessionEnd"]:
            results["hooks_work"] = True
        else:
            results["hooks_work"] = False
        
    except Exception as e:
        results["error"] = str(e)
        results["hooks_work"] = False
    
    finally:
        cleanup_detection_files()
    
    return results


async def run_all_hook_detection_tests():
    """Run all hook detection tests."""
    global db_logger
    
    print("\n" + "=" * 60)
    print("Comprehensive Hook Detection Test Suite")
    print("=" * 60)
    print()
    
    # Initialize database logger for detection
    db_logger = ExecutionLogger(
        db_path="logs/test_hook_detection.db",
        user_email="test-hook-detection@example.com"
    )
    
    all_results = []
    
    # Test 1: Simple query
    print("Test 1: Simple Query (SessionStart/SessionEnd)")
    print()
    result1 = await test_hook_execution_simple_query()
    all_results.append(result1)
    print()
    
    # Test 2: Tool-using query
    print("Test 2: Tool-Using Query (All Hooks)")
    print()
    result2 = await test_hook_execution_with_tool()
    all_results.append(result2)
    print()
    
    # Generate report
    print("=" * 60)
    print("Final Report")
    print("=" * 60)
    print()
    
    hooks_work = any(r.get("hooks_work", False) for r in all_results)
    
    if hooks_work:
        print("✅ CONCLUSION: Hooks ARE firing with Vertex AI")
    else:
        print("❌ CONCLUSION: Hooks are NOT firing with Vertex AI")
        print("   Recommendation: Use message-level logging fallback")
    
    print()
    
    # Save report
    report_path = project_root / "logs" / "test_results" / f"hook_validation_{int(time.time())}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "timestamp": time.time(),
        "vertex_ai_enabled": os.getenv("CLAUDE_CODE_USE_VERTEX") == "1",
        "sdk_version": "claude-agent-sdk",  # Could query package version
        "hooks_work": hooks_work,
        "test_results": all_results,
        "environment": {
            "CLAUDE_CODE_USE_VERTEX": os.getenv("CLAUDE_CODE_USE_VERTEX"),
            "ANTHROPIC_VERTEX_PROJECT_ID": os.getenv("ANTHROPIC_VERTEX_PROJECT_ID"),
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to: {report_path}")
    
    return hooks_work, report


if __name__ == "__main__":
    success, report = asyncio.run(run_all_hook_detection_tests())
    sys.exit(0 if success else 1)

