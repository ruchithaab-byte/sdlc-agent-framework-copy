"""
SQLite-backed execution logger for the SDLC agent framework.

Creates tables:
    - execution_log: granular hook events and tool uses
    - tool_usage: aggregated stats per tool
    - agent_performance: coarse agent-level metrics
    - execution_artifacts: structured outputs (deployments, PRs, commits)
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from config.agent_config import PROJECT_ROOT
from src.utils.repository_utils import detect_repository

if TYPE_CHECKING:
    from typing import Any as DashboardServerType


@dataclass(frozen=True)
class ExecutionEvent:
    """Convenience dataclass representing a single execution log row."""

    timestamp: str
    session_id: str
    hook_event: str
    status: str
    duration_ms: Optional[int] = None


class ExecutionLogger:
    """Centralized execution logger for all agent activities with user/repo tracking."""

    # Global dashboard server instance for broadcasting (set by DashboardServer)
    _dashboard_server: Optional[Any] = None

    def __init__(
        self,
        db_path: str = "logs/agent_execution.db",
        project_path: Optional[str] = None,
        user_email: Optional[str] = None,
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.project_path = project_path or str(PROJECT_ROOT)
        self.user_email = user_email
        self._repository_id: Optional[int] = None
        self._init_database()
        if self.user_email:
            self._ensure_repository_registered()


    def _connect(self) -> sqlite3.Connection:
        """Create database connection with timeout and WAL mode for better concurrency."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        # Enable WAL mode for better concurrent read/write performance
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_database(self) -> None:
        """Create tables if they do not exist (schema managed by migration script)."""
        # Tables are created by migration script, this is a no-op for compatibility
        pass
    
    def _ensure_repository_registered(self) -> None:
        """Register or update repository record."""
        if not self.project_path:
            return
        
        repo_info = detect_repository(self.project_path)
        if not repo_info:
            return
        
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                # Check if repositories table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='repositories'"
                )
                if not cursor.fetchone():
                    # Table doesn't exist yet, skip registration
                    return
                
                now = datetime.now(timezone.utc).isoformat()
                
                # Check if repository exists
                cursor.execute(
                    "SELECT id FROM repositories WHERE repo_path = ?",
                    (repo_info["repo_path"],),
                )
                row = cursor.fetchone()
            
            if row:
                self._repository_id = row[0]
                # Update last_seen_at
                cursor.execute(
                    "UPDATE repositories SET last_seen_at = ?, git_branch = ? WHERE id = ?",
                    (now, repo_info.get("git_branch"), self._repository_id),
                )
            else:
                # Create new repository
                cursor.execute(
                    """
                    INSERT INTO repositories (
                        repo_path, repo_name, git_remote_url, git_branch,
                        first_seen_at, last_seen_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        repo_info["repo_path"],
                        repo_info["repo_name"],
                        repo_info.get("git_remote_url"),
                        repo_info.get("git_branch"),
                        now,
                        now,
                        json.dumps(repo_info),
                    ),
                )
                self._repository_id = cursor.lastrowid
            
                conn.commit()
        except sqlite3.OperationalError:
            # Table doesn't exist yet, skip registration
            pass

    def _ensure_user_record(self, user_email: str) -> None:
        """Ensure user record exists in users table with GitHub display name."""
        if not user_email or user_email == "unknown":
            return
        
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                # Check if users table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
                )
                if not cursor.fetchone():
                    return
                
                # Check if user exists
                cursor.execute("SELECT email, display_name FROM users WHERE email = ?", (user_email,))
                user_row = cursor.fetchone()
                
                # Get GitHub display name
                try:
                    from src.utils.github_user_utils import get_github_user_info
                    github_email, github_username, github_display_name = get_github_user_info()
                    
                    # Only update if this email matches GitHub email
                    if user_email == github_email and github_display_name:
                        now = datetime.now(timezone.utc).isoformat()
                        if user_row:
                            # Update existing user with GitHub display name if not set
                            if not user_row[1]:  # display_name is None or empty
                                cursor.execute(
                                    "UPDATE users SET display_name = ?, last_seen_at = ? WHERE email = ?",
                                    (github_display_name, now, user_email)
                                )
                                conn.commit()
                        else:
                            # Try to update display_name only if user exists but doesn't have one
                            # Don't create new users here - they should be created via auth API
                            # Just update display_name for existing users
                            pass
                except Exception:
                    # Don't fail if GitHub info unavailable
                    pass
        except sqlite3.OperationalError:
            # Table doesn't exist yet, skip
            pass
        except Exception:
            # Don't fail logging if user record creation fails
            pass

    def log_execution(
        self,
        *,
        session_id: str,
        hook_event: str,
        tool_name: Optional[str] = None,
        agent_name: Optional[str] = None,
        phase: Optional[str] = None,
        status: str = "success",
        duration_ms: Optional[int] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Insert a single execution log entry.
        
        Returns:
            Execution log ID for artifact linking
        """
        # Always check environment variable to ensure we use the latest value
        # This prevents using stale cached email from initialization
        import os
        user_email = os.getenv("AGENT_USER_EMAIL") or self.user_email or "unknown"
        
        # Ensure user record exists with GitHub display name
        self._ensure_user_record(user_email)
        payload = (
            datetime.utcnow().isoformat(),
            session_id,
            user_email,
            self._repository_id,
            hook_event,
            tool_name,
            agent_name,
            phase,
            status,
            duration_ms,
            json.dumps(input_data) if input_data else None,
            json.dumps(output_data) if output_data else None,
            error_message,
            json.dumps(metadata) if metadata else None,
        )
        # Use explicit connection management with timeout and WAL mode
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO execution_log (
                    timestamp, session_id, user_email, repository_id,
                    hook_event, tool_name, agent_name, phase, status,
                    duration_ms, input_data, output_data, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                payload,
            )
            conn.commit()
            exec_id = cursor.lastrowid
            return exec_id
        finally:
            if conn:
                conn.close()

    def update_tool_usage(
        self,
        *,
        session_id: str,
        tool_name: str,
        success: bool,
        duration_ms: int = 0,
    ) -> None:
        """Update aggregated tool statistics."""
        # Always check environment variable to ensure we use the latest value
        import os
        user_email = os.getenv("AGENT_USER_EMAIL") or self.user_email or "unknown"
        self._ensure_user_record(user_email)
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, success_count, failure_count, total_duration_ms
                FROM tool_usage
                WHERE session_id = ? AND tool_name = ? AND user_email = ?
            """,
                (session_id, tool_name, user_email),
            )
            row = cursor.fetchone()
            if row:
                success_count = row[1] + (1 if success else 0)
                failure_count = row[2] + (0 if success else 1)
                total_duration_ms = row[3] + duration_ms
                cursor.execute(
                    """
                    UPDATE tool_usage
                    SET success_count = ?, failure_count = ?, total_duration_ms = ?
                    WHERE id = ?
                """,
                    (success_count, failure_count, total_duration_ms, row[0]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO tool_usage (
                        timestamp, session_id, user_email, repository_id, tool_name,
                        success_count, failure_count, total_duration_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.utcnow().isoformat(),
                        session_id,
                        user_email,
                        self._repository_id,
                        tool_name,
                        1 if success else 0,
                        0 if success else 1,
                        duration_ms,
                    ),
                )
            conn.commit()

    def log_agent_performance(
        self,
        *,
        session_id: str,
        agent_name: str,
        phase: str,
        total_turns: int,
        total_tokens: int,
        total_cost_usd: float,
        success: bool = True,
    ) -> None:
        """Persist a coarse agent-level metric snapshot."""
        # Always check environment variable to ensure we use the latest value
        import os
        user_email = os.getenv("AGENT_USER_EMAIL") or self.user_email or "unknown"
        self._ensure_user_record(user_email)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_performance (
                    timestamp, session_id, user_email, repository_id,
                    agent_name, phase, total_turns, total_tokens, total_cost_usd, success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.utcnow().isoformat(),
                    session_id,
                    user_email,
                    self._repository_id,
                    agent_name,
                    phase,
                    total_turns,
                    total_tokens,
                    total_cost_usd,
                    1 if success else 0,
                ),
            )
            conn.commit()
    
    def log_artifact(
        self,
        *,
        execution_log_id: int,
        artifact_type: str,
        artifact_url: Optional[str] = None,
        identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an execution artifact (deployment, PR, commit, etc.).
        
        Args:
            execution_log_id: ID of the execution_log entry this artifact belongs to
            artifact_type: Type of artifact (deployment, pr, commit, file)
            artifact_url: URL to the artifact (e.g., PR URL, deployment URL)
            identifier: Unique identifier (e.g., commit hash, PR number)
            metadata: Additional metadata as JSON
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO execution_artifacts (
                    execution_log_id, artifact_type, artifact_url,
                    identifier, created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    execution_log_id,
                    artifact_type,
                    artifact_url,
                    identifier,
                    datetime.utcnow().isoformat(),
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
    
    def get_user_executions(
        self,
        user_email: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get executions for a specific user (defaults to current user)."""
        email = user_email or self.user_email or "unknown"
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, session_id, hook_event, tool_name, agent_name,
                       phase, status, duration_ms
                FROM execution_log
                WHERE user_email = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (email, limit),
            )
            rows = cursor.fetchall()
        return [
            {
                "timestamp": row[0],
                "session_id": row[1],
                "hook_event": row[2],
                "tool_name": row[3],
                "agent_name": row[4],
                "phase": row[5],
                "status": row[6],
                "duration_ms": row[7],
            }
            for row in rows
        ]
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get list of all registered users (admin only)."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT email, display_name, created_at, last_seen_at, last_login_at, is_admin, is_active
                FROM users
                ORDER BY last_seen_at DESC
                """
            )
            rows = cursor.fetchall()
        return [
            {
                "email": row[0],
                "display_name": row[1],
                "created_at": row[2],
                "last_seen_at": row[3],
                "last_login_at": row[4],
                "is_admin": bool(row[5]),
                "is_active": bool(row[6]),
            }
            for row in rows
        ]

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Return aggregate stats for a session."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_events,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) AS successful,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) AS errors,
                    AVG(duration_ms) AS avg_duration,
                    SUM(duration_ms) AS total_duration
                FROM execution_log
                WHERE session_id = ?
            """,
                (session_id,),
            )
            total_events, successful, errors, avg_duration, total_duration = cursor.fetchone()
        return {
            "total_events": total_events or 0,
            "successful": successful or 0,
            "errors": errors or 0,
            "avg_duration_ms": int(avg_duration or 0),
            "total_duration_ms": int(total_duration or 0),
        }


__all__ = [
    "ExecutionLogger",
    "ExecutionEvent",
]

