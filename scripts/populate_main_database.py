#!/usr/bin/env python3
"""
Populate the main database (logs/agent_execution.db) with test execution data.

This script runs a real agent execution that will write to the main database
that the dashboard reads from.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions

# Load environment variables
load_dotenv(project_root / ".env")

# Set user email for logging
os.environ['AGENT_USER_EMAIL'] = os.getenv('AGENT_USER_EMAIL', 'test@example.com')

from src.logging.execution_logger import ExecutionLogger
from src.utils.message_logger import log_agent_execution


async def populate_main_database():
    """Run agent execution that writes to main database."""
    print("=" * 60)
    print("Populating Main Database (logs/agent_execution.db)")
    print("=" * 60)
    print()
    
    # Use main database (default)
    logger = ExecutionLogger(
        db_path="logs/agent_execution.db",
        user_email=os.getenv('AGENT_USER_EMAIL', 'test@example.com')
    )
    
    print(f"Using database: {logger.db_path}")
    print(f"User email: {logger.user_email}")
    print()
    
    # Check if hooks work (they don't with Vertex AI)
    hooks_work = False
    try:
        hook_report_path = project_root / "logs" / "test_results"
        if hook_report_path.exists():
            hook_reports = list(hook_report_path.glob("hook_validation_*.json"))
            if hook_reports:
                import json
                latest_report = max(hook_reports, key=lambda p: p.stat().st_mtime)
                with open(latest_report) as f:
                    hook_report = json.load(f)
                    hooks_work = hook_report.get("hooks_work", False)
    except Exception:
        pass
    
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
        print("Using hooks for logging")
    else:
        print("Using message-level logging (hooks don't work with Vertex AI)")
    
    print()
    
    # Run multiple queries to generate more data
    queries = [
        "Read the file 'main.py' and tell me what it does.",
        "Create a test file called 'test_populate.txt' with content 'This is a test file for database population'.",
        "Read the file 'requirements.txt' and summarize the dependencies.",
    ]
    
    for i, test_prompt in enumerate(queries, 1):
        print(f"Query {i}/{len(queries)}: {test_prompt}")
        print("-" * 60)
        
        try:
            if hooks_work:
                async for message in query(prompt=test_prompt, options=options):
                    # Just collect messages, hooks will log
                    pass
                else:
                    message_stream = query(prompt=test_prompt, options=options)
                    stats = await log_agent_execution(
                        message_stream=message_stream,
                        logger=logger,
                        user_email=logger.user_email,
                        agent_name="TestAgent",
                        phase="test"
                    )
                    print(f"Logged: {stats['tool_uses_logged']} tool uses, {stats['tool_results_logged']} tool results")
            
            print("✓ Completed")
            print()
            
        except Exception as e:
            print(f"✗ Error: {e}")
            print()
    
    # Show final count
    import sqlite3
    with logger._connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM execution_log")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM execution_log")
        sessions = cursor.fetchone()[0]
    
    print("=" * 60)
    print(f"Database populated: {total} total records, {sessions} sessions")
    print("=" * 60)
    print()
    print("The dashboard should now show these new records.")
    print("Refresh the dashboard page to see the updates.")


if __name__ == "__main__":
    asyncio.run(populate_main_database())

