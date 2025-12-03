#!/usr/bin/env python3
"""
Stream management tests for hooks with Vertex AI.

Tests if keeping streams open enables hooks to fire, based on the pattern
from GitHub issue #4775 where keeping stdin open fixed callback issues.
"""

import asyncio
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncIterator

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

# Load environment variables
load_dotenv(project_root / ".env")

# Set test user email
os.environ['AGENT_USER_EMAIL'] = 'test-stream-management@example.com'

from src.hooks import documentation_hooks
from src.utils.stream_monitor import StreamMonitor, StreamKeepAlive


# Global hook execution tracker
hook_execution_tracker = {
    "PreToolUse": [],
    "PostToolUse": [],
    "SessionStart": [],
    "SessionEnd": []
}


def create_monitored_hook_wrapper(original_func, hook_name: str, monitor: StreamMonitor):
    """Create a hook wrapper that monitors execution and stream state."""
    async def wrapper(input_data: Dict[str, Any], tool_use_id: Optional[str], context: Any) -> Dict[str, Any]:
        # Log hook attempt
        monitor.log_hook_event(hook_name, "attempted", {
            "tool_use_id": tool_use_id,
            "input_keys": list(input_data.keys()) if isinstance(input_data, dict) else None
        })
        
        # Check stream state
        stream_states = {}
        for stream_name in ["stdin", "stdout", "stderr", "query"]:
            stream_states[stream_name] = monitor.is_stream_open(stream_name)
        
        try:
            # Execute original hook
            result = await original_func(input_data, tool_use_id, context)
            
            # Log successful execution
            monitor.log_hook_event(hook_name, "executed", {
                "tool_use_id": tool_use_id,
                "stream_states": stream_states,
                "result": "success"
            })
            
            hook_execution_tracker[hook_name].append({
                "timestamp": time.time(),
                "tool_use_id": tool_use_id,
                "stream_states": stream_states
            })
            
            return result
        except Exception as e:
            monitor.log_hook_event(hook_name, "failed", {
                "tool_use_id": tool_use_id,
                "error": str(e),
                "stream_states": stream_states
            })
            return {}
    
    return wrapper


async def test_stream_lifecycle(timeout: int = 90) -> tuple[bool, Dict[str, Any]]:
    """Test 1: Monitor stream lifecycle and hook execution timing."""
    print("=" * 60)
    print("Test 1: Stream Lifecycle Monitoring")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "stream_lifecycle",
        "success": False,
        "stream_events": [],
        "hook_events": [],
        "message_events": [],
        "correlations": {}
    }
    
    monitor = StreamMonitor()
    
    # Create monitored hooks
    monitored_hooks = {
        "PreToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.pre_tool_use_logger, "PreToolUse", monitor
        )])],
        "PostToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.post_tool_use_logger, "PostToolUse", monitor
        )])],
        "SessionStart": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.session_start_logger, "SessionStart", monitor
        )])],
        "SessionEnd": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.session_end_logger, "SessionEnd", monitor
        )])],
    }
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
        hooks=monitored_hooks,
    )
    
    test_prompt = "Please read the file 'main.py' and tell me what it contains."
    
    print(f"Query: {test_prompt}")
    print()
    print("Monitoring stream lifecycle and hook execution...")
    print("-" * 60)
    
    try:
        # Monitor query start
        monitor.log_stream_event("query", "open", {"prompt": test_prompt[:50]})
        
        message_count = 0
        async for message in query(prompt=test_prompt, options=options):
            message_count += 1
            monitor.log_message_event("message_received", {
                "message_number": message_count,
                "message_type": type(message).__name__
            })
            
            # Check for tool-related messages
            msg_str = str(message)
            if "ToolUse" in msg_str or "tool_use" in msg_str.lower():
                monitor.log_message_event("tool_use_detected", {
                    "message_number": message_count
                })
            if "ToolResult" in msg_str or "tool_result" in msg_str.lower():
                monitor.log_message_event("tool_result_detected", {
                    "message_number": message_count
                })
        
        # Monitor query end
        monitor.log_stream_event("query", "close")
        
        # Wait a bit for any delayed hook calls
        await asyncio.sleep(2)
        
        # Get analysis
        timeline = monitor.get_timeline()
        correlation = monitor.get_correlation_analysis()
        
        results["stream_events"] = [e for e in timeline if e["type"] == "stream"]
        results["hook_events"] = [e for e in timeline if e["type"] == "hook"]
        results["message_events"] = [e for e in timeline if e["type"] == "message"]
        results["correlations"] = correlation
        
        print()
        print("-" * 60)
        print()
        print("Stream Events:", len(results["stream_events"]))
        print("Hook Events:", len(results["hook_events"]))
        print("Message Events:", len(results["message_events"]))
        print()
        
        # Analyze correlations
        hooks_executed = len([e for e in results["hook_events"] if e["event"] == "executed"])
        hooks_attempted = len([e for e in results["hook_events"] if e["event"] == "attempted"])
        
        print(f"Hooks attempted: {hooks_attempted}")
        print(f"Hooks executed: {hooks_executed}")
        print()
        
        if hooks_executed > 0:
            print("✓ Hooks are executing!")
            results["success"] = True
        else:
            print("✗ Hooks are not executing")
            if hooks_attempted > 0:
                print("  (Hooks were attempted but not executed)")
        
        # Print correlation analysis
        if correlation.get("correlations"):
            print()
            print("Correlation Analysis:")
            for corr in correlation["correlations"][:5]:
                print(f"  Hook: {corr['hook']}")
                print(f"    Time since stream close: {corr.get('time_since_close')}")
                print(f"    Time until stream open: {corr.get('time_until_open')}")
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()
    
    return results["success"], results


async def test_stream_keep_alive(timeout: int = 90) -> tuple[bool, Dict[str, Any]]:
    """Test 2: Test if keeping streams open manually enables hooks."""
    print("=" * 60)
    print("Test 2: Stream Keep-Alive Test")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "stream_keep_alive",
        "success": False,
        "hooks_executed": 0,
        "keep_alive_duration": 5.0
    }
    
    monitor = StreamMonitor()
    keep_alive = StreamKeepAlive(monitor, keep_alive_duration=5.0)
    
    # Create monitored hooks
    monitored_hooks = {
        "PreToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.pre_tool_use_logger, "PreToolUse", monitor
        )])],
        "PostToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.post_tool_use_logger, "PostToolUse", monitor
        )])],
        "SessionStart": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.session_start_logger, "SessionStart", monitor
        )])],
        "SessionEnd": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.session_end_logger, "SessionEnd", monitor
        )])],
    }
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
        hooks=monitored_hooks,
    )
    
    test_prompt = "Please read the file 'main.py' and summarize it."
    
    print(f"Query: {test_prompt}")
    print(f"Keep-alive duration: {results['keep_alive_duration']} seconds")
    print()
    print("Executing with stream keep-alive...")
    print("-" * 60)
    
    try:
        # Use keep-alive wrapper
        # Directly pass query with arguments
        wrapped_stream = keep_alive.wrap_query(
            query,
            prompt=test_prompt,
            options=options
        )
        
        message_count = 0
        async for message in wrapped_stream:
            message_count += 1
            monitor.log_message_event("message_received", {
                "message_number": message_count
            })
        
        # Wait for hook execution
        await asyncio.sleep(2)
        
        # Check results
        hooks_executed = len([e for e in monitor.hook_events if e["hook_type"] == "executed"])
        hooks_attempted = len([e for e in monitor.hook_events if e["hook_type"] == "attempted"])
        
        results["hooks_executed"] = hooks_executed
        results["hooks_attempted"] = hooks_attempted
        
        print()
        print("-" * 60)
        print()
        print(f"Hooks attempted: {hooks_attempted}")
        print(f"Hooks executed: {hooks_executed}")
        print()
        
        if hooks_executed > 0:
            print("✓ Keep-alive enabled hook execution!")
            results["success"] = True
        else:
            print("✗ Keep-alive did not enable hook execution")
            if hooks_attempted > 0:
                print("  (Hooks were attempted but not executed)")
        
        # Check keep-alive events
        keep_alive_events = [e for e in monitor.events if "keep_alive" in e.event_type]
        print(f"Keep-alive events: {len(keep_alive_events)}")
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    return results["success"], results


async def test_sdk_stream_inspection(timeout: int = 90) -> tuple[bool, Dict[str, Any]]:
    """Test 3: Inspect SDK internal stream handling."""
    print("=" * 60)
    print("Test 3: SDK Stream Inspection")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "sdk_stream_inspection",
        "success": False,
        "sdk_info": {},
        "stream_patches_applied": False
    }
    
    monitor = StreamMonitor()
    
    # Try to inspect SDK internals
    try:
        import claude_agent_sdk
        sdk_path = Path(claude_agent_sdk.__file__).parent
        results["sdk_info"]["path"] = str(sdk_path)
        results["sdk_info"]["version"] = getattr(claude_agent_sdk, "__version__", "unknown")
        
        # Check for subprocess_cli module
        try:
            from claude_agent_sdk._internal.transport import subprocess_cli
            results["sdk_info"]["subprocess_cli_found"] = True
            results["sdk_info"]["subprocess_cli_path"] = subprocess_cli.__file__
        except ImportError:
            results["sdk_info"]["subprocess_cli_found"] = False
        
        print("SDK Information:")
        print(f"  Path: {results['sdk_info']['path']}")
        print(f"  Version: {results['sdk_info']['version']}")
        print(f"  Subprocess CLI found: {results['sdk_info']['subprocess_cli_found']}")
        print()
        
    except Exception as e:
        results["sdk_info"]["error"] = str(e)
        print(f"⚠️  Could not inspect SDK: {e}")
        print()
    
    # Create monitored hooks
    monitored_hooks = {
        "PreToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.pre_tool_use_logger, "PreToolUse", monitor
        )])],
        "PostToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.post_tool_use_logger, "PostToolUse", monitor
        )])],
    }
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
        hooks=monitored_hooks,
    )
    
    test_prompt = "Read the file 'main.py'."
    
    print("Executing query to monitor SDK behavior...")
    print("-" * 60)
    
    try:
        monitor.log_stream_event("query", "open")
        
        message_count = 0
        async for message in query(prompt=test_prompt, options=options):
            message_count += 1
            monitor.log_message_event("message_received", {
                "message_number": message_count
            })
        
        monitor.log_stream_event("query", "close")
        
        await asyncio.sleep(2)
        
        hooks_executed = len([e for e in monitor.hook_events if e["hook_type"] == "executed"])
        results["hooks_executed"] = hooks_executed
        
        print()
        print("-" * 60)
        print()
        print(f"Hooks executed: {hooks_executed}")
        
        if hooks_executed > 0:
            print("✓ Hooks executed")
            results["success"] = True
        else:
            print("✗ Hooks did not execute")
        
        # Timeline analysis
        timeline = monitor.get_timeline()
        results["timeline_length"] = len(timeline)
        results["stream_events_count"] = len([e for e in timeline if e["type"] == "stream"])
        results["hook_events_count"] = len([e for e in timeline if e["type"] == "hook"])
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    return results["success"], results


async def test_message_hook_correlation(timeout: int = 90) -> tuple[bool, Dict[str, Any]]:
    """Test 4: Compare message stream timing with hook execution."""
    print("=" * 60)
    print("Test 4: Message-Hook Correlation")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "message_hook_correlation",
        "success": False,
        "correlations": []
    }
    
    monitor = StreamMonitor()
    
    # Create monitored hooks
    monitored_hooks = {
        "PreToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.pre_tool_use_logger, "PreToolUse", monitor
        )])],
        "PostToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.post_tool_use_logger, "PostToolUse", monitor
        )])],
        "SessionStart": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.session_start_logger, "SessionStart", monitor
        )])],
        "SessionEnd": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.session_end_logger, "SessionEnd", monitor
        )])],
    }
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
        hooks=monitored_hooks,
    )
    
    test_prompt = "Read the file 'main.py' and tell me what it does."
    
    print(f"Query: {test_prompt}")
    print()
    print("Tracking message and hook timing correlation...")
    print("-" * 60)
    
    try:
        monitor.log_stream_event("query", "open")
        
        message_times = []
        async for message in query(prompt=test_prompt, options=options):
            msg_time = time.time() - monitor.start_time
            message_times.append(msg_time)
            
            msg_str = str(message)
            if "ToolUse" in msg_str:
                monitor.log_message_event("tool_use_message", {
                    "timestamp": msg_time
                })
            if "ToolResult" in msg_str:
                monitor.log_message_event("tool_result_message", {
                    "timestamp": msg_time
                })
        
        monitor.log_stream_event("query", "close")
        
        await asyncio.sleep(2)
        
        # Correlate hook events with message events
        hook_times = [e["timestamp"] for e in monitor.hook_events if e["hook_type"] == "executed"]
        
        correlations = []
        for hook_time in hook_times:
            # Find closest message before hook
            messages_before = [t for t in message_times if t < hook_time]
            closest_message_before = max(messages_before) if messages_before else None
            
            # Find closest message after hook
            messages_after = [t for t in message_times if t > hook_time]
            closest_message_after = min(messages_after) if messages_after else None
            
            correlations.append({
                "hook_time": hook_time,
                "closest_message_before": closest_message_before,
                "closest_message_after": closest_message_after,
                "time_since_message": hook_time - closest_message_before if closest_message_before else None,
                "time_until_message": closest_message_after - hook_time if closest_message_after else None
            })
        
        results["correlations"] = correlations
        results["message_count"] = len(message_times)
        results["hook_count"] = len(hook_times)
        
        print()
        print("-" * 60)
        print()
        print(f"Messages received: {results['message_count']}")
        print(f"Hooks executed: {results['hook_count']}")
        print()
        
        if results["hook_count"] > 0:
            print("✓ Hooks executed - correlation analysis:")
            for corr in correlations[:3]:
                print(f"  Hook at {corr['hook_time']:.3f}s")
                if corr["closest_message_before"]:
                    print(f"    After message at {corr['closest_message_before']:.3f}s (gap: {corr['time_since_message']:.3f}s)")
            results["success"] = True
        else:
            print("✗ No hooks executed")
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    return results["success"], results


async def test_backend_comparison(timeout: int = 90) -> tuple[bool, Dict[str, Any]]:
    """Test 5: Compare stream behavior (Vertex AI only - no direct API available)."""
    print("=" * 60)
    print("Test 5: Backend Comparison (Vertex AI Only)")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "backend_comparison",
        "success": False,
        "note": "Direct Anthropic API not available - testing Vertex AI only",
        "vertex_ai_results": {}
    }
    
    # Verify Vertex AI is enabled
    vertex_enabled = os.getenv("CLAUDE_CODE_USE_VERTEX") == "1"
    
    if not vertex_enabled:
        print("⚠️  Vertex AI not enabled (CLAUDE_CODE_USE_VERTEX != 1)")
        print("   This test requires Vertex AI backend")
        results["error"] = "Vertex AI not enabled"
        return False, results
    
    print("✓ Vertex AI enabled")
    print("⚠️  Direct Anthropic API not available for comparison")
    print()
    
    monitor = StreamMonitor()
    
    # Create monitored hooks
    monitored_hooks = {
        "PreToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.pre_tool_use_logger, "PreToolUse", monitor
        )])],
        "PostToolUse": [HookMatcher(hooks=[create_monitored_hook_wrapper(
            documentation_hooks.post_tool_use_logger, "PostToolUse", monitor
        )])],
    }
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
        hooks=monitored_hooks,
    )
    
    test_prompt = "Read the file 'main.py'."
    
    print("Testing with Vertex AI backend...")
    print("-" * 60)
    
    try:
        monitor.log_stream_event("query", "open", {"backend": "vertex_ai"})
        
        message_count = 0
        async for message in query(prompt=test_prompt, options=options):
            message_count += 1
            monitor.log_message_event("message_received", {
                "message_number": message_count,
                "backend": "vertex_ai"
            })
        
        monitor.log_stream_event("query", "close", {"backend": "vertex_ai"})
        
        await asyncio.sleep(2)
        
        hooks_executed = len([e for e in monitor.hook_events if e["hook_type"] == "executed"])
        hooks_attempted = len([e for e in monitor.hook_events if e["hook_type"] == "attempted"])
        
        results["vertex_ai_results"] = {
            "hooks_executed": hooks_executed,
            "hooks_attempted": hooks_attempted,
            "messages_received": message_count,
            "stream_events": len([e for e in monitor.events])
        }
        
        print()
        print("-" * 60)
        print()
        print("Vertex AI Results:")
        print(f"  Hooks attempted: {hooks_attempted}")
        print(f"  Hooks executed: {hooks_executed}")
        print(f"  Messages received: {message_count}")
        print()
        
        if hooks_executed > 0:
            print("✓ Hooks executed with Vertex AI")
            results["success"] = True
        else:
            print("✗ Hooks did not execute with Vertex AI")
            if hooks_attempted > 0:
                print("  (Hooks were attempted but not executed)")
        
        print()
        print("Note: Cannot compare with direct API (not available)")
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    return results["success"], results


async def run_all_stream_management_tests():
    """Run all stream management tests."""
    print("\n" + "=" * 60)
    print("Stream Management Test Suite for Hooks with Vertex AI")
    print("=" * 60)
    print()
    
    all_results = []
    
    # Test 1: Stream Lifecycle
    success1, results1 = await test_stream_lifecycle()
    all_results.append(results1)
    print()
    
    # Test 2: Stream Keep-Alive
    success2, results2 = await test_stream_keep_alive()
    all_results.append(results2)
    print()
    
    # Test 3: SDK Inspection
    success3, results3 = await test_sdk_stream_inspection()
    all_results.append(results3)
    print()
    
    # Test 4: Message-Hook Correlation
    success4, results4 = await test_message_hook_correlation()
    all_results.append(results4)
    print()
    
    # Test 5: Backend Comparison (Vertex AI only)
    success5, results5 = await test_backend_comparison()
    all_results.append(results5)
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
    
    # Analysis
    print()
    print("=" * 60)
    print("Analysis")
    print("=" * 60)
    print()
    
    hooks_worked = any(r.get("hooks_executed", 0) > 0 for r in all_results)
    
    if hooks_worked:
        print("✅ Hooks ARE executing with stream management!")
        print("   Stream lifecycle management may enable hooks")
    else:
        print("❌ Hooks are NOT executing even with stream management")
        print("   Root cause may be different from stream lifecycle")
        print("   Consider alternative approaches")
    
    # Save report
    report_path = project_root / "logs" / "test_results" / f"stream_management_{int(time.time())}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "timestamp": time.time(),
        "vertex_ai_enabled": os.getenv("CLAUDE_CODE_USE_VERTEX") == "1",
        "hooks_worked": hooks_worked,
        "test_results": all_results
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print()
    print(f"Report saved to: {report_path}")
    
    overall_success = hooks_worked
    
    return overall_success, report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test stream management for hooks with Vertex AI")
    parser.add_argument("--test", choices=["lifecycle", "keep_alive", "inspection", "correlation", "backend", "all"],
                       default="all", help="Which test to run")
    
    args = parser.parse_args()
    
    if args.test == "lifecycle":
        success, results = asyncio.run(test_stream_lifecycle())
    elif args.test == "keep_alive":
        success, results = asyncio.run(test_stream_keep_alive())
    elif args.test == "inspection":
        success, results = asyncio.run(test_sdk_stream_inspection())
    elif args.test == "correlation":
        success, results = asyncio.run(test_message_hook_correlation())
    elif args.test == "backend":
        success, results = asyncio.run(test_backend_comparison())
    else:
        success, results = asyncio.run(run_all_stream_management_tests())
    
    sys.exit(0 if success else 1)

