"""Unit tests for validation_utils module."""

import pytest

from src.utils.validation_utils import (
    ValidationError,
    require_keys,
    require_non_empty,
)


class TestRequireKeys:
    """Tests for require_keys function."""

    def test_all_keys_present(self):
        """Test passes when all required keys are present."""
        payload = {"key1": "value1", "key2": "value2", "key3": "value3"}
        required = ["key1", "key2"]

        # Should not raise
        require_keys(payload, required)

    def test_missing_single_key(self):
        """Test raises when a single key is missing."""
        payload = {"key1": "value1"}
        required = ["key1", "key2"]

        with pytest.raises(ValidationError) as exc_info:
            require_keys(payload, required)

        assert "key2" in str(exc_info.value)

    def test_missing_multiple_keys(self):
        """Test raises with all missing keys listed."""
        payload = {"key1": "value1"}
        required = ["key1", "key2", "key3"]

        with pytest.raises(ValidationError) as exc_info:
            require_keys(payload, required)

        error_msg = str(exc_info.value)
        assert "key2" in error_msg
        assert "key3" in error_msg

    def test_empty_required_list(self):
        """Test passes when no keys are required."""
        payload = {"key1": "value1"}
        required = []

        # Should not raise
        require_keys(payload, required)

    def test_empty_payload_with_required_keys(self):
        """Test raises when payload is empty but keys are required."""
        payload = {}
        required = ["key1", "key2"]

        with pytest.raises(ValidationError):
            require_keys(payload, required)

    def test_extra_keys_ignored(self):
        """Test extra keys in payload don't cause issues."""
        payload = {"key1": "value1", "key2": "value2", "extra": "value"}
        required = ["key1", "key2"]

        # Should not raise
        require_keys(payload, required)


class TestRequireNonEmpty:
    """Tests for require_non_empty function."""

    def test_non_empty_string_passes(self):
        """Test passes for non-empty string."""
        # Should not raise
        require_non_empty("valid string", "field_name")

    def test_empty_string_raises(self):
        """Test raises for empty string."""
        with pytest.raises(ValidationError) as exc_info:
            require_non_empty("", "field_name")

        assert "field_name" in str(exc_info.value)
        assert "must not be empty" in str(exc_info.value)

    def test_whitespace_only_passes(self):
        """Test whitespace-only string passes (function only checks for empty, not whitespace)."""
        # require_non_empty only checks if string is falsy (empty), not if it's whitespace-only
        # Whitespace strings are truthy, so they pass
        require_non_empty("   ", "field_name")  # Should not raise

    def test_field_name_in_error_message(self):
        """Test error message includes field name."""
        with pytest.raises(ValidationError) as exc_info:
            require_non_empty("", "email")

        assert "email" in str(exc_info.value)

