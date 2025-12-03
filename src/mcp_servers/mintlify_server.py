"""Mintlify documentation search MCP server."""

from __future__ import annotations

from typing import Any, Dict, Optional

import aiohttp


class MintlifyMCPServer:
    """Client wrapper around Mintlify's documentation search endpoints."""

    def __init__(self, api_key: str, base_url: str = "https://api.mintlify.com") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        # Assistant API keys use Bearer token authentication
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.request(
                method,
                f"{self.base_url}{path}",
                params=params,
                json=json,
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def search_docs(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search Mintlify documentation using Assistant API.
        
        Note: Assistant API keys (mint_dsc_*) are required.
        The Assistant API uses /v1/assistant/message endpoint for queries.
        """
        # Assistant API uses message endpoint, not search endpoint
        payload = {"message": query}
        return await self._request("POST", "/v1/assistant/message", json=payload)

    async def get_page(self, slug: str) -> Dict[str, Any]:
        """Get a specific documentation page by slug."""
        return await self._request("GET", f"/v1/pages/{slug}")


__all__ = ["MintlifyMCPServer"]

