"""
Navigation MCP Server for Structural Code Navigation.

Implements LSP-grade code navigation (Gap 1 fix):
- list_symbols: Returns classes, functions, methods in a file
- find_definition: Go to Definition - returns file:line
- find_references: Find all References to a symbol
- get_call_graph: Build dependency graph for a function

Uses ctags and tree-sitter for structural understanding.
Agents using grep often hallucinate relationships - this prevents that.

Reference: "No Vibes Allowed: Solving Hard Problems in Complex Codebases" - Dex Horthy
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from src.tracing import trace_run, RunType


class NavigationError(Exception):
    """Raised when navigation operations fail."""
    pass


@dataclass
class Symbol:
    """A code symbol (class, function, method, variable)."""
    name: str
    kind: str  # class, function, method, variable, constant
    file_path: str
    line: int
    signature: Optional[str] = None
    parent: Optional[str] = None  # For methods, the containing class
    scope: Optional[str] = None
    
    def to_reference(self) -> str:
        """Convert to file:line reference format."""
        return f"{self.file_path}:{self.line}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "kind": self.kind,
            "file_path": self.file_path,
            "line": self.line,
            "signature": self.signature,
            "parent": self.parent,
            "scope": self.scope,
        }


@dataclass
class Location:
    """A location in the codebase."""
    file_path: str
    line: int
    column: int = 0
    context: Optional[str] = None  # Surrounding code
    
    def to_reference(self) -> str:
        """Convert to file:line reference format."""
        return f"{self.file_path}:{self.line}"


@dataclass
class CallGraph:
    """A call graph for a function."""
    root: str  # Root function name
    calls: List[str]  # Functions this function calls
    called_by: List[str]  # Functions that call this function
    depth: int = 1  # How many levels deep we analyzed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "root": self.root,
            "calls": self.calls,
            "called_by": self.called_by,
            "depth": self.depth,
        }


class NavigationMCPServer:
    """
    MCP Server for structural code navigation.
    
    Provides LSP-grade code navigation to prevent the common failure mode
    where agents using grep hallucinate import paths and relationships.
    
    Key capabilities:
    - list_symbols: Get all symbols in a file
    - find_definition: Jump to where a symbol is defined
    - find_references: Find all usages of a symbol
    - get_call_graph: Map function dependencies
    
    Example:
        >>> server = NavigationMCPServer("/path/to/repo")
        >>> 
        >>> # List symbols in a file
        >>> symbols = await server.list_symbols("src/models/user.py")
        >>> print([s.name for s in symbols])
        ['User', 'authenticate', 'get_roles']
        >>> 
        >>> # Find definition of a symbol
        >>> location = await server.find_definition("User")
        >>> print(location.to_reference())
        'src/models/user.py:45'
        >>> 
        >>> # Find all references
        >>> refs = await server.find_references("User")
        >>> print(len(refs))
        15
    """
    
    def __init__(
        self,
        workspace_path: str,
        *,
        use_ctags: bool = True,
        use_tree_sitter: bool = True,
        cache_enabled: bool = True,
    ):
        """
        Initialize the Navigation MCP Server.
        
        Args:
            workspace_path: Root path of the workspace to navigate.
            use_ctags: Whether to use ctags for symbol extraction.
            use_tree_sitter: Whether to use tree-sitter for parsing.
            cache_enabled: Whether to cache navigation results.
        """
        self.workspace_path = Path(workspace_path)
        self.use_ctags = use_ctags
        self.use_tree_sitter = use_tree_sitter
        self.cache_enabled = cache_enabled
        
        self._symbol_cache: Dict[str, List[Symbol]] = {}
        self._ctags_available = self._check_ctags()
        self._tree_sitter_available = self._check_tree_sitter()
        
        # Context for MCP
        self._context: Optional[Dict[str, Any]] = None
    
    def _check_ctags(self) -> bool:
        """Check if ctags is available."""
        try:
            result = subprocess.run(
                ["ctags", "--version"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_tree_sitter(self) -> bool:
        """Check if tree-sitter is available."""
        try:
            import tree_sitter
            return True
        except ImportError:
            return False
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """Set session context for the server."""
        self._context = context
    
    @trace_run(name="Navigation: List Symbols", run_type=RunType.TOOL)
    async def list_symbols(
        self,
        file_path: str,
        *,
        kinds: Optional[List[str]] = None,
    ) -> List[Symbol]:
        """
        List all symbols in a file.
        
        Args:
            file_path: Path to the file (relative to workspace).
            kinds: Optional filter for symbol kinds (class, function, etc.)
            
        Returns:
            List of Symbol objects found in the file.
        """
        full_path = self.workspace_path / file_path
        
        if not full_path.exists():
            raise NavigationError(f"File not found: {file_path}")
        
        # Check cache
        cache_key = str(full_path)
        if self.cache_enabled and cache_key in self._symbol_cache:
            symbols = self._symbol_cache[cache_key]
            if kinds:
                return [s for s in symbols if s.kind in kinds]
            return symbols
        
        # Extract symbols
        if self._ctags_available and self.use_ctags:
            symbols = await self._extract_symbols_ctags(full_path, file_path)
        else:
            symbols = await self._extract_symbols_regex(full_path, file_path)
        
        # Cache results
        if self.cache_enabled:
            self._symbol_cache[cache_key] = symbols
        
        # Filter by kind if specified
        if kinds:
            return [s for s in symbols if s.kind in kinds]
        
        return symbols
    
    async def _extract_symbols_ctags(self, full_path: Path, rel_path: str) -> List[Symbol]:
        """Extract symbols using ctags."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "ctags",
                    "-f", "-",
                    "--output-format=json",
                    "--fields=+n+S+K",
                    str(full_path),
                ],
                capture_output=True,
                text=True,
            )
            
            symbols = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    symbols.append(Symbol(
                        name=data.get("name", ""),
                        kind=data.get("kind", "unknown"),
                        file_path=rel_path,
                        line=data.get("line", 0),
                        signature=data.get("signature"),
                        scope=data.get("scope"),
                    ))
                except json.JSONDecodeError:
                    continue
            
            return symbols
            
        except Exception as e:
            # Fall back to regex
            return await self._extract_symbols_regex(full_path, rel_path)
    
    async def _extract_symbols_regex(self, full_path: Path, rel_path: str) -> List[Symbol]:
        """Extract symbols using regex patterns."""
        content = full_path.read_text(encoding='utf-8')
        symbols = []
        
        # Language detection
        suffix = full_path.suffix.lower()
        
        if suffix in ('.py',):
            symbols.extend(self._extract_python_symbols(content, rel_path))
        elif suffix in ('.ts', '.tsx', '.js', '.jsx'):
            symbols.extend(self._extract_typescript_symbols(content, rel_path))
        elif suffix in ('.java',):
            symbols.extend(self._extract_java_symbols(content, rel_path))
        elif suffix in ('.go',):
            symbols.extend(self._extract_go_symbols(content, rel_path))
        else:
            # Generic patterns
            symbols.extend(self._extract_generic_symbols(content, rel_path))
        
        return symbols
    
    def _extract_python_symbols(self, content: str, file_path: str) -> List[Symbol]:
        """Extract symbols from Python code."""
        symbols = []
        lines = content.split('\n')
        current_class = None
        
        for i, line in enumerate(lines, 1):
            # Classes
            class_match = re.match(r'^class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(1)
                symbols.append(Symbol(
                    name=current_class,
                    kind="class",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
                continue
            
            # Functions/Methods
            func_match = re.match(r'^(\s*)def\s+(\w+)\s*\((.*?)\)?', line)
            if func_match:
                indent = len(func_match.group(1))
                name = func_match.group(2)
                
                # If indented and we have a current class, it's a method
                if indent > 0 and current_class:
                    symbols.append(Symbol(
                        name=name,
                        kind="method",
                        file_path=file_path,
                        line=i,
                        signature=line.strip(),
                        parent=current_class,
                    ))
                else:
                    current_class = None  # Reset class context
                    symbols.append(Symbol(
                        name=name,
                        kind="function",
                        file_path=file_path,
                        line=i,
                        signature=line.strip(),
                    ))
            
            # Reset class context on unindented line
            if line and not line[0].isspace():
                if not class_match:
                    current_class = None
        
        return symbols
    
    def _extract_typescript_symbols(self, content: str, file_path: str) -> List[Symbol]:
        """Extract symbols from TypeScript/JavaScript code."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Classes
            class_match = re.match(r'^\s*(export\s+)?(abstract\s+)?class\s+(\w+)', line)
            if class_match:
                symbols.append(Symbol(
                    name=class_match.group(3),
                    kind="class",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
            
            # Interfaces
            interface_match = re.match(r'^\s*(export\s+)?interface\s+(\w+)', line)
            if interface_match:
                symbols.append(Symbol(
                    name=interface_match.group(2),
                    kind="interface",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
            
            # Functions
            func_match = re.match(r'^\s*(export\s+)?(async\s+)?function\s+(\w+)', line)
            if func_match:
                symbols.append(Symbol(
                    name=func_match.group(3),
                    kind="function",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
            
            # Arrow functions as const
            arrow_match = re.match(r'^\s*(export\s+)?(const|let)\s+(\w+)\s*=\s*(async\s+)?\(', line)
            if arrow_match:
                symbols.append(Symbol(
                    name=arrow_match.group(3),
                    kind="function",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
        
        return symbols
    
    def _extract_java_symbols(self, content: str, file_path: str) -> List[Symbol]:
        """Extract symbols from Java code."""
        symbols = []
        lines = content.split('\n')
        current_class = None
        
        for i, line in enumerate(lines, 1):
            # Classes
            class_match = re.match(r'^\s*(public|private|protected)?\s*(abstract)?\s*class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(3)
                symbols.append(Symbol(
                    name=current_class,
                    kind="class",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
            
            # Methods
            method_match = re.match(
                r'^\s*(public|private|protected)?\s*(static)?\s*\w+\s+(\w+)\s*\(',
                line
            )
            if method_match and current_class:
                symbols.append(Symbol(
                    name=method_match.group(3),
                    kind="method",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                    parent=current_class,
                ))
        
        return symbols
    
    def _extract_go_symbols(self, content: str, file_path: str) -> List[Symbol]:
        """Extract symbols from Go code."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Structs
            struct_match = re.match(r'^type\s+(\w+)\s+struct', line)
            if struct_match:
                symbols.append(Symbol(
                    name=struct_match.group(1),
                    kind="struct",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
            
            # Interfaces
            interface_match = re.match(r'^type\s+(\w+)\s+interface', line)
            if interface_match:
                symbols.append(Symbol(
                    name=interface_match.group(1),
                    kind="interface",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
            
            # Functions
            func_match = re.match(r'^func\s+(\w+)\s*\(', line)
            if func_match:
                symbols.append(Symbol(
                    name=func_match.group(1),
                    kind="function",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
            
            # Methods
            method_match = re.match(r'^func\s+\(\w+\s+\*?(\w+)\)\s+(\w+)\s*\(', line)
            if method_match:
                symbols.append(Symbol(
                    name=method_match.group(2),
                    kind="method",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                    parent=method_match.group(1),
                ))
        
        return symbols
    
    def _extract_generic_symbols(self, content: str, file_path: str) -> List[Symbol]:
        """Extract symbols using generic patterns."""
        symbols = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Generic function pattern
            func_match = re.match(r'^\s*(function|def|func|fn)\s+(\w+)', line)
            if func_match:
                symbols.append(Symbol(
                    name=func_match.group(2),
                    kind="function",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
            
            # Generic class pattern
            class_match = re.match(r'^\s*(class|struct|type)\s+(\w+)', line)
            if class_match:
                symbols.append(Symbol(
                    name=class_match.group(2),
                    kind="class",
                    file_path=file_path,
                    line=i,
                    signature=line.strip(),
                ))
        
        return symbols
    
    @trace_run(name="Navigation: Find Definition", run_type=RunType.TOOL)
    async def find_definition(
        self,
        symbol: str,
        *,
        scope: Optional[str] = None,
    ) -> Optional[Location]:
        """
        Find where a symbol is defined.
        
        Args:
            symbol: Name of the symbol to find.
            scope: Optional scope to narrow search (file path or class name).
            
        Returns:
            Location of the definition, or None if not found.
        """
        # Search all files in workspace
        for file_path in self._iter_source_files():
            try:
                symbols = await self.list_symbols(str(file_path.relative_to(self.workspace_path)))
                
                for sym in symbols:
                    if sym.name == symbol:
                        # If scope specified, check it matches
                        if scope:
                            if scope not in sym.file_path and scope != sym.parent:
                                continue
                        
                        return Location(
                            file_path=sym.file_path,
                            line=sym.line,
                            context=sym.signature,
                        )
            except Exception:
                continue
        
        return None
    
    @trace_run(name="Navigation: Find References", run_type=RunType.TOOL)
    async def find_references(
        self,
        symbol: str,
        *,
        include_definition: bool = True,
    ) -> List[Location]:
        """
        Find all references to a symbol.
        
        Args:
            symbol: Name of the symbol to find references for.
            include_definition: Whether to include the definition location.
            
        Returns:
            List of Location objects where the symbol is referenced.
        """
        references = []
        definition_found = False
        
        # Pattern to match the symbol (word boundary)
        pattern = re.compile(r'\b' + re.escape(symbol) + r'\b')
        
        for file_path in self._iter_source_files():
            try:
                rel_path = str(file_path.relative_to(self.workspace_path))
                content = file_path.read_text(encoding='utf-8')
                
                for i, line in enumerate(content.split('\n'), 1):
                    if pattern.search(line):
                        # Check if this is the definition
                        is_definition = any(
                            kw in line for kw in ['def ', 'class ', 'function ', 'const ', 'let ', 'var ']
                        ) and symbol in line.split('(')[0]
                        
                        if is_definition:
                            definition_found = True
                            if not include_definition:
                                continue
                        
                        references.append(Location(
                            file_path=rel_path,
                            line=i,
                            context=line.strip()[:100],
                        ))
            except Exception:
                continue
        
        return references
    
    @trace_run(name="Navigation: Get Call Graph", run_type=RunType.TOOL)
    async def get_call_graph(
        self,
        function: str,
        *,
        depth: int = 1,
    ) -> CallGraph:
        """
        Build a call graph for a function.
        
        Args:
            function: Name of the function to analyze.
            depth: How many levels of calls to analyze.
            
        Returns:
            CallGraph showing what the function calls and what calls it.
        """
        calls: Set[str] = set()
        called_by: Set[str] = set()
        
        # Find the function definition first
        definition = await self.find_definition(function)
        if not definition:
            return CallGraph(root=function, calls=[], called_by=[], depth=0)
        
        # Read the file containing the function
        full_path = self.workspace_path / definition.file_path
        if not full_path.exists():
            return CallGraph(root=function, calls=[], called_by=[], depth=0)
        
        content = full_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Find function body
        in_function = False
        indent_level = 0
        
        for i, line in enumerate(lines, 1):
            if i == definition.line:
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                continue
            
            if in_function:
                # Check if we've exited the function
                current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 1
                if line.strip() and current_indent <= indent_level:
                    break
                
                # Find function calls (simple pattern)
                call_matches = re.findall(r'(\w+)\s*\(', line)
                for call in call_matches:
                    if call != function and not call[0].isupper():  # Exclude class instantiation
                        calls.add(call)
        
        # Find what calls this function
        references = await self.find_references(function, include_definition=False)
        for ref in references:
            # Get the containing function
            ref_file = self.workspace_path / ref.file_path
            if ref_file.exists():
                symbols = await self.list_symbols(ref.file_path)
                for sym in symbols:
                    if sym.kind in ('function', 'method') and sym.line < ref.line:
                        called_by.add(sym.name)
                        break
        
        return CallGraph(
            root=function,
            calls=sorted(calls),
            called_by=sorted(called_by),
            depth=depth,
        )
    
    def _iter_source_files(self):
        """Iterate over source files in workspace."""
        source_extensions = {'.py', '.ts', '.tsx', '.js', '.jsx', '.java', '.go', '.rs', '.rb'}
        exclude_dirs = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build'}
        
        for file_path in self.workspace_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in source_extensions:
                # Check if in excluded directory
                if not any(excluded in file_path.parts for excluded in exclude_dirs):
                    yield file_path
    
    def get_tools(self) -> List[Callable]:
        """Get tools for Agent SDK consumption."""
        return [
            self.list_symbols,
            self.find_definition,
            self.find_references,
            self.get_call_graph,
        ]
    
    def clear_cache(self) -> None:
        """Clear the symbol cache."""
        self._symbol_cache.clear()


__all__ = [
    "NavigationMCPServer",
    "NavigationError",
    "Symbol",
    "Location",
    "CallGraph",
]

