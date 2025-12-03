#!/usr/bin/env python3
"""
Database migration script for multi-user dashboard with authentication.

This script creates a clean slate database schema with:
- User authentication (email/password)
- Repository tracking
- Execution sessions
- Artifact tracking (deployments, PRs, commits)
- Enhanced execution logging with user/repo context

Run this before using the enhanced dashboard system.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config.agent_config import PROJECT_ROOT


def migrate_database(db_path: str = "logs/agent_execution.db") -> None:
    """Migrate database to multi-user schema with authentication."""
    db_file = PROJECT_ROOT / db_path
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Migrating database: {db_file}")
    print("This will drop existing tables and create a new schema.")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Drop existing tables (clean slate)
        print("\nDropping existing tables...")
        tables_to_drop = [
            "execution_artifacts",
            "agent_performance",
            "tool_usage",
            "execution_log",
            "execution_sessions",
            "user_sessions",
            "repositories",
            "users",
        ]
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
        print("✓ Dropped existing tables")
        
        # Create users table
        print("\nCreating users table...")
        cursor.execute("""
            CREATE TABLE users (
                email TEXT PRIMARY KEY,
                display_name TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                last_login_at TEXT,
                is_active INTEGER DEFAULT 1,
                is_admin INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        print("✓ Created users table")
        
        # Create repositories table
        print("Creating repositories table...")
        cursor.execute("""
            CREATE TABLE repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_path TEXT UNIQUE NOT NULL,
                repo_name TEXT NOT NULL,
                git_remote_url TEXT,
                git_branch TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        print("✓ Created repositories table")
        
        # Create execution_sessions table
        print("Creating execution_sessions table...")
        cursor.execute("""
            CREATE TABLE execution_sessions (
                id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                repository_id INTEGER,
                session_name TEXT,
                agent_name TEXT,
                phase TEXT,
                status TEXT DEFAULT 'running',
                environment TEXT DEFAULT 'dev',
                version_tag TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                total_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                metadata TEXT,
                FOREIGN KEY (user_email) REFERENCES users(email),
                FOREIGN KEY (repository_id) REFERENCES repositories(id)
            )
        """)
        print("✓ Created execution_sessions table")
        
        # Create user_sessions table (for JWT token management)
        print("Creating user_sessions table...")
        cursor.execute("""
            CREATE TABLE user_sessions (
                id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_used_at TEXT,
                is_revoked INTEGER DEFAULT 0,
                FOREIGN KEY (user_email) REFERENCES users(email)
            )
        """)
        print("✓ Created user_sessions table")
        
        # Create enhanced execution_log table
        print("Creating execution_log table...")
        cursor.execute("""
            CREATE TABLE execution_log (
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
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES execution_sessions(id),
                FOREIGN KEY (user_email) REFERENCES users(email),
                FOREIGN KEY (repository_id) REFERENCES repositories(id)
            )
        """)
        print("✓ Created execution_log table")
        
        # Create enhanced tool_usage table
        print("Creating tool_usage table...")
        cursor.execute("""
            CREATE TABLE tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                repository_id INTEGER,
                tool_name TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                total_duration_ms INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES execution_sessions(id),
                FOREIGN KEY (user_email) REFERENCES users(email),
                FOREIGN KEY (repository_id) REFERENCES repositories(id)
            )
        """)
        print("✓ Created tool_usage table")
        
        # Create enhanced agent_performance table
        print("Creating agent_performance table...")
        cursor.execute("""
            CREATE TABLE agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                repository_id INTEGER,
                agent_name TEXT NOT NULL,
                phase TEXT NOT NULL,
                total_turns INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                success INTEGER DEFAULT 1,
                FOREIGN KEY (session_id) REFERENCES execution_sessions(id),
                FOREIGN KEY (user_email) REFERENCES users(email),
                FOREIGN KEY (repository_id) REFERENCES repositories(id)
            )
        """)
        print("✓ Created agent_performance table")
        
        # Create execution_artifacts table (NEW for SaaS tracking)
        print("Creating execution_artifacts table...")
        cursor.execute("""
            CREATE TABLE execution_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_log_id INTEGER NOT NULL,
                artifact_type TEXT NOT NULL,
                artifact_url TEXT,
                identifier TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (execution_log_id) REFERENCES execution_log(id)
            )
        """)
        print("✓ Created execution_artifacts table")
        
        # Create indexes for performance
        print("\nCreating indexes...")
        indexes = [
            ("idx_execution_log_user_email", "execution_log", "user_email"),
            ("idx_execution_log_session_id", "execution_log", "session_id"),
            ("idx_execution_log_timestamp", "execution_log", "timestamp"),
            ("idx_execution_log_repo_id", "execution_log", "repository_id"),
            ("idx_execution_log_timestamp_repo", "execution_log", "timestamp, repository_id"),
            ("idx_execution_log_timestamp_user", "execution_log", "timestamp, user_email"),
            ("idx_execution_sessions_user_email", "execution_sessions", "user_email"),
            ("idx_execution_sessions_status", "execution_sessions", "status"),
            ("idx_execution_sessions_repo_id", "execution_sessions", "repository_id"),
            ("idx_tool_usage_user_email", "tool_usage", "user_email"),
            ("idx_tool_usage_repo_id", "tool_usage", "repository_id"),
            ("idx_agent_performance_user_email", "agent_performance", "user_email"),
            ("idx_agent_performance_repo_id", "agent_performance", "repository_id"),
            ("idx_user_sessions_token_hash", "user_sessions", "token_hash"),
            ("idx_user_sessions_user_email", "user_sessions", "user_email"),
            ("idx_execution_artifacts_log_id", "execution_artifacts", "execution_log_id"),
            ("idx_execution_artifacts_type", "execution_artifacts", "artifact_type"),
        ]
        
        for idx_name, table, columns in indexes:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({columns})
            """)
        print(f"✓ Created {len(indexes)} indexes")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"\nDatabase location: {db_file}")
        print("\nNext steps:")
        print("1. Set JWT_SECRET environment variable")
        print("2. Run: python main.py create-user --email admin@example.com --password <password> --admin")
        print("3. Run: python main.py login --email admin@example.com --password <password>")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate database to multi-user schema")
    parser.add_argument(
        "--db-path",
        default="logs/agent_execution.db",
        help="Path to database file (relative to project root)",
    )
    
    args = parser.parse_args()
    migrate_database(args.db_path)

