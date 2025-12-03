#!/usr/bin/env python3
"""
Test script to demonstrate the dashboard functionality.

This script:
1. Starts the dashboard server in the background
2. Runs a simple agent test to generate execution events
3. Provides instructions for viewing the dashboard
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from claude_agent_sdk import query, ClaudeAgentOptions
from config.agent_config import PROJECT_ROOT


async def run_simple_agent_test():
    """Run a simple agent query to generate execution events."""
    print("=" * 60)
    print("Running Simple Agent Test")
    print("=" * 60)
    print()
    
    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        setting_sources=["user", "project"],
        allowed_tools=["Read", "Write"],  # Minimal tools for testing
    )
    
    # Simple test query that will trigger hooks
    test_prompt = "List the files in the current directory using a Read tool."
    
    print(f"Query: {test_prompt}")
    print()
    print("This will generate execution events that appear in the dashboard...")
    print()
    
    try:
        message_count = 0
        async for message in query(prompt=test_prompt, options=options):
            message_count += 1
            # Just count messages, don't print everything
            if message_count <= 3:  # Print first few messages
                print(f"  [{message_count}] Received message")
        
        print(f"\n✓ Test completed - Generated {message_count} messages")
        print("✓ Execution events should now be visible in the dashboard")
        return True
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def start_dashboard_server():
    """Start the dashboard server in the background."""
    print("=" * 60)
    print("Starting Dashboard Server")
    print("=" * 60)
    print()
    
    # Check if dashboard is already running
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8765))
        sock.close()
        if result == 0:
            print("⚠ Dashboard server is already running on port 8765")
            return None
    except:
        pass
    
    # Start dashboard server
    script_path = project_root / "main.py"
    process = subprocess.Popen(
        [sys.executable, str(script_path), "dashboard", "--port", "8765"],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait a moment for server to start
    time.sleep(2)
    
    # Check if process is still running
    if process.poll() is None:
        print("✓ Dashboard server started successfully")
        print(f"  Process ID: {process.pid}")
        print("  WebSocket: ws://localhost:8765")
        return process
    else:
        stdout, stderr = process.communicate()
        print("✗ Failed to start dashboard server")
        print(f"  Error: {stderr.decode() if stderr else 'Unknown error'}")
        return None


def main():
    """Main execution."""
    print("\n" + "=" * 60)
    print("Dashboard Test Script")
    print("=" * 60)
    print()
    
    # Step 1: Start dashboard server
    dashboard_process = start_dashboard_server()
    print()
    
    if dashboard_process is None and "already running" not in str(dashboard_process):
        print("⚠ Continuing without dashboard server...")
        print("  You can start it manually with: python main.py dashboard")
        print()
    
    # Step 2: Run agent test
    print("Running agent test to generate events...")
    print()
    success = asyncio.run(run_simple_agent_test())
    print()
    
    # Step 3: Instructions
    print("=" * 60)
    print("Next Steps")
    print("=" * 60)
    print()
    print("To view the dashboard:")
    print("1. Open the dashboard HTML file in your browser:")
    print(f"   file://{project_root}/src/dashboard/index.html")
    print()
    print("   Or use Python's HTTP server:")
    print(f"   cd {project_root}/src/dashboard")
    print("   python3 -m http.server 8000")
    print("   Then open: http://localhost:8000")
    print()
    print("2. The dashboard will:")
    print("   - Connect to ws://localhost:8765")
    print("   - Display execution events from the database")
    print("   - Show real-time updates as new events occur")
    print()
    
    if dashboard_process:
        print("Dashboard server is running in the background.")
        print(f"To stop it, run: kill {dashboard_process.pid}")
        print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

