"""
Tool Registry with Progressive Disclosure.

Implements the "Tools as Filesystem" pattern:
- Tools organized in virtual directory structure
- Lazy loading of tool schemas
- Semantic tool search
- On-demand schema retrieval

This prevents context saturation from loading all tool definitions upfront.

Reference: "No Vibes Allowed" - Dex Horthy, HumanLayer
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from src.tracing import trace_run, RunType


class ToolCategory(Enum):
    """Categories for organizing tools."""
    FILE = "file"              # File operations (read, write, search)
    CODE = "code"              # Code-specific (edit, format, lint)
    NAVIGATION = "navigation"  # Code navigation (symbols, references)
    EXECUTION = "execution"    # Code execution (bash, docker)
    GIT = "git"                # Git operations
    API = "api"                # External API calls
    ANALYSIS = "analysis"      # Code analysis tools
    MCP = "mcp"                # MCP server tools


@dataclass
class ToolDefinition:
    """Definition of a tool that can be used by agents."""
    name: str
    description: str
    category: ToolCategory
    
    # Schema (loaded lazily)
    schema: Optional[Dict[str, Any]] = None
    schema_loaded: bool = False
    
    # Metadata
    path: str = ""  # Virtual path like "servers/github/get_pr"
    server: Optional[str] = None  # MCP server name if applicable
    version: str = "1.0.0"
    
    # Usage tracking
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    # Capability flags
    read_only: bool = True
    requires_confirmation: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "path": self.path,
            "server": self.server,
            "version": self.version,
            "read_only": self.read_only,
            "requires_confirmation": self.requires_confirmation,
        }
    
    def get_full_schema(self) -> Dict[str, Any]:
        """Get full tool schema for API consumption."""
        if not self.schema:
            return {
                "name": self.name,
                "description": self.description,
                "input_schema": {"type": "object", "properties": {}},
            }
        return self.schema


@dataclass
class ToolSearchResult:
    """Result from searching for tools."""
    tools: List[ToolDefinition]
    query: str
    total_matches: int
    categories_searched: List[ToolCategory] = field(default_factory=list)


class ToolRegistry:
    """
    Registry for available tools with progressive disclosure.
    
    Implements the "Tools as Filesystem" pattern:
    - Tools organized in virtual directory structure
    - Agents can browse categories (list directory)
    - Schema only loaded when agent specifically "reads" a tool
    - Semantic search for finding relevant tools
    
    This prevents context saturation from loading all 50+ tool definitions
    into the system prompt upfront.
    
    Example:
        >>> registry = ToolRegistry()
        >>> 
        >>> # Agent browses tool categories (low token cost)
        >>> categories = registry.list_categories()
        >>> print(categories)
        ['file', 'code', 'navigation', 'execution', 'git', 'api']
        >>> 
        >>> # Agent lists tools in a category (still low cost - no schemas)
        >>> tools = registry.list_tools(category="navigation")
        >>> print([t.name for t in tools])
        ['list_symbols', 'find_definition', 'find_references', 'get_call_graph']
        >>> 
        >>> # Only when agent needs a tool, load its full schema
        >>> schema = registry.get_tool_schema("find_definition")
        >>> # Now schema is in context, ready to use
    """
    
    # Built-in tool definitions (without full schemas - lazy loaded)
    BUILTIN_TOOLS: Dict[str, Dict[str, Any]] = {
        # File tools
        "Read": {
            "description": "Read file contents",
            "category": ToolCategory.FILE,
            "path": "file/read",
            "read_only": True,
        },
        "Write": {
            "description": "Write content to a file",
            "category": ToolCategory.FILE,
            "path": "file/write",
            "read_only": False,
            "requires_confirmation": True,
        },
        "Grep": {
            "description": "Search for patterns in files",
            "category": ToolCategory.FILE,
            "path": "file/grep",
            "read_only": True,
        },
        "Glob": {
            "description": "Find files matching a pattern",
            "category": ToolCategory.FILE,
            "path": "file/glob",
            "read_only": True,
        },
        
        # Code tools
        "search_and_replace": {
            "description": "Edit file using unique anchor block (NOT line numbers)",
            "category": ToolCategory.CODE,
            "path": "code/edit",
            "read_only": False,
            "requires_confirmation": True,
        },
        
        # Navigation tools
        "list_symbols": {
            "description": "List all symbols (classes, functions) in a file",
            "category": ToolCategory.NAVIGATION,
            "path": "navigation/list_symbols",
            "read_only": True,
        },
        "find_definition": {
            "description": "Find where a symbol is defined",
            "category": ToolCategory.NAVIGATION,
            "path": "navigation/find_definition",
            "read_only": True,
        },
        "find_references": {
            "description": "Find all references to a symbol",
            "category": ToolCategory.NAVIGATION,
            "path": "navigation/find_references",
            "read_only": True,
        },
        "get_call_graph": {
            "description": "Build dependency graph for a function",
            "category": ToolCategory.NAVIGATION,
            "path": "navigation/get_call_graph",
            "read_only": True,
        },
        
        # Execution tools
        "Bash": {
            "description": "Execute bash commands",
            "category": ToolCategory.EXECUTION,
            "path": "execution/bash",
            "read_only": False,
            "requires_confirmation": True,
        },
        "execute_script": {
            "description": "Execute script in Docker container",
            "category": ToolCategory.EXECUTION,
            "path": "execution/docker",
            "read_only": False,
            "requires_confirmation": True,
        },
        
        # Git tools
        "git_status": {
            "description": "Get git repository status",
            "category": ToolCategory.GIT,
            "path": "git/status",
            "read_only": True,
        },
        "git_diff": {
            "description": "Get diff of changes",
            "category": ToolCategory.GIT,
            "path": "git/diff",
            "read_only": True,
        },
        "git_commit": {
            "description": "Create a commit",
            "category": ToolCategory.GIT,
            "path": "git/commit",
            "read_only": False,
            "requires_confirmation": True,
        },
        "create_pull_request": {
            "description": "Create a pull request",
            "category": ToolCategory.GIT,
            "path": "git/create_pr",
            "read_only": False,
            "requires_confirmation": True,
        },
    }
    
    def __init__(
        self,
        workspace_path: Optional[str] = None,
        lazy_loading: bool = True,
    ):
        """
        Initialize the Tool Registry.
        
        Args:
            workspace_path: Path to workspace for MCP server discovery.
            lazy_loading: If True, schemas loaded on demand.
        """
        self.workspace_path = Path(workspace_path) if workspace_path else None
        self.lazy_loading = lazy_loading
        
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
        self._loaded_schemas: Set[str] = set()
        
        # Schema loaders (injected)
        self._schema_loaders: Dict[str, Callable[[str], Dict[str, Any]]] = {}
        
        # Initialize with builtin tools
        self._register_builtin_tools()
    
    def _register_builtin_tools(self) -> None:
        """Register the builtin tools."""
        for name, config in self.BUILTIN_TOOLS.items():
            tool = ToolDefinition(
                name=name,
                description=config["description"],
                category=config["category"],
                path=config["path"],
                read_only=config.get("read_only", True),
                requires_confirmation=config.get("requires_confirmation", False),
            )
            self._tools[name] = tool
            self._categories[tool.category].append(name)
    
    def register_tool(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        *,
        path: Optional[str] = None,
        server: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        read_only: bool = True,
        requires_confirmation: bool = False,
    ) -> ToolDefinition:
        """
        Register a new tool.
        
        Args:
            name: Tool name.
            description: Brief description.
            category: Tool category.
            path: Virtual path (defaults to category/name).
            server: MCP server name if applicable.
            schema: Full tool schema (optional, can be loaded later).
            read_only: Whether tool is read-only.
            requires_confirmation: Whether tool requires user confirmation.
            
        Returns:
            The registered ToolDefinition.
        """
        if path is None:
            path = f"{category.value}/{name}"
        
        tool = ToolDefinition(
            name=name,
            description=description,
            category=category,
            path=path,
            server=server,
            schema=schema,
            schema_loaded=schema is not None,
            read_only=read_only,
            requires_confirmation=requires_confirmation,
        )
        
        self._tools[name] = tool
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        return tool
    
    def register_mcp_server(
        self,
        server_name: str,
        tools: List[Dict[str, Any]],
    ) -> List[ToolDefinition]:
        """
        Register tools from an MCP server.
        
        Args:
            server_name: Name of the MCP server.
            tools: List of tool definitions from the server.
            
        Returns:
            List of registered ToolDefinition objects.
        """
        registered = []
        
        for tool_config in tools:
            tool = self.register_tool(
                name=tool_config["name"],
                description=tool_config.get("description", ""),
                category=ToolCategory.MCP,
                path=f"servers/{server_name}/{tool_config['name']}",
                server=server_name,
                schema=tool_config.get("input_schema"),
            )
            registered.append(tool)
        
        return registered
    
    def list_categories(self) -> List[str]:
        """
        List available tool categories.
        
        This is the entry point for agents to browse tools.
        Returns only category names - minimal token cost.
        
        Returns:
            List of category names.
        """
        return [cat.value for cat in ToolCategory if self._categories[cat]]
    
    def list_tools(
        self,
        category: Optional[str] = None,
        *,
        include_schemas: bool = False,
    ) -> List[ToolDefinition]:
        """
        List tools, optionally filtered by category.
        
        By default, returns tools WITHOUT full schemas (low token cost).
        Set include_schemas=True to get full schemas (higher cost).
        
        Args:
            category: Optional category filter.
            include_schemas: Whether to include full schemas.
            
        Returns:
            List of ToolDefinition objects.
        """
        if category:
            try:
                cat = ToolCategory(category)
                tool_names = self._categories[cat]
            except ValueError:
                return []
        else:
            tool_names = list(self._tools.keys())
        
        tools = [self._tools[name] for name in tool_names if name in self._tools]
        
        # Load schemas if requested
        if include_schemas:
            for tool in tools:
                if not tool.schema_loaded:
                    self._load_schema(tool)
        
        return tools
    
    @trace_run(name="Registry: Get Tool Schema", run_type=RunType.TOOL)
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the full schema for a tool.
        
        This is called when an agent specifically needs to use a tool.
        Implements lazy loading - schema is only loaded when needed.
        
        Args:
            tool_name: Name of the tool.
            
        Returns:
            Full tool schema, or None if tool not found.
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return None
        
        # Load schema if not already loaded
        if not tool.schema_loaded:
            self._load_schema(tool)
        
        # Track usage
        tool.usage_count += 1
        tool.last_used = datetime.utcnow()
        self._loaded_schemas.add(tool_name)
        
        return tool.get_full_schema()
    
    def _load_schema(self, tool: ToolDefinition) -> None:
        """Load the full schema for a tool."""
        # Check if we have a custom loader
        if tool.name in self._schema_loaders:
            tool.schema = self._schema_loaders[tool.name](tool.name)
            tool.schema_loaded = True
            return
        
        # Generate default schema based on tool type
        tool.schema = self._generate_default_schema(tool)
        tool.schema_loaded = True
    
    def _generate_default_schema(self, tool: ToolDefinition) -> Dict[str, Any]:
        """Generate a default schema for a tool."""
        # These are example schemas - in production would be more complete
        schemas = {
            "Read": {
                "name": "Read",
                "description": "Read file contents",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read",
                        },
                    },
                    "required": ["file_path"],
                },
            },
            "search_and_replace": {
                "name": "search_and_replace",
                "description": "Edit file using unique anchor block",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to edit",
                        },
                        "find_block": {
                            "type": "string",
                            "description": "Unique anchor block to find (3-5 lines context)",
                        },
                        "replace_block": {
                            "type": "string",
                            "description": "Content to replace anchor with",
                        },
                    },
                    "required": ["file_path", "find_block", "replace_block"],
                },
            },
            "list_symbols": {
                "name": "list_symbols",
                "description": "List all symbols in a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file",
                        },
                        "kinds": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by symbol kind (class, function, etc.)",
                        },
                    },
                    "required": ["file_path"],
                },
            },
            "find_definition": {
                "name": "find_definition",
                "description": "Find where a symbol is defined",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Name of the symbol to find",
                        },
                        "scope": {
                            "type": "string",
                            "description": "Optional scope to narrow search",
                        },
                    },
                    "required": ["symbol"],
                },
            },
            "find_references": {
                "name": "find_references",
                "description": "Find all references to a symbol",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Name of the symbol",
                        },
                        "include_definition": {
                            "type": "boolean",
                            "description": "Include the definition location",
                            "default": True,
                        },
                    },
                    "required": ["symbol"],
                },
            },
        }
        
        if tool.name in schemas:
            return schemas[tool.name]
        
        # Generic schema
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": {"type": "object", "properties": {}},
        }
    
    @trace_run(name="Registry: Search Tools", run_type=RunType.TOOL)
    def search_tools(
        self,
        query: str,
        *,
        categories: Optional[List[str]] = None,
        limit: int = 10,
    ) -> ToolSearchResult:
        """
        Semantic search for relevant tools.
        
        Allows agents to find tools by describing what they need.
        
        Args:
            query: Natural language description of needed capability.
            categories: Optional category filter.
            limit: Maximum results to return.
            
        Returns:
            ToolSearchResult with matching tools.
        """
        # Simple keyword-based search (could be enhanced with embeddings)
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        matches = []
        
        for tool in self._tools.values():
            # Category filter
            if categories:
                if tool.category.value not in categories:
                    continue
            
            # Score based on keyword matches
            score = 0
            
            # Name match (highest weight)
            if query_lower in tool.name.lower():
                score += 10
            
            # Description match
            desc_lower = tool.description.lower()
            for word in query_words:
                if word in desc_lower:
                    score += 2
            
            # Path match
            if query_lower in tool.path.lower():
                score += 3
            
            if score > 0:
                matches.append((tool, score))
        
        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return ToolSearchResult(
            tools=[m[0] for m in matches[:limit]],
            query=query,
            total_matches=len(matches),
            categories_searched=[ToolCategory(c) for c in (categories or self.list_categories())],
        )
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_loaded_schemas(self) -> List[str]:
        """Get list of tools whose schemas have been loaded."""
        return list(self._loaded_schemas)
    
    def get_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics for all tools."""
        return {
            name: {
                "usage_count": tool.usage_count,
                "last_used": tool.last_used.isoformat() if tool.last_used else None,
                "schema_loaded": tool.schema_loaded,
            }
            for name, tool in self._tools.items()
        }
    
    def set_schema_loader(
        self,
        tool_name: str,
        loader: Callable[[str], Dict[str, Any]],
    ) -> None:
        """
        Set a custom schema loader for a tool.
        
        Args:
            tool_name: Name of the tool.
            loader: Function that returns the schema.
        """
        self._schema_loaders[tool_name] = loader
    
    def get_filesystem_view(self) -> Dict[str, Any]:
        """
        Get a filesystem-style view of tools.
        
        Returns tools organized as a virtual directory structure.
        """
        tree: Dict[str, Any] = {}
        
        for tool in self._tools.values():
            parts = tool.path.split("/")
            current = tree
            
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Add tool at leaf
            current[parts[-1]] = {
                "name": tool.name,
                "description": tool.description,
                "read_only": tool.read_only,
            }
        
        return tree
    
    def get_meta_tools(self) -> List[Callable]:
        """
        Get the meta-tools for Progressive Disclosure.
        
        These are the ONLY tools an agent sees initially. The agent uses
        these to discover other tools on-demand, preventing context saturation.
        
        Returns:
            List of callable meta-tools for tool discovery
        """
        return [
            self.list_categories,
            self.list_tools,
            self.get_tool_schema,
            self.search_tools,
        ]


__all__ = [
    "ToolRegistry",
    "ToolDefinition",
    "ToolCategory",
    "ToolSearchResult",
]

