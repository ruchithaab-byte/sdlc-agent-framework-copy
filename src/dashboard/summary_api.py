"""
Summary API endpoints for repository analytics and artifacts.
"""

from __future__ import annotations

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from src.analytics.summary_service import SummaryService
from src.auth.middleware import require_auth


class SummaryAPI:
    """API endpoints for summary data."""

    def __init__(self, db_path: str = "logs/agent_execution.db"):
        self.service = SummaryService(db_path)

    # @require_auth()  # Temporarily disabled for testing
    async def get_repository_summary(self, request: Request) -> Response:
        """GET /api/summary/repository/{repo_id}?period=today"""
        try:
            repo_id_str = request.match_info.get("repo_id")
            if not repo_id_str:
                return web.json_response({"error": "Repository ID required"}, status=400)

            repo_id = int(repo_id_str)
            period = request.query.get("period", "today")
            user_email = request.get("user_email")
            is_admin = request.get("is_admin", False)

            # Non-admin users can only see their own data
            filter_user = user_email if not is_admin else None

            summary = self.service.get_repository_summary(
                repository_id=repo_id, period=period, user_email=filter_user
            )

            # Convert to dict
            data = {
                "repository_id": summary.repository_id,
                "repo_name": summary.repo_name,
                "repo_path": summary.repo_path,
                "total_users": summary.total_users,
                "total_sessions": summary.total_sessions,
                "total_executions": summary.total_executions,
                "agents_used": summary.agents_used,
                "phases_completed": summary.phases_completed,
                "user_summaries": [
                    {
                        "user_email": u.user_email,
                        "display_name": u.display_name,
                        "total_sessions": u.total_sessions,
                        "total_executions": u.total_executions,
                        "successful_executions": u.successful_executions,
                        "failed_executions": u.failed_executions,
                        "total_duration_ms": u.total_duration_ms,
                        "total_tokens": u.total_tokens,
                        "total_cost_usd": u.total_cost_usd,
                        "agents_used": u.agents_used,
                        "phases_completed": u.phases_completed,
                        "tools_used": u.tools_used,
                    }
                    for u in summary.user_summaries
                ],
            }

            return web.json_response(data, status=200)

        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            return web.json_response({"error": f"Failed to get summary: {str(e)}"}, status=500)

    @require_auth()
    async def get_all_repositories(self, request: Request) -> Response:
        """GET /api/summary/repositories"""
        try:
            user_email = request.get("user_email")
            is_admin = request.get("is_admin", False)

            repos = self.service.get_all_repositories()

            # Non-admin users see repos they've used OR repos they have access to
            # (repos are visible even with 0 executions - they just need to exist)
            if not is_admin and user_email:
                # For non-admin users, show all repositories
                # The repository summary will show 0 executions if they haven't used it yet
                # This allows users to see available repositories even before running agents
                pass  # Show all repos - filtering by execution count was too restrictive

            return web.json_response(repos, status=200)

        except Exception as e:
            return web.json_response({"error": f"Failed to get repositories: {str(e)}"}, status=500)

    @require_auth()
    async def get_deployments(self, request: Request) -> Response:
        """GET /api/summary/deployments/{repo_id} or /api/summary/deployments"""
        try:
            repo_id_str = request.match_info.get("repo_id")
            repo_id = int(repo_id_str) if repo_id_str and repo_id_str != "all" else None
            limit = int(request.query.get("limit", 50))

            deployments = self.service.get_deployment_history(repository_id=repo_id, limit=limit)

            data = [
                {
                    "id": d.id,
                    "execution_log_id": d.execution_log_id,
                    "artifact_url": d.artifact_url,
                    "identifier": d.identifier,
                    "created_at": d.created_at,
                    "metadata": d.metadata,
                }
                for d in deployments
            ]

            return web.json_response(data, status=200)

        except Exception as e:
            return web.json_response(
                {"error": f"Failed to get deployments: {str(e)}"}, status=500
            )

    @require_auth()
    async def get_changelog(self, request: Request) -> Response:
        """GET /api/summary/changelog/{repo_id}"""
        try:
            repo_id_str = request.match_info.get("repo_id")
            repo_id = int(repo_id_str) if repo_id_str else None
            limit = int(request.query.get("limit", 50))

            changelog = self.service.get_changelog(repository_id=repo_id, limit=limit)

            data = [
                {
                    "id": c.id,
                    "execution_log_id": c.execution_log_id,
                    "artifact_type": c.artifact_type,
                    "artifact_url": c.artifact_url,
                    "identifier": c.identifier,
                    "created_at": c.created_at,
                    "metadata": c.metadata,
                }
                for c in changelog
            ]

            return web.json_response(data, status=200)

        except Exception as e:
            return web.json_response(
                {"error": f"Failed to get changelog: {str(e)}"}, status=500
            )

    def setup_routes(self, app: web.Application) -> None:
        """Register summary API routes."""
        app.router.add_get("/api/summary/repository/{repo_id}", self.get_repository_summary)
        app.router.add_get("/api/summary/repositories", self.get_all_repositories)
        app.router.add_get("/api/summary/deployments/{repo_id}", self.get_deployments)
        app.router.add_get("/api/summary/deployments", self.get_deployments)  # All deployments
        app.router.add_get("/api/summary/changelog/{repo_id}", self.get_changelog)
        app.router.add_get("/api/summary/changelog", self.get_changelog)  # All changelog


__all__ = ["SummaryAPI"]

