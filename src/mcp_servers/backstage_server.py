"""MCP server wrapper for Backstage catalog interactions."""

from __future__ import annotations

from typing import Any, Dict, Optional

import aiohttp


class BackstageMCPServer:
    """Simple REST client for the Backstage catalog API."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}{path}", params=params) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def catalog_lookup(self, kind: str = "Component", query: Optional[str] = None) -> Dict[str, Any]:
        params = {"filter": f"kind={kind}"}
        if query:
            params["text"] = query
        return await self._get("/api/catalog/entities", params)

    async def get_dependencies(self, entity_ref: str) -> Dict[str, Any]:
        return await self._get(f"/api/catalog/entities/by-name/{entity_ref}/relations")

    async def register_component(self, yaml_def: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession(
            headers={"Content-Type": "application/x-yaml"}
        ) as session:
            async with session.post(f"{self.base_url}/api/catalog/entities", data=yaml_def) as resp:
                resp.raise_for_status()
                return await resp.json()


__all__ = ["BackstageMCPServer"]

