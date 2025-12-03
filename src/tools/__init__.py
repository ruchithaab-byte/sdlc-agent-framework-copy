"""
Tools Module.

Provides tool primitives and registry for agents:
- ReliableEditor: Anchored edits (Gap 2 fix)
- ToolRegistry: Progressive tool disclosure with lazy loading

Reference: "Tools as Filesystem" - Dex Horthy
"""

from src.tools.editor import (
    ReliableEditor,
    EditResult,
    EditHistoryEntry,
    AmbiguousEditError,
    EditValidationError,
    EDIT_SYSTEM_PROMPT,
)
from src.tools.registry import (
    ToolRegistry,
    ToolDefinition,
    ToolCategory,
    ToolSearchResult,
)

__all__ = [
    # Editor
    "ReliableEditor",
    "EditResult",
    "EditHistoryEntry",
    "AmbiguousEditError",
    "EditValidationError",
    "EDIT_SYSTEM_PROMPT",
    # Registry
    "ToolRegistry",
    "ToolDefinition",
    "ToolCategory",
    "ToolSearchResult",
]

