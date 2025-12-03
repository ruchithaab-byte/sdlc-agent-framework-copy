"""Session Manager for multi-repository context orchestration.

Provides the ContextOrchestrator class that coordinates routing, repository
configuration, and tool setup for agent sessions.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from config.agent_config import PROJECT_ROOT, resolve_model_config
from src.orchestrator.registry import RepoRegistry, RepoConfig, RepoNotFoundError
from src.orchestrator.router import RepoRouter, RoutingError
from src.orchestrator.discovery import RepositoryDiscovery
from src.mcp_servers.github_server import GitHubMCPServer, GitHubServerError
from src.mcp_servers.linear_server import LinearMCPServer
from src.mcp_servers.navigation_server import NavigationMCPServer
from src.execution.docker_service import DockerExecutionService
from src.config.project_config import ProjectConfig, load_project_config
from src.tools.registry import ToolRegistry


class SessionContext(BaseModel):
    """
    Pydantic model representing a prepared agent session context.
    
    Contains all the configuration and tools needed to run an agent
    against a specific repository. Enhanced with context injection fields
    to eliminate hallucinations and ensure agents operate on correct repos.
    
    Phase 2 Extension: Now supports sub-agent forking for Context Firewall pattern.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    repo_config: RepoConfig = Field(
        ..., 
        description="Repository configuration for this session"
    )
    repo_id: str = Field(
        ...,
        description="Repository ID that was routed to"
    )
    memory_path: str = Field(
        ...,
        description="Path to repository-specific memory storage"
    )
    tools: List[Callable] = Field(
        default_factory=list,
        description="List of callable tools for the Agent SDK"
    )
    agent_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration dict compatible with ClaudeAgentOptions"
    )
    github_server: Optional[Any] = Field(
        default=None,
        description="GitHubMCPServer instance for this session"
    )
    linear_server: Optional[Any] = Field(
        default=None,
        description="LinearMCPServer instance for this session"
    )
    navigation_server: Optional[Any] = Field(
        default=None,
        description="NavigationMCPServer instance for structural code navigation (Phase 4)"
    )
    docker_service: Optional[Any] = Field(
        default=None,
        description="DockerExecutionService for sandboxed code execution (Phase 5)"
    )
    project_config: Optional[ProjectConfig] = Field(
        default=None,
        description="Target project configuration from .sdlc/config.yaml"
    )
    # Context injection fields (Phase 2)
    linear_ticket_id: Optional[str] = Field(
        default=None,
        description="Linear ticket/issue ID for this session"
    )
    repo_url: Optional[str] = Field(
        default=None,
        description="Full repository URL (e.g., https://github.com/owner/repo)"
    )
    repo_owner: Optional[str] = Field(
        default=None,
        description="Repository owner (e.g., 'ruchithaab-byte')"
    )
    repo_name: Optional[str] = Field(
        default=None,
        description="Repository name (e.g., 'new-auth-bff')"
    )
    current_branch: Optional[str] = Field(
        default=None,
        description="Current branch name (e.g., 'main', 'feature/AGENTIC-19')"
    )
    
    # --- Phase 2: Sub-Agent Support (Context Firewall Pattern) ---
    session_id: Optional[str] = Field(
        default=None,
        description="Unique session ID for this context"
    )
    is_subagent: bool = Field(
        default=False,
        description="Whether this is a sub-agent session (forked from parent)"
    )
    parent_session_id: Optional[str] = Field(
        default=None,
        description="Parent session ID if this is a sub-agent fork"
    )
    isolation_level: str = Field(
        default="full",
        description="Isolation level: 'full' (complete firewall) or 'shared' (partial context sharing)"
    )
    max_turns: int = Field(
        default=50,
        description="Maximum conversation turns (lower for sub-agents to prevent runaway)"
    )
    tokens_consumed: int = Field(
        default=0,
        description="Tokens consumed by this session (tracked for sub-agent cost attribution)"
    )
    
    # --- Phase 3: Tool Registry (Progressive Disclosure) ---
    tool_registry: Optional[Any] = Field(
        default=None,
        description="ToolRegistry instance for progressive tool disclosure (Phase 3)"
    )

    def get_cwd(self) -> str:
        """Get the working directory for the agent."""
        return str(Path(PROJECT_ROOT) / self.repo_config.local_path)
    
    def get_project_context(self) -> Dict[str, Any]:
        """Get project context for prompt template injection."""
        if self.project_config:
            return self.project_config.to_context_dict()
        return {
            "project": {
                "name": self.repo_config.id,
                "type": "unknown",
                "description": self.repo_config.description,
                "tech_stack": {},
                "skills": [],
            },
            "tech_stack": {},
            "skills": [],
        }
    
    def create_isolated_fork(
        self,
        objective: str,
        tools: List[str],
        max_turns: int = 10,
        max_tokens: int = 30000,
    ) -> 'SessionContext':
        """
        Create an isolated context fork for a sub-agent.
        
        This implements the "Context Firewall" pattern from "No Vibes Allowed":
        - The fork shares configuration (repo, memory, servers) with parent
        - The fork starts with a PRISTINE conversation history (no context pollution)
        - Only specified tools are available (Principle of Least Privilege)
        - The fork has lower resource limits to prevent runaway execution
        
        The "Context Tax" is paid by the sub-agent, not the parent. Only the
        distilled summary returns to the parent context.
        
        Args:
            objective: What the sub-agent should accomplish
            tools: List of tool names the sub-agent can use (filtered from parent tools)
            max_turns: Maximum conversation turns (default: 10, much lower than parent's 50)
            max_tokens: Maximum tokens for sub-agent (default: 30000)
            
        Returns:
            New SessionContext for the sub-agent with isolated context
            
        Example:
            >>> # Main agent needs to search codebase
            >>> sub_context = session.create_isolated_fork(
            ...     objective="Find all authentication-related files",
            ...     tools=["Read", "Grep", "Glob", "list_symbols"],
            ...     max_turns=10
            ... )
            >>> # Run sub-agent with sub_context
            >>> # Only summary returns to main agent
        """
        # Generate unique session ID for the fork
        fork_session_id = f"{self.session_id or 'main'}-sub-{uuid.uuid4().hex[:8]}"
        
        # Filter tools to only those specified (Principle of Least Privilege)
        filtered_tools = [
            tool for tool in self.tools
            if tool.__name__ in tools
        ]
        
        # Create fork with shared config but isolated execution
        return SessionContext(
            # Genealogy
            session_id=fork_session_id,
            parent_session_id=self.session_id,
            is_subagent=True,
            isolation_level="full",
            
            # Shared configuration (inherited from parent)
            repo_config=self.repo_config,
            repo_id=self.repo_id,
            memory_path=self.memory_path,  # Share memory bank
            project_config=self.project_config,
            
            # Context injection (inherited)
            repo_url=self.repo_url,
            repo_owner=self.repo_owner,
            repo_name=self.repo_name,
            current_branch=self.current_branch,
            linear_ticket_id=self.linear_ticket_id,
            
            # Filtered tools (Principle of Least Privilege)
            tools=filtered_tools,
            
            # MCP servers (shared references - context will be injected separately)
            github_server=self.github_server,
            linear_server=self.linear_server,
            
            # Agent config (will be overridden with sub-agent specific settings)
            agent_config={
                **self.agent_config,
                "max_turns": max_turns,
                "max_tokens": max_tokens,
            },
            
            # Resource limits (much lower than parent)
            max_turns=max_turns,
            tokens_consumed=0,  # Fresh counter
            
            # CRITICAL: Do NOT copy conversation history or accumulated context
            # The fork starts with a clean slate - this is the "Context Firewall"
        )


class SessionError(Exception):
    """Raised when session preparation fails."""
    pass


class ContextOrchestrator:
    """
    Orchestrates context preparation for multi-repository agent sessions.
    
    Coordinates the Registry (data), Router (decision), and Session Manager
    (configuration) components to prepare a complete agent session context
    based on a user's prompt.
    
    This implements the standard "Router Pattern" from Anthropic's best practices:
    1. User Input -> Router (LLM classifies)
    2. Router -> Session Manager (loads config)
    3. Session Manager -> Agent (with tools and context)
    """

    def __init__(
        self,
        registry: RepoRegistry,
        router: Optional[RepoRouter] = None,
        *,
        model_profile: str = "vertex-strategy",
        enable_discovery: bool = True,
    ) -> None:
        """
        Initialize the ContextOrchestrator.
        
        Args:
            registry: RepoRegistry instance for repository lookups.
            router: Optional RepoRouter instance for prompt classification.
            model_profile: Model profile to use for agent configuration.
                          Options: "vertex-strategy", "vertex-build", "strategy", "build".
                          Defaults to "vertex-strategy" for Vertex AI (Gemini).
            enable_discovery: Enable dynamic repository discovery from multiple sources.
        """
        self.registry = registry
        self.router = router
        self.model_profile = model_profile
        self.enable_discovery = enable_discovery
        
        # Initialize discovery if enabled
        self.discovery = None
        if enable_discovery:
            self.discovery = RepositoryDiscovery(
                backstage_url=os.getenv("BACKSTAGE_URL"),
                github_token=os.getenv("GITHUB_TOKEN"),
                linear_api_key=os.getenv("LINEAR_API_KEY"),
                linear_team_id=os.getenv("LINEAR_TEAM_ID"),
            )

    def _ensure_memory_path(
        self, 
        repo_config: RepoConfig,
        project_config: Optional[ProjectConfig] = None,
    ) -> str:
        """
        Ensure the memory path exists for a repository.
        
        Standard path (always used): target_repo/.sdlc/memories/
        
        This ensures memories are stored with the target project, making them:
        - Version controlled with the project
        - Portable across environments
        - Isolated per project
        
        Args:
            repo_config: Repository configuration.
            project_config: Optional project configuration from target.
            
        Returns:
            str: Absolute path to the memory directory (.sdlc/memories/).
        """
        target_dir = Path(PROJECT_ROOT) / repo_config.local_path
        
        if project_config:
            # Use configured memory path (default: .sdlc/memories/)
            memory_path = project_config.get_memory_path(target_dir)
        else:
            # Always use .sdlc/memories/ for consistency
            # This ensures all projects use the same structure
            memory_path = target_dir / ".sdlc" / "memories"
        
        memory_path.mkdir(parents=True, exist_ok=True)
        return str(memory_path)
    
    def _load_project_config(self, repo_config: RepoConfig) -> Optional[ProjectConfig]:
        """
        Load project configuration from target repository.
        
        Args:
            repo_config: Repository configuration.
            
        Returns:
            ProjectConfig if found, None otherwise.
        """
        target_dir = Path(PROJECT_ROOT) / repo_config.local_path
        return load_project_config(target_dir)

    def _build_agent_config(
        self,
        repo_config: RepoConfig,
        memory_path: str,
    ) -> Dict[str, Any]:
        """
        Build agent configuration compatible with ClaudeAgentOptions.
        
        Args:
            repo_config: Repository configuration.
            memory_path: Path to memory storage.
            
        Returns:
            Dict[str, Any]: Configuration dict for agent initialization.
        """
        model_config = resolve_model_config(self.model_profile)
        
        return {
            "cwd": str(Path(PROJECT_ROOT) / repo_config.local_path),
            "setting_sources": ["user", "project"],
            "allowed_tools": model_config.allowed_tools,
            "model": model_config.name,
            "memory_path": memory_path,
            "repo_id": repo_config.id,
            "repo_branch": repo_config.branch,
        }

    async def prepare_session_with_discovery(
        self,
        user_prompt: str,
        *,
        linear_issue_id: Optional[str] = None,
    ) -> SessionContext:
        """
        Prepare session with dynamic repository discovery.
        
        This method attempts to discover repositories from multiple sources:
        1. Linear issue (if provided)
        2. Backstage catalog
        3. GitHub organization
        4. Static registry (fallback)
        
        Args:
            user_prompt: The user's task description.
            linear_issue_id: Optional Linear issue ID to extract repo from.
            
        Returns:
            SessionContext: Complete session context with tools and configuration.
        """
        repo_id = None
        repo_config = None
        
        # Step 1: Try discovery if enabled
        if self.enable_discovery and self.discovery:
            try:
                # Try to discover from Linear issue first
                if linear_issue_id:
                    repo_config = await self.discovery.discover_from_linear_issue(linear_issue_id)
                    if repo_config:
                        repo_id = repo_config.id
                        # Auto-register in registry if not exists
                        if repo_id not in self.registry:
                            self._register_discovered_repo(repo_config)
                
                # If not found, try to extract repo name from prompt
                if not repo_config:
                    # Extract potential repo name from prompt
                    import re
                    patterns = [
                        r"in\s+([\w-]+)",
                        r"repo:\s*([\w-]+)",
                        r"repository:\s*([\w-]+)",
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, user_prompt, re.IGNORECASE)
                        if match:
                            potential_repo = match.group(1)
                            repo_config = await self.discovery.discover(potential_repo)
                            if repo_config:
                                repo_id = repo_config.id
                                if repo_id not in self.registry:
                                    self._register_discovered_repo(repo_config)
                                break
            except Exception as e:
                print(f"⚠️  Discovery failed: {e}, falling back to static registry")
        
        # Step 2: Fall back to router or static registry
        if not repo_config:
            if self.router:
                try:
                    repo_id = self.router.route(user_prompt)
                    repo_config = self.registry.get_repo(repo_id)
                except (RoutingError, RepoNotFoundError) as e:
                    # Router failed - try to extract repo from prompt or use fallback
                    print(f"⚠️  Router failed: {e}, trying fallback")
                    # Try to find repo in registry by name from prompt
                    import re
                    repo_match = re.search(r'\b([\w-]+)\b', user_prompt)
                    if repo_match:
                        potential_repo = repo_match.group(1)
                        try:
                            repo_config = self.registry.get_repo(potential_repo)
                            print(f"✅ Found repo in registry: {potential_repo}")
                        except RepoNotFoundError:
                            pass
                    
                    if not repo_config:
                        raise SessionError(f"Failed to route or find repository: {e}")
            else:
                raise SessionError("No router available and discovery failed")
        else:
            # Use discovered repo
            repo_id = repo_config.id
        
        # Continue with standard session preparation
        return self._prepare_session_for_repo_config(repo_config, repo_id)
    
    def _register_discovered_repo(self, repo_config: RepoConfig) -> None:
        """Register a discovered repository in the registry."""
        # Add to in-memory registry
        self.registry._repos[repo_config.id] = repo_config
        print(f"✅ Auto-registered discovered repository: {repo_config.id}")
    
    def _prepare_session_for_repo_config(
        self,
        repo_config: RepoConfig,
        repo_id: str,
    ) -> SessionContext:
        """
        Internal method to prepare session from repo config.
        
        Phase 3: Implements Progressive Tool Disclosure pattern.
        Instead of loading all tool schemas upfront (~10k tokens), we:
        1. Register all tools in a ToolRegistry
        2. Only expose meta-tools (list, get_schema, search) initially (~200 tokens)
        3. Agent discovers other tools on-demand
        """
        # Load project config from target repository
        project_config = self._load_project_config(repo_config)
        
        # Phase 3: Initialize Tool Registry for Progressive Disclosure
        tool_registry = ToolRegistry(workspace_path=str(Path(PROJECT_ROOT) / repo_config.local_path))
        
        # Initialize GitHub MCP Server
        github_token = os.getenv("GITHUB_TOKEN")
        github_server = None
        
        if github_token:
            try:
                github_server = GitHubMCPServer(
                    repo_url=repo_config.github_url,
                    token=github_token,
                )
                # Phase 3: Register in registry instead of direct tools list
                github_tools = github_server.get_tools()
                tool_registry.register_mcp_server("github", 
                    [{"name": t.__name__, "description": t.__doc__ or f"GitHub: {t.__name__}"} 
                     for t in github_tools]
                )
            except GitHubServerError as e:
                print(f"Warning: Failed to initialize GitHub server: {e}")
        
        # Initialize Linear MCP Server
        linear_api_key = os.getenv("LINEAR_API_KEY")
        linear_team_id = os.getenv("LINEAR_TEAM_ID")
        linear_server = None
        
        if linear_api_key and linear_team_id:
            try:
                linear_server = LinearMCPServer(
                    api_key=linear_api_key,
                    team_id=linear_team_id,
                )
                # Phase 3: Register in registry instead of direct tools list
                linear_tools = linear_server.get_tools()
                tool_registry.register_mcp_server("linear",
                    [{"name": t.__name__, "description": t.__doc__ or f"Linear: {t.__name__}"}
                     for t in linear_tools]
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Linear server: {e}")
        
        # --- Phase 4: Initialize Navigation Server (Gap 1 Fix) ---
        # This provides LSP-grade structural navigation:
        # - list_symbols: Get all symbols in a file
        # - find_definition: Go to Definition (file:line)
        # - find_references: Find all References to a symbol
        # - get_call_graph: Build dependency graph
        navigation_server = None
        try:
            workspace_path = str(Path(PROJECT_ROOT) / repo_config.local_path)
            navigation_server = NavigationMCPServer(
                workspace_path=workspace_path,
                use_ctags=True,  # Enable ctags if available
                use_tree_sitter=True,  # Enable tree-sitter if available
            )
            # Register navigation tools in registry
            navigation_tools = navigation_server.get_tools()
            tool_registry.register_mcp_server("navigation",
                [{"name": t.__name__, "description": t.__doc__ or f"Navigation: {t.__name__}"}
                 for t in navigation_tools]
            )
        except Exception as e:
            print(f"Warning: Failed to initialize Navigation server: {e}")
            # Non-critical - agent can still work without structural navigation
        
        # --- Phase 5: Initialize Docker Execution Service (Code Execution) ---
        # This enables the shift from "Tool Calling" (JSON Ping-Pong) to
        # "Code Execution" (Batch Scripting), achieving ~98% token reduction.
        # 
        # Security: Only enabled if repo_config.enable_code_execution = True
        # PII Protection: Automatic filtering via PrivacyFilter (enabled by default)
        docker_service = None
        if repo_config.enable_code_execution:
            try:
                workspace_path = str(Path(PROJECT_ROOT) / repo_config.local_path)
                docker_service = DockerExecutionService(
                    enable_pii_filtering=True,  # Always filter PII
                )
                
                # Register execution tools in registry
                # Note: We register the capability, not the raw execute_script method
                # Agents should use BatchRunner for most operations
                from src.execution.batch_runner import BatchRunner
                batch_runner = BatchRunner(docker_service)
                
                tool_registry.register_tool(
                    name="batch_process_files",
                    description="Process multiple files with a single script (replaces N individual tool calls)",
                    category=tool_registry.ToolCategory.EXECUTION if hasattr(tool_registry, 'ToolCategory') else "execution",
                    path="execution/batch_process_files",
                    read_only=False,
                    requires_confirmation=True,
                )
                
                tool_registry.register_tool(
                    name="batch_search",
                    description="Search across multiple directories with a single execution",
                    category=tool_registry.ToolCategory.EXECUTION if hasattr(tool_registry, 'ToolCategory') else "execution",
                    path="execution/batch_search",
                    read_only=True,
                    requires_confirmation=False,
                )
                
            except Exception as e:
                print(f"Warning: Failed to initialize Docker execution: {e}")
                # Non-critical - agent can fall back to individual tool calls
        
        # Phase 3: Progressive Disclosure - Only expose meta-tools initially
        # This reduces initial context from ~10k tokens to ~200 tokens
        # Agent can discover other tools by:
        # - list_categories() -> ["file", "code", "navigation", "git", "mcp"]
        # - list_tools(category="github") -> [list of GitHub tools]
        # - get_tool_schema("create_pull_request") -> full schema loaded on-demand
        # - search_tools("pull request") -> semantic search for relevant tools
        meta_tools: List[Callable] = tool_registry.get_meta_tools()
        
        # Ensure memory path exists
        memory_path = self._ensure_memory_path(repo_config, project_config)
        
        # Build agent configuration
        agent_config = self._build_agent_config(repo_config, memory_path)
        
        return SessionContext(
            repo_config=repo_config,
            repo_id=repo_id,
            memory_path=memory_path,
            tools=meta_tools,  # Phase 3: Only meta-tools, not all tools
            agent_config=agent_config,
            github_server=github_server,
            linear_server=linear_server,
            navigation_server=navigation_server,  # Phase 4: Structural navigation
            docker_service=docker_service,        # Phase 5: Code execution
            project_config=project_config,
            tool_registry=tool_registry,          # Phase 3: Registry for on-demand discovery
        )

    def prepare_session(self, user_prompt: str) -> SessionContext:
        """
        Prepare a complete session context for an agent based on user prompt.
        
        This is the main entry point for the orchestrator. It:
        1. Routes the prompt to the appropriate repository
        2. Loads the repository configuration
        3. Loads project config from target's .sdlc/config.yaml
        4. Initializes the GitHub MCP server
        5. Extracts tools from the server
        6. Returns a complete SessionContext
        
        Args:
            user_prompt: The user's task description.
            
        Returns:
            SessionContext: Complete session context with tools and configuration.
            
        Raises:
            SessionError: If session preparation fails at any step.
        """
        # Use discovery if enabled, otherwise use router
        if self.enable_discovery and self.discovery:
            # Try synchronous discovery (extract repo name from prompt)
            import re
            patterns = [
                r"in\s+([\w-]+)",
                r"repo:\s*([\w-]+)",
                r"repository:\s*([\w-]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, user_prompt, re.IGNORECASE)
                if match:
                    potential_repo = match.group(1)
                    try:
                        repo_config = self.registry.get_repo(potential_repo)
                        return self._prepare_session_for_repo_config(repo_config, potential_repo)
                    except RepoNotFoundError:
                        pass
        
        # Step 1: Route the prompt to the appropriate repository
        if not self.router:
            raise SessionError("No router available for routing")
        
        try:
            repo_id = self.router.route(user_prompt)
        except RoutingError as e:
            raise SessionError(f"Failed to route prompt: {e}")
        
        # Step 2: Get repository configuration
        try:
            repo_config = self.registry.get_repo(repo_id)
        except Exception as e:
            raise SessionError(f"Failed to get repository config: {e}")
        
        # Use internal method to prepare session
        return self._prepare_session_for_repo_config(repo_config, repo_id)

    def prepare_session_for_repo(self, repo_id: str) -> SessionContext:
        """
        Prepare a session context for a specific repository (bypass routing).
        
        Use this method when you already know which repository to target.
        
        Phase 3: Now uses Progressive Tool Disclosure pattern.
        
        Args:
            repo_id: The repository ID to prepare session for.
            
        Returns:
            SessionContext: Complete session context with tools and configuration.
        """
        # Get repository configuration directly
        try:
            repo_config = self.registry.get_repo(repo_id)
        except Exception as e:
            raise SessionError(f"Failed to get repository config: {e}")
        
        # Phase 3: Delegate to _prepare_session_for_repo_config for consistency
        # This ensures all sessions use the same Progressive Disclosure pattern
        return self._prepare_session_for_repo_config(repo_config, repo_id)

    def list_repositories(self) -> List[Dict[str, str]]:
        """
        List all available repositories.
        
        Returns:
            List[Dict[str, str]]: List of repository info dicts.
        """
        return [
            {
                "id": repo.id,
                "description": repo.description[:100] + "..." if len(repo.description) > 100 else repo.description,
                "github_url": repo.github_url,
            }
            for repo in self.registry.get_all_repos()
        ]


__all__ = [
    "SessionContext",
    "SessionError",
    "ContextOrchestrator",
]

