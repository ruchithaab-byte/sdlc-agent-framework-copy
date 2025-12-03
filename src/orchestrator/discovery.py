"""
Dynamic Repository Discovery

Provides multiple sources for discovering repositories:
1. Backstage Catalog - Primary source for scaffolder-created repos
2. GitHub Organization - Fallback for org-wide discovery
3. Linear Issues - Extract repo info from Linear tasks
4. GitHub Webhooks - Real-time registration

This enables agents to work with repositories without manual registry updates.
"""

from __future__ import annotations

import os
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import aiohttp

from src.mcp_servers.backstage_server import BackstageMCPServer
from src.mcp_servers.linear_server import LinearMCPServer
from src.orchestrator.registry import RepoConfig, RepoNotFoundError


class RepositoryDiscovery:
    """Multi-source repository discovery."""
    
    def __init__(
        self,
        backstage_url: Optional[str] = None,
        github_token: Optional[str] = None,
        linear_api_key: Optional[str] = None,
        linear_team_id: Optional[str] = None,
    ):
        """
        Initialize repository discovery.
        
        Args:
            backstage_url: Backstage catalog URL
            github_token: GitHub personal access token
            linear_api_key: Linear API key
            linear_team_id: Linear team ID
        """
        self.backstage = None
        if backstage_url:
            self.backstage = BackstageMCPServer(base_url=backstage_url)
        
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.linear = None
        if linear_api_key and linear_team_id:
            self.linear = LinearMCPServer(
                api_key=linear_api_key,
                team_id=linear_team_id
            )
    
    async def discover_from_backstage(self, repo_name: str) -> Optional[RepoConfig]:
        """
        Discover repository from Backstage catalog.
        
        Args:
            repo_name: Repository name or identifier
            
        Returns:
            RepoConfig if found, None otherwise
        """
        if not self.backstage:
            return None
        
        try:
            # Query Backstage catalog
            result = await self.backstage.catalog_lookup(
                kind="Component",
                query=repo_name
            )
            
            entities = result.get("items", [])
            for entity in entities:
                if entity.get("metadata", {}).get("name") == repo_name:
                    spec = entity.get("spec", {})
                    source_location = spec.get("sourceLocation", "")
                    
                    if source_location.startswith("url:"):
                        github_url = source_location[4:].strip()
                    else:
                        github_url = source_location
                    
                    return RepoConfig(
                        id=repo_name,
                        description=entity.get("metadata", {}).get("description", ""),
                        github_url=github_url,
                        local_path=f"./repos/{repo_name}",
                        branch="main"
                    )
        except Exception:
            pass
        
        return None
    
    async def discover_from_github(self, repo_identifier: str) -> Optional[RepoConfig]:
        """
        Discover repository from GitHub.
        
        Args:
            repo_identifier: Repository name, full name (org/repo), or URL
            
        Returns:
            RepoConfig if found, None otherwise
        """
        if not self.github_token:
            return None
        
        # Parse identifier
        if repo_identifier.startswith("http"):
            # Full URL
            parsed = urlparse(repo_identifier)
            org_repo = parsed.path.strip("/")
        elif "/" in repo_identifier:
            # org/repo format
            org_repo = repo_identifier
        else:
            # Just repo name - need to find org
            # Try common patterns
            org_repo = f"ruchithaab-byte/{repo_identifier}"
        
        try:
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.github.com/repos/{org_repo}",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        repo_data = await resp.json()
                        
                        return RepoConfig(
                            id=repo_data["name"],
                            description=repo_data.get("description", ""),
                            github_url=repo_data["html_url"],
                            local_path=f"./repos/{repo_data['name']}",
                            branch=repo_data.get("default_branch", "main")
                        )
        except Exception:
            pass
        
        return None
    
    async def discover_from_linear_issue(self, issue_id: str) -> Optional[RepoConfig]:
        """
        Extract repository information from Linear issue.
        
        Args:
            issue_id: Linear issue ID or identifier (can be UUID or identifier like AGENTIC-10)
            
        Returns:
            RepoConfig if found, None otherwise
        """
        if not self.linear:
            return None
        
        try:
            # Query Linear issue - handle both UUID and identifier
            query = """
            query GetIssue($id: String!) {
              issue(id: $id) {
                id
                identifier
                title
                description
                labels {
                  nodes {
                    name
                  }
                }
              }
            }
            """
            
            headers = {
                "Authorization": self.linear.api_key,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Try with identifier first (e.g., AGENTIC-10)
                async with session.post(
                    "https://api.linear.app/graphql",
                    json={"query": query, "variables": {"id": issue_id}},
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Check for errors
                        if "errors" in data:
                            # Try querying by identifier
                            query_by_identifier = """
                            query GetIssueByIdentifier($identifier: String!) {
                              issue(identifier: $identifier) {
                                id
                                identifier
                                title
                                description
                                labels {
                                  nodes {
                                    name
                                  }
                                }
                              }
                            }
                            """
                            async with session.post(
                                "https://api.linear.app/graphql",
                                json={"query": query_by_identifier, "variables": {"identifier": issue_id}},
                                headers=headers
                            ) as resp2:
                                if resp2.status == 200:
                                    data = await resp2.json()
                        
                        issue = data.get("data", {}).get("issue")
                        
                        if issue:
                            # Extract repo from description, title, or labels
                            repo_name = self._extract_repo_name(issue)
                            
                            if repo_name:
                                # Try to discover the repo
                                return await self.discover_from_github(repo_name)
        except Exception as e:
            print(f"⚠️  Error discovering from Linear issue: {e}")
        
        return None
    
    def _extract_repo_name(self, issue: Dict[str, Any]) -> Optional[str]:
        """Extract repository name from Linear issue."""
        # Try description first (most detailed)
        description = issue.get("description", "")
        if description:
            # Look for patterns like "in new-agent-service" or "repo: new-agent-service"
            patterns = [
                r"repo[:\s]+([\w-]+(?:-service|-bff|-api|-dashboard))",
                r"repository[:\s]+([\w-]+(?:-service|-bff|-api|-dashboard))",
                r"in\s+([\w-]+(?:-service|-bff|-api|-dashboard))",
                r"service[:\s]+([\w-]+(?:-service|-bff|-api|-dashboard))",
                r"github\.com/[\w-]+/([\w-]+)",
                r"repository\s+([\w-]+(?:-service|-bff|-api|-dashboard))",
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, description, re.IGNORECASE)
                for match in matches:
                    repo_name = match if isinstance(match, str) else match[0] if match else None
                    if repo_name and repo_name.lower() not in ["the", "a", "an", "this", "that", "new"]:
                        return repo_name
        
        # Try title (often contains repo name)
        title = issue.get("title", "")
        if title:
            # Look for patterns in title
            patterns = [
                r"in\s+([\w-]+(?:-service|-bff|-api|-dashboard))",
                r"\[([\w-]+(?:-service|-bff|-api|-dashboard))\]",
                r"([\w-]+(?:-service|-bff|-api|-dashboard))",
            ]
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    repo_name = match.group(1)
                    if repo_name.lower() not in ["the", "a", "an", "this", "that"]:
                        return repo_name
        
        # Try labels (last resort)
        labels = issue.get("labels", {}).get("nodes", [])
        for label in labels:
            label_name = label.get("name", "")
            # Check if label looks like a repo name
            if re.match(r"^[\w-]+(?:-service|-bff|-api|-dashboard)$", label_name, re.IGNORECASE):
                return label_name
        
        return None
    
    async def discover(
        self,
        identifier: str,
        *,
        linear_issue_id: Optional[str] = None,
    ) -> Optional[RepoConfig]:
        """
        Discover repository from multiple sources.
        
        Priority:
        1. Backstage catalog (if enabled)
        2. Linear issue (if issue_id provided)
        3. GitHub (direct lookup)
        
        Args:
            identifier: Repository name, URL, or identifier
            linear_issue_id: Optional Linear issue ID to extract repo from
            
        Returns:
            RepoConfig if found, None otherwise
        """
        # Try Linear issue first if provided
        if linear_issue_id:
            repo = await self.discover_from_linear_issue(linear_issue_id)
            if repo:
                return repo
        
        # Try Backstage
        if self.backstage:
            repo = await self.discover_from_backstage(identifier)
            if repo:
                return repo
        
        # Try GitHub
        repo = await self.discover_from_github(identifier)
        if repo:
            return repo
        
        return None


__all__ = ["RepositoryDiscovery"]

