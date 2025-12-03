"""Common validation helpers."""

from __future__ import annotations

from typing import Iterable, Mapping


class ValidationError(ValueError):
    """Raised when incoming data fails validation."""


def require_keys(payload: Mapping[str, object], required_keys: Iterable[str]) -> None:
    """
    Ensure payload contains each required key.
    """
    missing = [key for key in required_keys if key not in payload]
    if missing:
        raise ValidationError(f"Missing required keys: {', '.join(missing)}")


def require_non_empty(value: str, field_name: str) -> None:
    """Ensure a string field has a non-empty value."""
    if not value:
        raise ValidationError(f"Field '{field_name}' must not be empty.")


__all__ = ["ValidationError", "require_keys", "require_non_empty"]

