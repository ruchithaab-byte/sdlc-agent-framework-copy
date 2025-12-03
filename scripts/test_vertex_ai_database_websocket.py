#!/usr/bin/env python3
"""
Comprehensive test for database population and WebSocket broadcasting with Vertex AI.

Tests:
1. Database population (via hooks or message-level logging)
2. WebSocket broadcasting
3. End-to-end integration
"""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import websockets
from threading import Thread

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions

# Load environment variables
load_dotenv(project_root / ".env")

# Set test user email
os.environ['AGENT_USER_EMAIL'] = 'test-db-websocket@example.com'

from src.logging.execution_logger import ExecutionLogger
from src.utils.message_logger import log_agent_execution, MessageLogger
from src.dashboard.websocket_server import DashboardServer


def init_test_database(db_path: Path) -> None:
    """Initialize test database with required schema."""
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create execution_log table (simplified for testing - no foreign keys)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                repository_id INTEGER,
                hook_event TEXT NOT NULL,
                tool_name TEXT,
                agent_name TEXT,
                phase TEXT,
                status TEXT,
                duration_ms INTEGER,
                input_data TEXT,
                output_data TEXT,
                error_message TEXT,
                metadata TEXT
            )
        """)
        
        # Create tool_usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                repository_id INTEGER,
                tool_name TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                total_duration_ms INTEGER DEFAULT 0
            )
        """)
        
        # Create execution_artifacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_log_id INTEGER,
                artifact_type TEXT NOT NULL,
                artifact_url TEXT,
                identifier TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        conn.commit()
    finally:
        conn.close()


# Global flag to track if hooks work (from hook detection test)
HOOKS_WORK = None


def check_hooks_status() -> bool:
    """Check if hooks work by looking for hook detection report."""
    global HOOKS_WORK
    
    if HOOKS_WORK is not None:
        return HOOKS_WORK
    
    # Try to find latest hook detection report
    test_results_dir = project_root / "logs" / "test_results"
    if test_results_dir.exists():
        hook_reports = list(test_results_dir.glob("hook_validation_*.json"))
        if hook_reports:
            latest_report = max(hook_reports, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest_report) as f:
                    report = json.load(f)
                    HOOKS_WORK = report.get("hooks_work", False)
                    return HOOKS_WORK
            except Exception:
                pass
    
    # Default: assume hooks don't work (conservative approach)
    HOOKS_WORK = False
    return False


async def test_database_population(timeout: int = 90) -> tuple[bool, Dict[str, Any]]:
    """Test that execution logs are written to database."""
    print("=" * 60)
    print("Test: Database Population")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "database_population",
        "success": False,
        "hooks_used": False,
        "message_level_used": False,
        "rows_inserted": 0,
        "session_id": None,
        "tool_uses_logged": 0
    }
    
    # Create test database
    test_db_path = project_root / "logs" / "test_database_population.db"
    test_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing test database
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Initialize database schema
    init_test_database(test_db_path)
    
    # Initialize logger with test database
    logger = ExecutionLogger(
        db_path=str(test_db_path),
        user_email="test-db-websocket@example.com"
    )
    
    # Get initial row count
    try:
        with logger._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM execution_log")
            initial_count = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        # Table doesn't exist yet, will be created on first write
        initial_count = 0
    
    print(f"Initial database row count: {initial_count}")
    print()
    
    # Check if hooks work
    hooks_work = check_hooks_status()
    results["hooks_used"] = hooks_work
    
    options = ClaudeAgentOptions(
        cwd=str(project_root),
        setting_sources=["user", "project"],
        allowed_tools=["Read"],
    )
    
    # Add hooks if they work
    if hooks_work:
        from claude_agent_sdk import HookMatcher
        from src.hooks import documentation_hooks
        options.hooks = {
            "PreToolUse": [HookMatcher(hooks=[documentation_hooks.pre_tool_use_logger])],
            "PostToolUse": [HookMatcher(hooks=[documentation_hooks.post_tool_use_logger])],
            "SessionStart": [HookMatcher(hooks=[documentation_hooks.session_start_logger])],
            "SessionEnd": [HookMatcher(hooks=[documentation_hooks.session_end_logger])],
        }
        print("Using hooks for logging (hooks work with Vertex AI)")
    else:
        print("Using message-level logging (hooks don't work with Vertex AI)")
        results["message_level_used"] = True
    
    test_prompt = "Please read the file 'main.py' and tell me what it contains."
    
    print(f"Query: {test_prompt}")
    print()
    print("Executing and logging...")
    print("-" * 60)
    
    try:
        if hooks_work:
            # Hooks should automatically log
            async for message in query(prompt=test_prompt, options=options):
                # Just collect messages, hooks will log
                pass
        else:
            # Use message-level logging
            message_stream = query(prompt=test_prompt, options=options)
            stats = await log_agent_execution(
                message_stream=message_stream,
                logger=logger,
                user_email="test-db-websocket@example.com"
            )
            results["logging_stats"] = stats
        
        # Wait a bit for database writes to complete
        await asyncio.sleep(2)
        
        # Verify database writes
        with logger._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM execution_log")
            final_count = cursor.fetchone()[0]
            
            results["rows_inserted"] = final_count - initial_count
            
            # Get session_id from first entry
            cursor.execute(
                "SELECT session_id FROM execution_log ORDER BY timestamp DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                results["session_id"] = row[0]
            
            # Count tool uses
            cursor.execute(
                "SELECT COUNT(*) FROM execution_log WHERE hook_event IN ('PreToolUse', 'PostToolUse')"
            )
            results["tool_uses_logged"] = cursor.fetchone()[0]
            
            # Get all entries for verification
            cursor.execute(
                """
                SELECT hook_event, tool_name, status, session_id
                FROM execution_log
                ORDER BY timestamp ASC
                """
            )
            entries = cursor.fetchall()
            results["entries"] = [
                {
                    "hook_event": row[0],
                    "tool_name": row[1],
                    "status": row[2],
                    "session_id": row[3]
                }
                for row in entries
            ]
        
        print()
        print("-" * 60)
        print()
        print(f"Final database row count: {final_count}")
        print(f"Rows inserted: {results['rows_inserted']}")
        print(f"Tool uses logged: {results['tool_uses_logged']}")
        print(f"Session ID: {results['session_id']}")
        print()
        
        if results["rows_inserted"] > 0:
            print("✓ Database population successful")
            results["success"] = True
            
            # Verify entries
            print("\nLogged entries:")
            for entry in results["entries"]:
                print(f"  - {entry['hook_event']}: {entry.get('tool_name', 'N/A')}")
        else:
            print("✗ No rows inserted into database")
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()
    
    finally:
        # Clean up test database (optional - keep for inspection)
        # if test_db_path.exists():
        #     test_db_path.unlink()
        pass
    
    return results["success"], results


async def test_websocket_broadcasting(timeout: int = 120) -> tuple[bool, Dict[str, Any]]:
    """Test that new database entries are broadcast via WebSocket."""
    print("=" * 60)
    print("Test: WebSocket Broadcasting")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "websocket_broadcasting",
        "success": False,
        "server_started": False,
        "client_connected": False,
        "messages_received": 0,
        "execution_messages": []
    }
    
    # Create test database
    test_db_path = project_root / "logs" / "test_websocket.db"
    test_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Initialize database schema
    init_test_database(test_db_path)
    
    # Start WebSocket server in background
    server = DashboardServer(db_path=str(test_db_path))
    server_task = None
    server_running = False
    
    try:
        # Start server
        async def run_server():
            nonlocal server_running
            try:
                server_running = True
                await server.run(host="127.0.0.1", port=8766, http_port=8081)  # Use different ports
            except Exception as e:
                print(f"Server error: {e}")
        
        server_task = asyncio.create_task(run_server())
        await asyncio.sleep(2)  # Wait for server to start
        results["server_started"] = True
        print("✓ WebSocket server started")
        
        # Connect WebSocket client
        messages_received = []
        
        async def websocket_client():
            try:
                uri = "ws://127.0.0.1:8766"
                async with websockets.connect(uri) as websocket:
                    results["client_connected"] = True
                    print("✓ WebSocket client connected")
                    
                    # Wait for initial data
                    try:
                        initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        initial_data = json.loads(initial_msg)
                        if initial_data.get("type") == "initial_data":
                            print(f"✓ Received initial data: {len(initial_data.get('executions', []))} executions")
                    except asyncio.TimeoutError:
                        print("⚠ No initial data received (this is OK)")
                    
                    # Now execute agent query and monitor for new messages
                    logger = ExecutionLogger(
                        db_path=str(test_db_path),
                        user_email="test-db-websocket@example.com"
                    )
                    
                    hooks_work = check_hooks_status()
                    
                    options = ClaudeAgentOptions(
                        cwd=str(project_root),
                        setting_sources=["user", "project"],
                        allowed_tools=["Read"],
                    )
                    
                    if hooks_work:
                        from claude_agent_sdk import HookMatcher
                        from src.hooks import documentation_hooks
                        options.hooks = {
                            "PreToolUse": [HookMatcher(hooks=[documentation_hooks.pre_tool_use_logger])],
                            "PostToolUse": [HookMatcher(hooks=[documentation_hooks.post_tool_use_logger])],
                        }
                    
                    test_prompt = "Please read the file 'main.py' and summarize it in one sentence."
                    
                    print(f"\nExecuting query: {test_prompt}")
                    print("Monitoring WebSocket for broadcasts...")
                    print("-" * 60)
                    
                    # Execute query
                    if hooks_work:
                        async for message in query(prompt=test_prompt, options=options):
                            pass
                    else:
                        message_stream = query(prompt=test_prompt, options=options)
                        await log_agent_execution(
                            message_stream=message_stream,
                            logger=logger,
                            user_email="test-db-websocket@example.com"
                        )
                    
                    # Wait for database writes
                    await asyncio.sleep(3)
                    
                    # Monitor WebSocket for new messages (with timeout)
                    print("\nWaiting for WebSocket broadcasts...")
                    try:
                        while True:
                            try:
                                msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                                msg_data = json.loads(msg)
                                
                                if msg_data.get("type") == "new_execution":
                                    messages_received.append(msg_data.get("data"))
                                    print(f"✓ Received execution event: {msg_data['data'].get('hook_event')} - {msg_data['data'].get('tool_name', 'N/A')}")
                            except asyncio.TimeoutError:
                                print("⚠ Timeout waiting for more messages")
                                break
                    except Exception as e:
                        print(f"⚠ Error receiving messages: {e}")
            
            except Exception as e:
                print(f"✗ WebSocket client error: {e}")
                results["error"] = str(e)
        
        # Run client
        await websocket_client()
        
        results["messages_received"] = len(messages_received)
        results["execution_messages"] = messages_received
        
        print()
        print("-" * 60)
        print()
        print(f"Messages received: {results['messages_received']}")
        
        if results["messages_received"] > 0:
            print("✓ WebSocket broadcasting successful")
            results["success"] = True
            
            # Verify message structure
            for msg in messages_received:
                required_fields = ["timestamp", "session_id", "hook_event"]
                missing = [f for f in required_fields if f not in msg]
                if missing:
                    print(f"⚠ Missing fields in message: {missing}")
        else:
            print("✗ No WebSocket messages received")
    
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()
    
    finally:
        # Stop server
        if server_task:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
    
    return results["success"], results


async def test_end_to_end_integration(timeout: int = 120) -> tuple[bool, Dict[str, Any]]:
    """Test complete workflow from agent execution to dashboard."""
    print("=" * 60)
    print("Test: End-to-End Integration")
    print("=" * 60)
    print()
    
    results = {
        "test_name": "end_to_end_integration",
        "success": False,
        "database_populated": False,
        "websocket_broadcast": False,
        "data_consistency": False
    }
    
    # Use same database for both database and websocket tests
    test_db_path = project_root / "logs" / "test_e2e.db"
    test_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Initialize database schema
    init_test_database(test_db_path)
    
    # Start server
    server = DashboardServer(db_path=str(test_db_path))
    server_task = None
    
    try:
        async def run_server():
            await server.run(host="127.0.0.1", port=8767, http_port=8082)
        
        server_task = asyncio.create_task(run_server())
        await asyncio.sleep(2)
        print("✓ WebSocket server started")
        
        # Connect client and execute
        db_entries_result = []
        ws_messages_result = []
        
        async def run_test():
            nonlocal db_entries_result, ws_messages_result
            
            # Connect WebSocket
            uri = "ws://127.0.0.1:8767"
            async with websockets.connect(uri) as websocket:
                print("✓ WebSocket client connected")
                
                # Wait for initial data
                try:
                    await asyncio.wait_for(websocket.recv(), timeout=5.0)
                except asyncio.TimeoutError:
                    pass
                
                # Initialize logger
                logger = ExecutionLogger(
                    db_path=str(test_db_path),
                    user_email="test-db-websocket@example.com"
                )
                
                hooks_work = check_hooks_status()
                
                options = ClaudeAgentOptions(
                    cwd=str(project_root),
                    setting_sources=["user", "project"],
                    allowed_tools=["Read", "Write"],
                )
                
                if hooks_work:
                    from claude_agent_sdk import HookMatcher
                    from src.hooks import documentation_hooks
                    options.hooks = {
                        "PreToolUse": [HookMatcher(hooks=[documentation_hooks.pre_tool_use_logger])],
                        "PostToolUse": [HookMatcher(hooks=[documentation_hooks.post_tool_use_logger])],
                        "SessionStart": [HookMatcher(hooks=[documentation_hooks.session_start_logger])],
                        "SessionEnd": [HookMatcher(hooks=[documentation_hooks.session_end_logger])],
                    }
                
                # Execute query with multiple tool uses
                test_prompt = "Read the file 'main.py', then create a test file called 'e2e_test.txt' with content 'End-to-end test'."
                
                print(f"\nExecuting: {test_prompt}")
                print("-" * 60)
                
                if hooks_work:
                    async for message in query(prompt=test_prompt, options=options):
                        pass
                else:
                    message_stream = query(prompt=test_prompt, options=options)
                    logging_stats = await log_agent_execution(
                        message_stream=message_stream,
                        logger=logger,
                        user_email="test-db-websocket@example.com"
                    )
                    print(f"Message logging stats: {logging_stats}")
                
                # Wait for processing and database writes
                await asyncio.sleep(10)  # Give more time for database writes
                
                # Get database entries - retry if empty
                max_retries = 5
                db_entries_local = []
                for retry in range(max_retries):
                    try:
                        # Use direct connection to ensure we're reading the same database
                        import sqlite3
                        conn = sqlite3.connect(str(test_db_path), timeout=10.0)
                        conn.execute("PRAGMA journal_mode=WAL")
                        cursor = conn.cursor()
                        
                        # First check if table exists and has any rows
                        cursor.execute("SELECT COUNT(*) FROM execution_log")
                        total_count = cursor.fetchone()[0]
                        print(f"  Database check (retry {retry + 1}): {total_count} total rows")
                        
                        cursor.execute(
                            """
                            SELECT timestamp, session_id, hook_event, tool_name, status
                            FROM execution_log
                            WHERE user_email = ?
                            ORDER BY timestamp ASC
                            """,
                            ("test-db-websocket@example.com",)
                        )
                        db_entries_local = [
                            {
                                "timestamp": row[0],
                                "session_id": row[1],
                                "hook_event": row[2],
                                "tool_name": row[3],
                                "status": row[4]
                            }
                            for row in cursor.fetchall()
                        ]
                        conn.close()
                        
                        print(f"  Found {len(db_entries_local)} entries for test user")
                    except Exception as e:
                        print(f"⚠️  Database query error (retry {retry + 1}): {e}")
                        import traceback
                        print(traceback.format_exc())
                    
                    if db_entries_local:
                        break
                    elif retry < max_retries - 1:
                        await asyncio.sleep(3)  # Wait and retry
                
                db_entries_result = db_entries_local
                
                # Collect WebSocket messages
                try:
                    while True:
                        try:
                            msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            msg_data = json.loads(msg)
                            if msg_data.get("type") == "new_execution":
                                ws_messages_result.append(msg_data.get("data"))
                        except asyncio.TimeoutError:
                            break
                except Exception:
                    pass
        
        await run_test()
        
        db_entries = db_entries_result
        ws_messages = ws_messages_result
        
        # Verify results
        print()
        print("-" * 60)
        print()
        
        results["database_entries"] = len(db_entries)
        results["websocket_messages"] = len(ws_messages)
        
        print(f"Database entries: {results['database_entries']}")
        print(f"WebSocket messages: {results['websocket_messages']}")
        print()
        
        if results["database_entries"] > 0:
            results["database_populated"] = True
            print("✓ Database populated")
        else:
            print("✗ Database not populated")
        
        if results["websocket_messages"] > 0:
            results["websocket_broadcast"] = True
            print("✓ WebSocket broadcasting working")
        else:
            print("✗ WebSocket broadcasting not working")
        
        # Check data consistency
        if results["database_entries"] > 0 and results["websocket_messages"] > 0:
            # Compare session_ids
            db_session_ids = set(e["session_id"] for e in db_entries if e["session_id"])
            ws_session_ids = set(m.get("session_id") for m in ws_messages if m.get("session_id"))
            
            if db_session_ids and ws_session_ids and db_session_ids.intersection(ws_session_ids):
                results["data_consistency"] = True
                print("✓ Data consistency verified")
            else:
                print("⚠ Data consistency issue (session_ids don't match)")
        
        results["success"] = (
            results["database_populated"] and
            results["websocket_broadcast"] and
            results["data_consistency"]
        )
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        results["error"] = str(e)
    
    finally:
        if server_task:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
    
    return results["success"], results


async def run_all_database_websocket_tests():
    """Run all database and WebSocket tests."""
    print("\n" + "=" * 60)
    print("Database and WebSocket Test Suite")
    print("=" * 60)
    print()
    
    # Check hooks status
    hooks_work = check_hooks_status()
    print(f"Hooks status: {'Working' if hooks_work else 'Not working (using message-level fallback)'}")
    print()
    
    all_results = []
    
    # Test 1: Database population
    success1, results1 = await test_database_population()
    all_results.append(results1)
    print()
    
    # Test 2: WebSocket broadcasting
    success2, results2 = await test_websocket_broadcasting()
    all_results.append(results2)
    print()
    
    # Test 3: End-to-end integration
    success3, results3 = await test_end_to_end_integration()
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
        "hooks_work": hooks_work,
        "results": all_results
    }


if __name__ == "__main__":
    success, results = asyncio.run(run_all_database_websocket_tests())
    sys.exit(0 if success else 1)

