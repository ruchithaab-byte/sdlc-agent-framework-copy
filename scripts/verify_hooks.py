#!/usr/bin/env python3
"""
Verify that hooks are working correctly by running a test agent execution
and checking if events are logged to the database.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.logging.execution_logger import ExecutionLogger
from src.hooks.documentation_hooks import (
    pre_tool_use_logger,
    post_tool_use_logger,
    session_start_logger,
    session_end_logger,
)


async def test_hooks():
    """Test that hooks can be called and log events."""
    print("🔍 Testing Hook Functions...")
    print("=" * 60)
    
    logger = ExecutionLogger()
    initial_count = logger.get_session_summary("test-session")["total_events"]
    
    # Test SessionStart hook
    print("\n1. Testing SessionStart hook...")
    await session_start_logger(
        {"session_id": "test-session", "source": "test"},
        None,
        None
    )
    
    # Test PreToolUse hook
    print("2. Testing PreToolUse hook...")
    await pre_tool_use_logger(
        {
            "session_id": "test-session",
            "tool_name": "Read",
            "tool_input": {"file_path": "test.txt"},
        },
        "test-tool-id-1",
        None
    )
    
    # Test PostToolUse hook
    print("3. Testing PostToolUse hook...")
    await post_tool_use_logger(
        {
            "session_id": "test-session",
            "tool_name": "Read",
            "tool_response": {"success": True, "content": "test"},
        },
        "test-tool-id-1",
        None
    )
    
    # Test SessionEnd hook
    print("4. Testing SessionEnd hook...")
    await session_end_logger(
        {"session_id": "test-session", "reason": "test complete"},
        None,
        None
    )
    
    # Verify events were logged
    summary = logger.get_session_summary("test-session")
    new_count = summary["total_events"]
    events_added = new_count - initial_count
    
    print("\n" + "=" * 60)
    print(f"✅ Hooks executed successfully!")
    print(f"📊 Events logged: {events_added}")
    print(f"📈 Session summary: {summary}")
    
    if events_added >= 4:
        print("\n✅ ALL HOOKS WORKING CORRECTLY!")
        return True
    else:
        print(f"\n❌ Expected at least 4 events, got {events_added}")
        return False


def check_database():
    """Check database for recent events."""
    print("\n🔍 Checking Database...")
    print("=" * 60)
    
    import sqlite3
    db_path = project_root / "logs" / "agent_execution.db"
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM execution_log")
        total = cursor.fetchone()[0]
        print(f"📊 Total events in database: {total}")
        
        # Get recent events
        cursor.execute("""
            SELECT timestamp, session_id, hook_event, tool_name, status
            FROM execution_log
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        
        if rows:
            print(f"\n📋 Recent events (last 10):")
            for row in rows:
                print(f"  - {row[0][:19]} | {row[2]:15} | {row[3] or 'N/A':10} | {row[4]}")
        else:
            print("⚠️  No events found in database")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False


def check_websocket_server():
    """Check if WebSocket server is running."""
    print("\n🔍 Checking WebSocket Server...")
    print("=" * 60)
    
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8765))
        sock.close()
        
        if result == 0:
            print("✅ WebSocket server is running on port 8765")
            return True
        else:
            print("❌ WebSocket server is NOT running on port 8765")
            return False
    except Exception as e:
        print(f"❌ Error checking WebSocket server: {e}")
        return False


def check_http_server():
    """Check if HTTP server is running."""
    print("\n🔍 Checking HTTP Server...")
    print("=" * 60)
    
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print("✅ HTTP server is running on port 8000")
            return True
        else:
            print("❌ HTTP server is NOT running on port 8000")
            return False
    except Exception as e:
        print(f"❌ Error checking HTTP server: {e}")
        return False


async def main():
    """Run all verification checks."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🔍 HOOKS & WEBSOCKET VERIFICATION                           ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    results = []
    
    # Test hooks
    hooks_ok = await test_hooks()
    results.append(("Hooks", hooks_ok))
    
    # Check database
    db_ok = check_database()
    results.append(("Database", db_ok))
    
    # Check WebSocket server
    ws_ok = check_websocket_server()
    results.append(("WebSocket Server", ws_ok))
    
    # Check HTTP server
    http_ok = check_http_server()
    results.append(("HTTP Server", http_ok))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_ok = True
    for name, status in results:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}: {'PASS' if status else 'FAIL'}")
        if not status:
            all_ok = False
    
    print("=" * 60)
    
    if all_ok:
        print("\n🎉 ALL CHECKS PASSED! System is fully operational!")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

