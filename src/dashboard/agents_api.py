"""
Agents API endpoints for agent profiles, costs, and structured outputs.

Provides REST endpoints for the dashboard UI to display:
- Agent profiles from AGENT_PROFILES configuration
- Aggregated costs per agent from execution logs
- Recent structured outputs from agent executions
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from config.agent_profiles import AGENT_PROFILES, get_agent_profile, list_agent_ids
from src.auth.middleware import require_auth


class AgentsAPI:
    """API endpoints for agent profiles and cost tracking."""

    def __init__(self, db_path: str = "logs/agent_execution.db"):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    async def get_all_profiles(self, request: Request) -> Response:
        """
        GET /api/agents/profiles
        
        Return all agent profiles with their configurations.
        """
        try:
            profiles = []
            for agent_id in list_agent_ids():
                profile = get_agent_profile(agent_id)
                profiles.append({
                    "agent_id": agent_id,
                    "model_profile": profile.model_profile,
                    "max_turns": profile.max_turns,
                    "permission_mode": profile.permission_mode,
                    "output_schema": profile.output_schema,
                    "system_prompt_file": profile.system_prompt_file,
                    "hooks_profile": profile.hooks_profile,
                    "budget_usd": profile.budget_usd,
                    "mcp_servers": list(profile.mcp_servers.keys()),
                    "extra_allowed_tools": profile.extra_allowed_tools,
                })
            
            return web.json_response(profiles, status=200)
        
        except Exception as e:
            return web.json_response(
                {"error": f"Failed to get profiles: {str(e)}"}, 
                status=500
            )

    # @require_auth()  # Temporarily disabled for cost tracking testing
    async def get_agent_costs(self, request: Request) -> Response:
        """
        GET /api/agents/costs?period=today
        
        Return aggregated costs per agent from execution logs.
        Query params:
        - period: "today", "week", "month", "all" (default: "today")
        """
        try:
            period = request.query.get("period", "today")
            
            # Calculate time range
            now = datetime.now(timezone.utc)
            if period == "today":
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "week":
                start_time = now - timedelta(days=now.weekday())
                start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "month":
                start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif period == "all":
                start_time = None
            else:
                return web.json_response(
                    {"error": f"Invalid period: {period}"}, 
                    status=400
                )

            with self._connect() as conn:
                cursor = conn.cursor()
                
                # Query to aggregate costs by agent
                if start_time:
                    start_iso = start_time.isoformat()
                    cursor.execute("""
                        SELECT 
                            agent_name,
                            COUNT(*) as execution_count,
                            SUM(COALESCE(total_cost_usd, 0)) as total_cost_usd,
                            SUM(COALESCE(total_tokens, 0)) as total_tokens,
                            AVG(COALESCE(total_cost_usd, 0)) as avg_cost_usd
                        FROM agent_performance
                        WHERE agent_name IS NOT NULL AND timestamp >= ?
                        GROUP BY agent_name
                        ORDER BY total_cost_usd DESC
                    """, (start_iso,))
                else:
                    cursor.execute("""
                        SELECT 
                            agent_name,
                            COUNT(*) as execution_count,
                            SUM(COALESCE(total_cost_usd, 0)) as total_cost_usd,
                            SUM(COALESCE(total_tokens, 0)) as total_tokens,
                            AVG(COALESCE(total_cost_usd, 0)) as avg_cost_usd
                        FROM agent_performance
                        WHERE agent_name IS NOT NULL
                        GROUP BY agent_name
                        ORDER BY total_cost_usd DESC
                    """)
                
                rows = cursor.fetchall()
            
            # Build response with budget info from profiles
            costs = []
            for row in rows:
                agent_id = row[0]
                execution_count = row[1]
                total_cost = row[2] or 0.0
                total_tokens = row[3] or 0
                avg_cost = row[4] or 0.0
                
                # Get budget from profile
                budget_usd = None
                budget_utilization = None
                try:
                    profile = get_agent_profile(agent_id)
                    budget_usd = profile.budget_usd
                    if budget_usd and budget_usd > 0:
                        budget_utilization = (total_cost / budget_usd) * 100
                except KeyError:
                    pass  # Agent not in profiles
                
                costs.append({
                    "agent_id": agent_id,
                    "execution_count": execution_count,
                    "total_cost_usd": round(total_cost, 6),
                    "total_tokens": total_tokens,
                    "avg_cost_usd": round(avg_cost, 6),
                    "budget_usd": budget_usd,
                    "budget_utilization_percent": round(budget_utilization, 2) if budget_utilization else None,
                })
            
            # Calculate totals
            total_cost_all = sum(c["total_cost_usd"] for c in costs)
            total_budget_all = sum(c["budget_usd"] or 0 for c in costs)
            total_executions = sum(c["execution_count"] for c in costs)
            
            return web.json_response({
                "period": period,
                "agents": costs,
                "totals": {
                    "total_cost_usd": round(total_cost_all, 6),
                    "total_budget_usd": round(total_budget_all, 2),
                    "total_executions": total_executions,
                    "budget_utilization_percent": round(
                        (total_cost_all / total_budget_all) * 100, 2
                    ) if total_budget_all > 0 else None,
                }
            }, status=200)
        
        except sqlite3.OperationalError as e:
            # Table might not exist yet
            return web.json_response({
                "period": period,
                "agents": [],
                "totals": {
                    "total_cost_usd": 0,
                    "total_budget_usd": 0,
                    "total_executions": 0,
                    "budget_utilization_percent": None,
                }
            }, status=200)
        except Exception as e:
            return web.json_response(
                {"error": f"Failed to get costs: {str(e)}"}, 
                status=500
            )

    @require_auth()
    async def get_agent_outputs(self, request: Request) -> Response:
        """
        GET /api/agents/{agent_id}/outputs?limit=10
        
        Return recent structured outputs for a specific agent.
        """
        try:
            agent_id = request.match_info.get("agent_id")
            if not agent_id:
                return web.json_response(
                    {"error": "Agent ID required"}, 
                    status=400
                )
            
            limit = int(request.query.get("limit", 10))
            limit = min(limit, 100)  # Cap at 100
            
            with self._connect() as conn:
                cursor = conn.cursor()
                
                # Query for structured outputs stored in execution_artifacts
                cursor.execute("""
                    SELECT 
                        ea.id,
                        ea.execution_log_id,
                        ea.artifact_type,
                        ea.identifier,
                        ea.created_at,
                        ea.metadata,
                        el.session_id,
                        el.status
                    FROM execution_artifacts ea
                    JOIN execution_log el ON ea.execution_log_id = el.id
                    WHERE el.agent_name = ? 
                      AND ea.artifact_type = 'structured_output'
                    ORDER BY ea.created_at DESC
                    LIMIT ?
                """, (agent_id, limit))
                
                rows = cursor.fetchall()
            
            outputs = []
            for row in rows:
                metadata = json.loads(row[5]) if row[5] else {}
                outputs.append({
                    "id": row[0],
                    "execution_log_id": row[1],
                    "artifact_type": row[2],
                    "identifier": row[3],
                    "created_at": row[4],
                    "session_id": row[6],
                    "status": row[7],
                    "output_schema": metadata.get("schema_type"),
                    "structured_output": metadata.get("output"),
                })
            
            # Get schema type from profile
            output_schema = None
            try:
                profile = get_agent_profile(agent_id)
                output_schema = profile.output_schema
            except KeyError:
                pass
            
            return web.json_response({
                "agent_id": agent_id,
                "output_schema": output_schema,
                "outputs": outputs,
            }, status=200)
        
        except sqlite3.OperationalError:
            return web.json_response({
                "agent_id": agent_id,
                "output_schema": None,
                "outputs": [],
            }, status=200)
        except Exception as e:
            return web.json_response(
                {"error": f"Failed to get outputs: {str(e)}"}, 
                status=500
            )

    @require_auth()
    async def get_recent_outputs(self, request: Request) -> Response:
        """
        GET /api/agents/outputs?limit=20
        
        Return recent structured outputs across all agents.
        """
        try:
            limit = int(request.query.get("limit", 20))
            limit = min(limit, 100)
            
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        ea.id,
                        ea.execution_log_id,
                        ea.artifact_type,
                        ea.identifier,
                        ea.created_at,
                        ea.metadata,
                        el.agent_name,
                        el.session_id,
                        el.status
                    FROM execution_artifacts ea
                    JOIN execution_log el ON ea.execution_log_id = el.id
                    WHERE ea.artifact_type = 'structured_output'
                    ORDER BY ea.created_at DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
            
            outputs = []
            for row in rows:
                metadata = json.loads(row[5]) if row[5] else {}
                outputs.append({
                    "id": row[0],
                    "execution_log_id": row[1],
                    "artifact_type": row[2],
                    "identifier": row[3],
                    "created_at": row[4],
                    "agent_id": row[6],
                    "session_id": row[7],
                    "status": row[8],
                    "output_schema": metadata.get("schema_type"),
                    "structured_output": metadata.get("output"),
                })
            
            return web.json_response({
                "outputs": outputs,
            }, status=200)
        
        except sqlite3.OperationalError:
            return web.json_response({"outputs": []}, status=200)
        except Exception as e:
            return web.json_response(
                {"error": f"Failed to get outputs: {str(e)}"}, 
                status=500
            )

    def setup_routes(self, app: web.Application) -> None:
        """Register agents API routes."""
        # Public endpoint - profiles don't require auth
        app.router.add_get("/api/agents/profiles", self.get_all_profiles)
        
        # Protected endpoints
        app.router.add_get("/api/agents/costs", self.get_agent_costs)
        app.router.add_get("/api/agents/outputs", self.get_recent_outputs)
        app.router.add_get("/api/agents/{agent_id}/outputs", self.get_agent_outputs)


__all__ = ["AgentsAPI"]

