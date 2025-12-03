#!/usr/bin/env python3
"""
Simple test script to generate dashboard events for testing.
This directly logs events to the database without running a full agent.
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.logging.execution_logger import ExecutionLogger


async def generate_test_events():
    """Generate test events for dashboard testing."""
    print("🚀 Generating test events for dashboard...")
    print("=" * 60)
    
    # Get user email from config or use default
    from config.agent_config import get_user_email
    user_email = get_user_email() or "test@example.com"
    
    # Create logger
    logger = ExecutionLogger(db_path="logs/agent_execution.db")
    
    # Generate a session ID
    session_id = str(uuid4())
    print(f"📊 Session ID: {session_id}")
    print(f"👤 User: {user_email}")
    print()
    
    # Simulate agent execution events
    events = [
        ("SessionStart", None, "ProductSpec", "planning", "success", 0),
        ("PreToolUse", "Read", "ProductSpec", "planning", "success", 0),
        ("PostToolUse", "Read", "ProductSpec", "planning", "success", 45),
        ("PreToolUse", "Write", "ProductSpec", "planning", "success", 0),
        ("PostToolUse", "Write", "ProductSpec", "planning", "success", 120),
        ("PreToolUse", "Bash", "ProductSpec", "execution", "success", 0),
        ("PostToolUse", "Bash", "ProductSpec", "execution", "success", 250),
        ("PreToolUse", "Read", "ProductSpec", "review", "success", 0),
        ("PostToolUse", "Read", "ProductSpec", "review", "success", 30),
        ("SessionEnd", None, "ProductSpec", "completed", "success", 0),
    ]
    
    print("📝 Logging events:")
    for i, (event_type, tool_name, agent_name, phase, status, duration) in enumerate(events, 1):
        logger.log_execution(
            session_id=session_id,
            hook_event=event_type,
            tool_name=tool_name,
            agent_name=agent_name,
            phase=phase,
            status=status,
            duration_ms=duration,
        )
        print(f"  {i}. [{event_type}] {tool_name or 'N/A'} - {agent_name} - {phase} - {status} ({duration}ms)")
        # Small delay to simulate real execution
        await asyncio.sleep(0.1)
    
    print()
    print("=" * 60)
    print("✅ Test events generated successfully!")
    print(f"📊 Check dashboard at http://localhost:3000")
    print(f"🔍 Session ID: {session_id}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(generate_test_events())

