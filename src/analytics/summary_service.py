"""
Service for generating time-based summary analytics by user and repository.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class UserProgressSummary:
    """Summary of user progress for a time period."""

    user_email: str
    display_name: Optional[str]
    total_sessions: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    total_duration_ms: int
    total_tokens: int
    total_cost_usd: float
    agents_used: List[str]
    phases_completed: List[str]
    tools_used: Dict[str, int]  # tool_name -> count


@dataclass
class RepositorySummary:
    """Summary of repository progress for a time period."""

    repository_id: int
    repo_name: str
    repo_path: str
    total_users: int
    total_sessions: int
    total_executions: int
    user_summaries: List[UserProgressSummary]
    agents_used: List[str]
    phases_completed: List[str]


@dataclass
class DeploymentArtifact:
    """Deployment artifact information."""

    id: int
    execution_log_id: int
    artifact_url: Optional[str]
    identifier: Optional[str]
    created_at: str
    metadata: Optional[Dict[str, Any]]


@dataclass
class ChangelogArtifact:
    """Changelog artifact (PR or commit) information."""

    id: int
    execution_log_id: int
    artifact_type: str  # "pr" or "commit"
    artifact_url: Optional[str]
    identifier: Optional[str]
    created_at: str
    metadata: Optional[Dict[str, Any]]


class SummaryService:
    """Service for generating progress summaries."""

    def __init__(self, db_path: str = "logs/agent_execution.db"):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def get_repository_summary(
        self,
        repository_id: Optional[int] = None,
        repo_path: Optional[str] = None,
        period: str = "today",  # "today", "week", "month"
        user_email: Optional[str] = None,
    ) -> RepositorySummary:
        """
        Get summary of repository progress for a time period.

        Args:
            repository_id: Repository ID (if known)
            repo_path: Repository path (used to find repository_id if not provided)
            period: Time period ("today", "week", "month")
            user_email: Optional filter by specific user
        """
        # Calculate time range
        now = datetime.now(timezone.utc)
        if period == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_time = now - timedelta(days=now.weekday())
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError(f"Invalid period: {period}")

        start_iso = start_time.isoformat()

        with self._connect() as conn:
            cursor = conn.cursor()

            # Find repository_id if not provided
            if repository_id is None and repo_path:
                cursor.execute(
                    "SELECT id, repo_name, repo_path FROM repositories WHERE repo_path = ?",
                    (repo_path,),
                )
                row = cursor.fetchone()
                if row:
                    repository_id = row[0]
                    repo_name = row[1]
                    repo_path = row[2]
                else:
                    raise ValueError(f"Repository not found: {repo_path}")
            elif repository_id:
                cursor.execute(
                    "SELECT repo_name, repo_path FROM repositories WHERE id = ?",
                    (repository_id,),
                )
                row = cursor.fetchone()
                if row:
                    repo_name = row[0]
                    repo_path = row[1]
                else:
                    raise ValueError(f"Repository not found: {repository_id}")
            else:
                raise ValueError("Either repository_id or repo_path must be provided")

            # Build query conditions - use table aliases to avoid ambiguous column names
            conditions = ["el.repository_id = ?", "el.timestamp >= ?"]
            params = [repository_id, start_iso]

            if user_email:
                conditions.append("el.user_email = ?")
                params.append(user_email)

            where_clause = " AND ".join(conditions)

            # Get execution statistics
            cursor.execute(
                f"""
                SELECT
                    el.user_email,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN el.status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN el.status = 'error' THEN 1 ELSE 0 END) as failed,
                    SUM(el.duration_ms) as total_duration,
                    COUNT(DISTINCT COALESCE(ap.agent_name, el.agent_name)) as unique_agents,
                    COUNT(DISTINCT el.phase) as unique_phases
                FROM execution_log el
                LEFT JOIN agent_performance ap ON el.session_id = ap.session_id
                WHERE {where_clause}
                GROUP BY el.user_email
            """,
                params,
            )

            user_stats = cursor.fetchall()

            # Get user details
            user_summaries = []
            for user_row in user_stats:
                email = user_row[0]
                total_exec = user_row[1]
                successful = user_row[2]
                failed = user_row[3]
                total_duration = user_row[4] or 0

                # Get user info from users table
                cursor.execute(
                    "SELECT display_name FROM users WHERE email = ?", (email,)
                )
                user_info = cursor.fetchone()
                display_name = user_info[0] if user_info else None

                # If no display_name in users table, try to get from GitHub
                if not display_name:
                    try:
                        from src.utils.github_user_utils import get_github_user_info
                        github_email, _, github_display_name = get_github_user_info()
                        # Only use GitHub name if email matches
                        if github_email == email and github_display_name:
                            display_name = github_display_name
                    except Exception:
                        pass

                # Get session count - rebuild where_clause with table alias
                session_where = " AND ".join([
                    "el.repository_id = ?",
                    "el.timestamp >= ?",
                    "el.user_email = ?"
                ])
                cursor.execute(
                    f"""
                    SELECT COUNT(DISTINCT el.session_id)
                    FROM execution_log el
                    WHERE {session_where}
                """,
                    [repository_id, start_iso, email],
                )
                session_count = cursor.fetchone()[0] or 0

                # Get tokens and cost from agent_performance
                # Match by user_email OR by session_id (in case user_email was "unknown" when logged)
                # This ensures we capture all costs for sessions belonging to this user
                cursor.execute(
                    f"""
                    SELECT
                        SUM(ap.total_tokens) as tokens,
                        SUM(ap.total_cost_usd) as cost
                    FROM agent_performance ap
                    WHERE (
                          ap.user_email = ?
                          OR EXISTS (
                              SELECT 1 
                              FROM execution_log el 
                              WHERE el.session_id = ap.session_id 
                                AND el.user_email = ?
                          )
                      )
                      AND ap.timestamp >= ?
                      AND (
                          ap.repository_id = ?
                          OR (
                              ap.repository_id IS NULL 
                              AND EXISTS (
                                  SELECT 1 
                                  FROM execution_log el 
                                  WHERE el.session_id = ap.session_id 
                                    AND el.repository_id = ?
                              )
                          )
                          OR (? IS NULL)
                      )
                """,
                    (email, email, start_iso, repository_id, repository_id, repository_id),
                )
                perf_row = cursor.fetchone()
                total_tokens = perf_row[0] or 0 if perf_row else 0
                total_cost = perf_row[1] or 0.0 if perf_row else 0.0

                # Get agents used from BOTH execution_log AND agent_performance
                # This ensures we capture all agents, even if they're only in one table
                cursor.execute(
                    f"""
                    SELECT DISTINCT agent_name
                    FROM (
                        -- Agents from execution_log
                        SELECT DISTINCT el.agent_name
                        FROM execution_log el
                        WHERE el.repository_id = ?
                          AND el.timestamp >= ?
                          AND el.user_email = ?
                          AND el.agent_name IS NOT NULL
                        UNION
                        -- Agents from agent_performance (match by user_email OR session_id)
                        SELECT DISTINCT ap.agent_name
                        FROM agent_performance ap
                        WHERE (
                              ap.user_email = ?
                              OR EXISTS (
                                  SELECT 1 
                                  FROM execution_log el 
                                  WHERE el.session_id = ap.session_id 
                                    AND el.user_email = ?
                              )
                          )
                          AND ap.timestamp >= ?
                          AND (
                              ap.repository_id = ?
                              OR (
                                  ap.repository_id IS NULL 
                                  AND EXISTS (
                                      SELECT 1 
                                      FROM execution_log el 
                                      WHERE el.session_id = ap.session_id 
                                        AND el.repository_id = ?
                                  )
                              )
                              OR (? IS NULL)
                          )
                          AND ap.agent_name IS NOT NULL
                    )
                    ORDER BY agent_name
                """,
                    (repository_id, start_iso, email, email, email, start_iso, repository_id, repository_id, repository_id),
                )
                agents = [row[0] for row in cursor.fetchall()]

                # Get phases completed - rebuild where_clause without table alias for single-table query
                phases_where = " AND ".join([
                    "repository_id = ?",
                    "timestamp >= ?",
                    "user_email = ?",
                    "phase IS NOT NULL"
                ])
                cursor.execute(
                    f"""
                    SELECT DISTINCT phase
                    FROM execution_log
                    WHERE {phases_where}
                """,
                    [repository_id, start_iso, email],
                )
                phases = [row[0] for row in cursor.fetchall()]

                # Get tools used - rebuild where_clause without table alias for single-table query
                tools_where = " AND ".join([
                    "repository_id = ?",
                    "timestamp >= ?",
                    "user_email = ?",
                    "tool_name IS NOT NULL"
                ])
                cursor.execute(
                    f"""
                    SELECT tool_name, COUNT(*) as count
                    FROM execution_log
                    WHERE {tools_where}
                    GROUP BY tool_name
                """,
                    [repository_id, start_iso, email],
                )
                tools = {row[0]: row[1] for row in cursor.fetchall()}

                user_summaries.append(
                    UserProgressSummary(
                        user_email=email,
                        display_name=display_name,
                        total_sessions=session_count,
                        total_executions=total_exec,
                        successful_executions=successful,
                        failed_executions=failed,
                        total_duration_ms=total_duration,
                        total_tokens=total_tokens,
                        total_cost_usd=total_cost,
                        agents_used=agents,
                        phases_completed=phases,
                        tools_used=tools,
                    )
                )

            # Get overall repository stats
            # Get overall repository stats - rebuild where_clause without table alias for single-table query
            repo_stats_where = " AND ".join([
                "repository_id = ?",
                "timestamp >= ?"
            ])
            repo_stats_params = [repository_id, start_iso]
            if user_email:
                repo_stats_where += " AND user_email = ?"
                repo_stats_params.append(user_email)
            
            cursor.execute(
                f"""
                SELECT
                    COUNT(DISTINCT user_email) as total_users,
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(*) as total_executions
                FROM execution_log
                WHERE {repo_stats_where}
            """,
                repo_stats_params,
            )
            repo_stats = cursor.fetchone()

            # Get all agents used from BOTH execution_log AND agent_performance
            # For Activity Breakdown: Show ALL agents that have been run (any repository)
            # This gives a complete picture of agent usage across the system
            cursor.execute(
                f"""
                SELECT DISTINCT agent_name
                FROM (
                    -- Agents from execution_log (for this repository)
                    SELECT DISTINCT el.agent_name
                    FROM execution_log el
                    WHERE el.repository_id = ?
                      AND el.timestamp >= ?
                      {f"AND el.user_email = ?" if user_email else ""}
                      AND el.agent_name IS NOT NULL
                    UNION
                    -- Agents from agent_performance (match if session has ANY execution_log with this repository_id)
                    SELECT DISTINCT ap.agent_name
                    FROM agent_performance ap
                    WHERE ap.timestamp >= ?
                      AND (
                          -- Direct repository_id match
                          ap.repository_id = ?
                          OR (
                              -- Session-based match: if ANY execution_log for this session has this repository_id
                              EXISTS (
                                  SELECT 1 
                                  FROM execution_log el 
                                  WHERE el.session_id = ap.session_id 
                                    AND el.repository_id = ?
                                    AND el.timestamp >= ?
                              )
                          )
                      )
                      {f"AND (ap.user_email = ? OR EXISTS (SELECT 1 FROM execution_log el WHERE el.session_id = ap.session_id AND el.user_email = ? AND el.timestamp >= ?))" if user_email else ""}
                      AND ap.agent_name IS NOT NULL
                    UNION
                    -- ALL agents from agent_performance (any repository) - for Activity Breakdown completeness
                    -- This shows all agents that have been run, regardless of repository
                    SELECT DISTINCT ap.agent_name
                    FROM agent_performance ap
                    WHERE ap.timestamp >= ?
                      {f"AND (ap.user_email = ? OR EXISTS (SELECT 1 FROM execution_log el WHERE el.session_id = ap.session_id AND el.user_email = ? AND el.timestamp >= ?))" if user_email else ""}
                      AND ap.agent_name IS NOT NULL
                )
                ORDER BY agent_name
            """,
                ([repository_id, start_iso] + ([user_email] if user_email else []) +
                 [start_iso, repository_id, repository_id, start_iso] + ([user_email, user_email, start_iso] if user_email else []) +
                 [start_iso] + ([user_email, user_email, start_iso] if user_email else [])),
            )
            all_agents = [row[0] for row in cursor.fetchall()]

            # Get all phases used - rebuild where_clause without table alias for single-table query
            phases_where = " AND ".join([
                "repository_id = ?",
                "timestamp >= ?"
            ])
            phases_params = [repository_id, start_iso]
            if user_email:
                phases_where += " AND user_email = ?"
                phases_params.append(user_email)

            cursor.execute(
                f"""
                SELECT DISTINCT phase
                FROM execution_log
                WHERE {phases_where} AND phase IS NOT NULL
            """,
                phases_params,
            )
            all_phases = [row[0] for row in cursor.fetchall()]

            return RepositorySummary(
                repository_id=repository_id,
                repo_name=repo_name,
                repo_path=repo_path,
                total_users=repo_stats[0] or 0,
                total_sessions=repo_stats[1] or 0,
                total_executions=repo_stats[2] or 0,
                user_summaries=user_summaries,
                agents_used=all_agents,
                phases_completed=all_phases,
            )

    def get_deployment_history(
        self, repository_id: Optional[int] = None, limit: int = 50
    ) -> List[DeploymentArtifact]:
        """Get deployment artifacts for a repository."""
        with self._connect() as conn:
            cursor = conn.cursor()

            if repository_id:
                cursor.execute(
                    """
                    SELECT ea.id, ea.execution_log_id, ea.artifact_url, ea.identifier,
                           ea.created_at, ea.metadata
                    FROM execution_artifacts ea
                    JOIN execution_log el ON ea.execution_log_id = el.id
                    WHERE ea.artifact_type = 'deployment' AND el.repository_id = ?
                    ORDER BY ea.created_at DESC
                    LIMIT ?
                    """,
                    (repository_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, execution_log_id, artifact_url, identifier,
                           created_at, metadata
                    FROM execution_artifacts
                    WHERE artifact_type = 'deployment'
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = cursor.fetchall()
            return [
                DeploymentArtifact(
                    id=row[0],
                    execution_log_id=row[1],
                    artifact_url=row[2],
                    identifier=row[3],
                    created_at=row[4],
                    metadata=json.loads(row[5]) if row[5] else None,
                )
                for row in rows
            ]

    def get_changelog(
        self,
        repository_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[ChangelogArtifact]:
        """Get changelog artifacts (PRs and commits) for a repository."""

        with self._connect() as conn:
            cursor = conn.cursor()

            if repository_id:
                cursor.execute(
                    """
                    SELECT ea.id, ea.execution_log_id, ea.artifact_type, ea.artifact_url,
                           ea.identifier, ea.created_at, ea.metadata
                    FROM execution_artifacts ea
                    JOIN execution_log el ON ea.execution_log_id = el.id
                    WHERE ea.artifact_type IN ('pr', 'commit') AND el.repository_id = ?
                    ORDER BY ea.created_at DESC
                    LIMIT ?
                    """,
                    (repository_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, execution_log_id, artifact_type, artifact_url,
                           identifier, created_at, metadata
                    FROM execution_artifacts
                    WHERE artifact_type IN ('pr', 'commit')
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = cursor.fetchall()
            return [
                ChangelogArtifact(
                    id=row[0],
                    execution_log_id=row[1],
                    artifact_type=row[2],
                    artifact_url=row[3],
                    identifier=row[4],
                    created_at=row[5],
                    metadata=json.loads(row[6]) if row[6] else None,
                )
                for row in rows
            ]

    def get_all_repositories(self) -> List[Dict[str, Any]]:
        """Get list of all tracked repositories."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, repo_name, repo_path, git_remote_url, git_branch,
                       first_seen_at, last_seen_at
                FROM repositories
                ORDER BY last_seen_at DESC
            """
            )
            rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "repo_name": row[1],
                "repo_path": row[2],
                "git_remote_url": row[3],
                "git_branch": row[4],
                "first_seen_at": row[5],
                "last_seen_at": row[6],
            }
            for row in rows
        ]


__all__ = [
    "SummaryService",
    "RepositorySummary",
    "UserProgressSummary",
    "DeploymentArtifact",
    "ChangelogArtifact",
]

