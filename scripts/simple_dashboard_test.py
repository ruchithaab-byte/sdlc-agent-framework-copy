#!/usr/bin/env python3
"""
Simple test to generate dashboard events without requiring Vertex AI.

This creates mock execution events directly in the database.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.logging.execution_logger import ExecutionLogger
import uuid

def create_test_events():
    """Create some test execution events."""
    logger = ExecutionLogger()
    session_id = str(uuid.uuid4())
    
    print("Creating test execution events...")
    print(f"Session ID: {session_id}")
    print()
    
    # Simulate a session with various events
    events = [
        {
            "hook_event": "SessionStart",
            "status": "success",
            "metadata": {"source": "test", "permission_mode": "default"}
        },
        {
            "hook_event": "PreToolUse",
            "tool_name": "Read",
            "status": "success",
            "input_data": {"path": "README.md"}
        },
        {
            "hook_event": "PostToolUse",
            "tool_name": "Read",
            "status": "success",
            "duration_ms": 45,
            "output_data": {"content": "Sample content"}
        },
        {
            "hook_event": "PreToolUse",
            "tool_name": "Write",
            "status": "success",
            "input_data": {"path": "test.txt", "content": "test"}
        },
        {
            "hook_event": "PostToolUse",
            "tool_name": "Write",
            "status": "success",
            "duration_ms": 120,
            "output_data": {"success": True}
        },
        {
            "hook_event": "PreToolUse",
            "tool_name": "Bash",
            "status": "success",
            "input_data": {"command": "ls -la"}
        },
        {
            "hook_event": "PostToolUse",
            "tool_name": "Bash",
            "status": "success",
            "duration_ms": 200,
            "output_data": {"exit_code": 0}
        },
        {
            "hook_event": "SessionEnd",
            "status": "success",
            "metadata": {"reason": "completed", "summary": {"total_events": 7}}
        }
    ]
    
    for i, event in enumerate(events, 1):
        logger.log_execution(
            session_id=session_id,
            hook_event=event["hook_event"],
            tool_name=event.get("tool_name"),
            status=event["status"],
            duration_ms=event.get("duration_ms"),
            input_data=event.get("input_data"),
            output_data=event.get("output_data"),
            metadata=event.get("metadata")
        )
        print(f"  [{i}] Created {event['hook_event']} event" + 
              (f" - Tool: {event.get('tool_name', 'N/A')}" if event.get('tool_name') else ""))
    
    print()
    print(f"✓ Created {len(events)} test events")
    print(f"✓ Events are now in the database and will appear in the dashboard")
    print()
    print("To view the dashboard:")
    print("1. Make sure the dashboard server is running:")
    print("   python3 main.py dashboard")
    print()
    print("2. Open the dashboard HTML file:")
    print(f"   file://{project_root}/src/dashboard/index.html")
    print()
    print("   Or start a simple HTTP server:")
    print(f"   cd {project_root}/src/dashboard")
    print("   python3 -m http.server 8000")
    print("   Then open: http://localhost:8000")
    
    return session_id

if __name__ == "__main__":
    create_test_events()

