"""GitHub MCP Server for repository operations.

Provides tools for GitHub operations including file reading, branch management,
commits, and pull request creation. Uses PyGithub with async wrappers.
"""

from __future__ import annotations

import asyncio
import base64
import os
import re
from typing import Any, Callable, Dict, List, Optional

from github import Github, GithubException, Auth

from src.tracing import trace_run, RunType


class GitHubServerError(Exception):
    """Raised when a GitHub operation fails."""
    pass


class GitHubMCPServer:
    """
    MCP Server for GitHub repository operations.
    
    Provides async methods for common GitHub operations like reading files,
    creating branches, making commits, and creating pull requests.
    
    Note: PyGithub is synchronous, so all operations are wrapped with
    asyncio.to_thread() to prevent blocking the event loop.
    """

    def __init__(
        self,
        repo_url: str,
        *,
        token: Optional[str] = None,
    ) -> None:
        """
        Initialize the GitHubMCPServer.
        
        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
            token: GitHub personal access token. Defaults to GITHUB_TOKEN env var.
        """
        self._token = token or os.getenv("GITHUB_TOKEN")
        if not self._token:
            raise GitHubServerError(
                "GITHUB_TOKEN not found. Set the environment variable or pass token parameter."
            )
        
        # Parse owner and repo from URL
        self._owner, self._repo_name = self._parse_repo_url(repo_url)
        self._repo_url = repo_url
        
        # Initialize GitHub client
        auth = Auth.Token(self._token)
        self._github = Github(auth=auth)
        
        # Lazy-load repository object
        self._repo = None
        
        # Context injection (Phase 2)
        self._context: Optional[Dict[str, Any]] = None

    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set session context for tool operations.
        
        This method binds the server to a specific repository/branch context,
        preventing hallucinations and ensuring tools operate on the correct repo.
        
        Args:
            context: Session context dict with keys:
                - repo_url: Full repository URL
                - repo_owner: Repository owner
                - repo_name: Repository name
                - current_branch: Current branch name
        """
        self._context = context
        
        # Update repo URL if provided in context
        if context.get("repo_url"):
            self._owner, self._repo_name = self._parse_repo_url(context["repo_url"])
            self._repo_url = context["repo_url"]
            # Reset cached repo to force re-initialization
        self._repo = None

    @staticmethod
    def _parse_repo_url(url: str) -> tuple[str, str]:
        """
        Parse owner and repository name from a GitHub URL.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            tuple[str, str]: (owner, repo_name)
        """
        # Handle various URL formats
        patterns = [
            r"github\.com[:/]([^/]+)/([^/\.]+)",  # https://github.com/owner/repo or git@github.com:owner/repo
            r"^([^/]+)/([^/]+)$",  # owner/repo format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2).rstrip(".git")
        
        raise GitHubServerError(f"Could not parse repository URL: {url}")

    def _get_repo(self):
        """Get or lazily initialize the repository object."""
        if self._repo is None:
            try:
                self._repo = self._github.get_repo(f"{self._owner}/{self._repo_name}")
            except GithubException as e:
                raise GitHubServerError(f"Failed to access repository: {e}")
        return self._repo

    # =========================================================================
    # Private synchronous methods (called via asyncio.to_thread)
    # =========================================================================

    def _sync_get_file_contents(self, path: str, branch: str) -> Dict[str, Any]:
        """Synchronous implementation of get_file_contents."""
        repo = self._get_repo()
        try:
            content = repo.get_contents(path, ref=branch)
            
            # Handle single file
            if not isinstance(content, list):
                decoded_content = base64.b64decode(content.content).decode("utf-8")
                return {
                    "path": content.path,
                    "content": decoded_content,
                    "sha": content.sha,
                    "size": content.size,
                    "encoding": content.encoding,
                    "url": content.html_url,
                }
            
            # Handle directory
            return {
                "path": path,
                "type": "directory",
                "contents": [
                    {"name": item.name, "path": item.path, "type": item.type}
                    for item in content
                ],
            }
        except GithubException as e:
            raise GitHubServerError(f"Failed to get file contents: {e}")

    def _sync_create_branch(self, new_branch: str, source_branch: str) -> Dict[str, Any]:
        """Synchronous implementation of create_branch."""
        repo = self._get_repo()
        try:
            # Get the SHA of the source branch
            source_ref = repo.get_git_ref(f"heads/{source_branch}")
            source_sha = source_ref.object.sha
            
            # Create new branch
            repo.create_git_ref(f"refs/heads/{new_branch}", source_sha)
            
            return {
                "branch": new_branch,
                "source_branch": source_branch,
                "sha": source_sha,
                "success": True,
            }
        except GithubException as e:
            raise GitHubServerError(f"Failed to create branch: {e}")

    def _sync_create_commit(
        self,
        branch: str,
        path: str,
        content: str,
        message: str,
    ) -> Dict[str, Any]:
        """Synchronous implementation of create_commit."""
        repo = self._get_repo()
        try:
            # Try to get existing file to get its SHA
            sha = None
            try:
                existing = repo.get_contents(path, ref=branch)
                if not isinstance(existing, list):
                    sha = existing.sha
            except GithubException:
                pass  # File doesn't exist, will create new
            
            # Create or update file
            if sha:
                result = repo.update_file(
                    path=path,
                    message=message,
                    content=content,
                    sha=sha,
                    branch=branch,
                )
            else:
                result = repo.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=branch,
                )
            
            return {
                "commit_sha": result["commit"].sha,
                "path": path,
                "branch": branch,
                "message": message,
                "url": result["commit"].html_url,
                "success": True,
            }
        except GithubException as e:
            raise GitHubServerError(f"Failed to create commit: {e}")

    def _sync_create_pull_request(
        self,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
    ) -> Dict[str, Any]:
        """Synchronous implementation of create_pull_request."""
        repo = self._get_repo()
        try:
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
            )
            
            return {
                "pr_number": pr.number,
                "title": pr.title,
                "url": pr.html_url,
                "state": pr.state,
                "head": head_branch,
                "base": base_branch,
                "success": True,
            }
        except GithubException as e:
            raise GitHubServerError(f"Failed to create pull request: {e}")

    # =========================================================================
    # Public async methods (Agent SDK tools)
    # =========================================================================

    @trace_run(name="GitHub: Get File Contents", run_type=RunType.TOOL)
    async def get_file_contents(
        self,
        path: str,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Get file contents from the repository.
        
        Args:
            path: Path to the file in the repository.
            branch: Branch to read from (default: "main").
            
        Returns:
            Dict containing file content, path, sha, and metadata.
        """
        return await asyncio.to_thread(
            self._sync_get_file_contents, path, branch
        )

    @trace_run(name="GitHub: Create Branch", run_type=RunType.TOOL)
    async def create_branch(
        self,
        new_branch: Optional[str] = None,
        source_branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new branch from a source branch.
        
        Uses injected context if parameters are not provided.
        
        Args:
            new_branch: Name of the new branch to create. Uses context if None.
            source_branch: Branch to create from. Uses context.current_branch or "main" if None.
            
        Returns:
            Dict containing branch info and success status.
        """
        # Use context if parameters not provided
        if source_branch is None:
            if self._context and self._context.get("current_branch"):
                source_branch = self._context["current_branch"]
            else:
                source_branch = "main"
        
        if new_branch is None:
            raise ValueError("new_branch is required (not provided and not in context)")
        
        return await asyncio.to_thread(
            self._sync_create_branch, new_branch, source_branch
        )

    @trace_run(name="GitHub: Create Commit", run_type=RunType.TOOL)
    async def create_commit(
        self,
        path: str,
        content: str,
        message: str,
        branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a commit with file changes.
        
        Uses injected context if branch is not provided.
        
        Args:
            path: Path of the file to create/update.
            content: New content for the file.
            message: Commit message.
            branch: Branch to commit to. Uses context.current_branch or "main" if None.
            
        Returns:
            Dict containing commit sha, url, and success status.
        """
        # Use context if branch not provided
        if branch is None:
            if self._context and self._context.get("current_branch"):
                branch = self._context["current_branch"]
            else:
                branch = "main"
        
        return await asyncio.to_thread(
            self._sync_create_commit, branch, path, content, message
        )

    @trace_run(name="GitHub: Create Pull Request", run_type=RunType.TOOL)
    async def create_pull_request(
        self,
        title: str,
        body: str = "",
        head_branch: Optional[str] = None,
        base_branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Uses injected context if branches are not provided.
        
        Args:
            title: PR title.
            body: PR description (optional).
            head_branch: Branch containing the changes. Uses context.current_branch if None.
            base_branch: Branch to merge into. Uses "main" if None.
            
        Returns:
            Dict containing PR number, url, and success status.
        """
        # Use context if branches not provided
        if head_branch is None:
            if self._context and self._context.get("current_branch"):
                head_branch = self._context["current_branch"]
            else:
                raise ValueError("head_branch is required (not provided and not in context)")
        
        if base_branch is None:
            base_branch = "main"
        
        return await asyncio.to_thread(
            self._sync_create_pull_request, head_branch, base_branch, title, body
        )

    # =========================================================================
    # Tool Exposure (Critical for Agent SDK)
    # =========================================================================

    def get_tools(self) -> List[Callable]:
        """
        Returns list of callable tools for Agent SDK consumption.
        
        This method exposes the GitHub operations as tools that can be
        passed directly to the Agent SDK's tools parameter.
        
        Returns:
            List[Callable]: List of async tool methods.
        """
        return [
            self.get_file_contents,
            self.create_branch,
            self.create_commit,
            self.create_pull_request,
        ]

    def close(self) -> None:
        """Close the GitHub client connection."""
        if self._github:
            self._github.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


__all__ = [
    "GitHubMCPServer",
    "GitHubServerError",
]

