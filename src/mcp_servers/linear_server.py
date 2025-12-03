"""
Minimal MCP server wrapper for Linear GraphQL operations.

Provides helper methods for:
    - creating epics
    - creating issues
    - planning sprints
    - updating issue status
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional

import aiohttp

from src.tracing import trace_run, RunType


class LinearMCPServer:
    """Async GraphQL client for Linear operations used by the SDLC agents."""

    def __init__(
        self,
        *,
        api_key: str,
        team_id: str,
        endpoint: str = "https://api.linear.app/graphql",
    ) -> None:
        self.api_key = api_key
        self.team_id = team_id
        self.endpoint = endpoint
        
        # Context injection (Phase 2)
        self._context: Optional[Dict[str, Any]] = None

    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set session context for tool operations.
        
        This method binds the server to a specific Linear ticket context,
        ensuring tools operate on the correct ticket.
        
        Args:
            context: Session context dict with keys:
                - linear_ticket_id: Linear ticket/issue ID
        """
        self._context = context

    async def _execute(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(self.endpoint, json={"query": query, "variables": variables}) as resp:
                resp.raise_for_status()
                data = await resp.json()
                if "errors" in data:
                    raise RuntimeError(f"Linear API error: {data['errors']}")
                return data["data"]

    @trace_run(name="Linear: Create Epic", run_type=RunType.TOOL)
    async def create_epic(self, title: str, description: str) -> Dict[str, Any]:
        mutation = """
        mutation CreateEpic($title: String!, $description: String!, $teamId: String!) {
          issueCreate(input: {
            title: $title,
            description: $description,
            teamId: $teamId
          }) {
            issue { id identifier url }
          }
        }
        """
        return await self._execute(
            mutation,
            {"title": title, "description": description, "teamId": self.team_id},
        )

    @trace_run(name="Linear: Create Issue", run_type=RunType.TOOL)
    async def create_issue(
        self,
        title: str,
        description: str,
        *,
        parent_id: Optional[str] = None,
        estimate: Optional[int] = None,
    ) -> Dict[str, Any]:
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            issue { id identifier url }
          }
        }
        """
        input_payload: Dict[str, Any] = {
            "teamId": self.team_id,
            "title": title,
            "description": description,
        }
        if parent_id:
            input_payload["parentId"] = parent_id
        if estimate is not None:
            input_payload["estimate"] = estimate
        return await self._execute(mutation, {"input": input_payload})

    async def plan_sprint(self, name: str, start_date: str, end_date: str) -> Dict[str, Any]:
        mutation = """
        mutation CreateSprint($name: String!, $startDate: TimelessDate!, $endDate: TimelessDate!, $teamId: String!) {
          cycleCreate(input: {
            name: $name,
            startsAt: $startDate,
            endsAt: $endDate,
            teamId: $teamId
          }) {
            cycle { id name startsAt endsAt }
          }
        }
        """
        variables = {
            "name": name,
            "startDate": start_date,
            "endDate": end_date,
            "teamId": self.team_id,
        }
        return await self._execute(mutation, variables)

    async def update_issue_status(self, issue_id: str, state_id: str) -> Dict[str, Any]:
        mutation = """
        mutation UpdateIssue($issueId: String!, $stateId: String!) {
          issueUpdate(id: $issueId, input: { stateId: $stateId }) {
            issue { id identifier state { name } }
          }
        }
        """
        return await self._execute(mutation, {"issueId": issue_id, "stateId": state_id})

    # =========================================================================
    # Tool Exposure (Critical for Agent SDK)
    # =========================================================================

    def get_tools(self) -> List[Callable]:
        """
        Returns list of callable tools for Agent SDK consumption.
        
        This method exposes the Linear operations as tools that can be
        passed directly to the Agent SDK's tools parameter.
        
        Returns:
            List[Callable]: List of async tool methods.
        """
        from typing import Callable
        return [
            self.create_epic,
            self.create_issue,
            self.plan_sprint,
            self.update_issue_status,
        ]


async def example_usage() -> None:
    """Simple smoke-test helper (not executed automatically)."""
    client = LinearMCPServer(api_key="dummy", team_id="team123")
    try:
        await client.create_epic("Example", "Demo epic")
    except Exception:
        # Ignore failures during local smoke testing when real credentials are missing.
        pass


if __name__ == "__main__":
    asyncio.run(example_usage())

