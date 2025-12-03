"""Helpers for interacting with memory tool artifacts stored on disk."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def read_memory(path: str) -> Optional[str]:
    """
    Return the contents of a memory file if it exists; otherwise None.
    """
    memory_path = Path(path)
    if not memory_path.exists():
        return None
    return memory_path.read_text(encoding="utf-8")


def write_memory(path: str, content: str) -> None:
    """
    Persist content to the supplied path, creating parent directories as needed.
    """
    memory_path = Path(path)
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(content, encoding="utf-8")


def ensure_memory_initialized(path: str, template: str) -> str:
    """
    Guarantee that a memory file exists. If missing, seed it with the template.
    """
    existing = read_memory(path)
    if existing is not None:
        return existing
    write_memory(path, template)
    return template


__all__ = [
    "read_memory",
    "write_memory",
    "ensure_memory_initialized",
]

