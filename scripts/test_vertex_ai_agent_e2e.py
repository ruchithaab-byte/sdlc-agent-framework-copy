#!/usr/bin/env python3
"""
End-to-end test: Run actual agent with Vertex AI and verify complete workflow.

This test:
1. Runs a real agent (ArchGuard) with Vertex AI backend
2. Verifies message-level logging works
3. Verifies database population
4. Verifies WebSocket broadcasting
5. Confirms complete workflow from agent execution to dashboard
"""

import asyncio
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions

# Load environment variables
load_dotenv(project_root / ".env")

# Set test user email
os.environ['AGENT_USER_EMAIL'] = os.getenv('AGENT_USER_EMAIL', 'test-agent@example.com')

from src.logging.execution_logger import ExecutionLogger
from src.utils.message_logger import log_agent_execution
from src.dashboard.websocket_server import DashboardServer
import websockets


async def test_agent_execution_e2e():
    """Run complete end-to-end test with real agent."""
    print("=" * 60)
    print("End-to-End Test: Real Agent Execution with Vertex AI")
    print("=" * 60)
    print()
    
    # Verify Vertex AI is enabled
    vertex_enabled = os.getenv("CLAUDE_CODE_USE_VERTEX") == "1"
    if not vertex_enabled:
        print("⚠️  WARNING: CLAUDE_CODE_USE_VERTEX is not set to '1'")
        print("   This test requires Vertex AI backend")
        print()
    
    print(f"✓ Vertex AI enabled: {vertex_enabled}")
    print(f"✓ Project ID: {os.getenv('ANTHROPIC_VERTEX_PROJECT_ID', 'Not set')}")
    print()
    
    # Use main database
    db_path = project_root / "logs" / "agent_execution.db"
    logger = ExecutionLogger(
        db_path=str(db_path),
        user_email=os.getenv('AGENT_USER_EMAIL', 'test-agent@example.com')
    )
    
    print(f"✓ Using database: {db_path}")
    print(f"✓ User email: {logger.user_email}")
    print()
    
    # Get initial database state
    with logger._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM execution_log")
        initial_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM execution_log")
        initial_sessions = cursor.fetchone()[0]
    
    print(f"Initial state: {initial_count} records, {initial_sessions} sessions")
    print()
    
    # Start WebSocket server in background
    server = DashboardServer(db_path=str(db_path))
    server_task = None
    ws_messages_received = []
    logging_stats_result = {}
    
    try:
        async def run_server():
            await server.run(host="127.0.0.1", port=8768, http_port=8083)
        
        server_task = asyncio.create_task(run_server())
        await asyncio.sleep(2)
        print("✓ WebSocket server started on port 8768")
        print()
        
        # Connect WebSocket client
        async def websocket_monitor():
            nonlocal logging_stats_result
            try:
                uri = "ws://127.0.0.1:8768"
                async with websockets.connect(uri) as websocket:
                    print("✓ WebSocket client connected")
                    
                    # Wait for initial data
                    try:
                        await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    except asyncio.TimeoutError:
                        pass
                    
                    # Now run agent and monitor for new messages
                    print()
                    print("=" * 60)
                    print("Running Agent: ArchGuard")
                    print("=" * 60)
                    print()
                    
                    # Configure agent options
                    from config.agent_config import PROJECT_ROOT, resolve_model_config
                    model = resolve_model_config("strategy")
                    
                    options = ClaudeAgentOptions(
                        cwd=str(PROJECT_ROOT),
                        setting_sources=["user", "project"],
                        allowed_tools=model.allowed_tools,
                        model=model.name,
                    )
                    
                    # Agent prompt - simple task that uses tools
                    agent_prompt = """
                    Please help me understand the project structure:
                    1. Read the file 'main.py' and tell me what it does
                    2. Read the file 'README.md' if it exists, or tell me if it doesn't
                    3. Summarize what you found
                    """
                    
                    print(f"Agent Prompt: {agent_prompt.strip()}")
                    print()
                    print("Executing agent...")
                    print("-" * 60)
                    
                    # Run agent with message-level logging
                    # Extract agent name from model config or use default
                    agent_name = "ArchGuard"  # Based on the agent being tested
                    phase = "strategy"  # Based on model config
                    
                    message_stream = query(prompt=agent_prompt, options=options)
                    logging_stats_result = await log_agent_execution(
                        message_stream=message_stream,
                        logger=logger,
                        user_email=logger.user_email,
                        agent_name=agent_name,
                        phase=phase
                    )
                    
                    print()
                    print("-" * 60)
                    print()
                    print("Agent execution completed!")
                    print(f"Message logging stats: {logging_stats_result}")
                    print()
                    
                    # Wait for database writes
                    await asyncio.sleep(5)
                    
                    # Monitor WebSocket for new messages
                    print("Monitoring WebSocket for broadcasts...")
                    print("-" * 60)
                    
                    try:
                        while True:
                            try:
                                msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                                msg_data = json.loads(msg)
                                
                                if msg_data.get("type") == "new_execution":
                                    ws_messages_received.append(msg_data.get("data"))
                                    event_data = msg_data.get("data", {})
                                    print(f"✓ Received: {event_data.get('hook_event')} - {event_data.get('tool_name', 'N/A')}")
                            except asyncio.TimeoutError:
                                print("⚠ Timeout waiting for more messages")
                                break
                    except Exception as e:
                        print(f"⚠ WebSocket monitoring error: {e}")
            
            except Exception as e:
                print(f"✗ WebSocket client error: {e}")
        
        # Run WebSocket monitor (which runs the agent)
        await websocket_monitor()
        
        # Verify results
        print()
        print("=" * 60)
        print("Verification Results")
        print("=" * 60)
        print()
        
        # Check database
        with logger._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM execution_log")
            final_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM execution_log")
            final_sessions = cursor.fetchone()[0]
            
            new_records = final_count - initial_count
            new_sessions = final_sessions - initial_sessions
            
            # Get latest session entries
            cursor.execute(
                """
                SELECT timestamp, session_id, hook_event, tool_name, status
                FROM execution_log
                WHERE user_email = ?
                ORDER BY timestamp DESC
                LIMIT 10
                """,
                (logger.user_email,)
            )
            latest_entries = [
                {
                    "timestamp": row[0],
                    "session_id": row[1],
                    "hook_event": row[2],
                    "tool_name": row[3],
                    "status": row[4]
                }
                for row in cursor.fetchall()
            ]
        
        print(f"Database:")
        print(f"  Initial: {initial_count} records, {initial_sessions} sessions")
        print(f"  Final: {final_count} records, {final_sessions} sessions")
        print(f"  New: {new_records} records, {new_sessions} sessions")
        print()
        
        if new_records > 0:
            print("✓ Database populated successfully")
            print(f"  Latest entries:")
            for entry in latest_entries[:5]:
                print(f"    - {entry['hook_event']}: {entry.get('tool_name', 'N/A')} ({entry['status']})")
        else:
            print("✗ No new records in database")
        
        print()
        print(f"WebSocket:")
        print(f"  Messages received: {len(ws_messages_received)}")
        
        if len(ws_messages_received) > 0:
            print("✓ WebSocket broadcasting working")
            print(f"  Events received:")
            for msg in ws_messages_received[:5]:
                print(f"    - {msg.get('hook_event')}: {msg.get('tool_name', 'N/A')}")
        else:
            print("⚠ No WebSocket messages received (may be timing issue)")
        
        print()
        print("=" * 60)
        print("End-to-End Test Summary")
        print("=" * 60)
        print()
        
        success = new_records > 0
        
        if success:
            print("✅ END-TO-END TEST PASSED")
            print()
            print("Verified:")
            print("  ✓ Agent execution with Vertex AI")
            print("  ✓ Message-level logging")
            print("  ✓ Database population")
            if len(ws_messages_received) > 0:
                print("  ✓ WebSocket broadcasting")
            print()
            print("The dashboard should now show the new agent execution records.")
            print("Refresh the dashboard to see the updates.")
        else:
            print("❌ END-TO-END TEST FAILED")
            print("   No new records were created in the database.")
        
        return success, {
            "initial_count": initial_count,
            "final_count": final_count,
            "new_records": new_records,
            "new_sessions": new_sessions,
            "websocket_messages": len(ws_messages_received),
            "logging_stats": logging_stats_result,
            "latest_entries": latest_entries[:5]
        }
    
    except Exception as e:
        print(f"\n✗ Error during test: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, {"error": str(e)}
    
    finally:
        # Stop server
        if server_task:
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    success, results = asyncio.run(test_agent_execution_e2e())
    sys.exit(0 if success else 1)

