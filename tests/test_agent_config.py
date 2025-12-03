"""Unit tests for agent_config module."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from config.agent_config import (
    MODEL_REGISTRY,
    get_env,
    get_api_keys,
    get_google_cloud_credentials_path,
    get_user_email,
    resolve_model_config,
)


class TestGetEnv:
    """Tests for get_env function."""

    def test_get_existing_env_var(self):
        """Test retrieving an existing environment variable."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = get_env("TEST_VAR")
            assert result == "test_value"

    def test_get_missing_env_var_with_default(self):
        """Test retrieving missing env var returns default."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env("MISSING_VAR", default="default_value")
            assert result == "default_value"

    def test_get_missing_env_var_no_default(self):
        """Test retrieving missing env var without default returns None."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env("MISSING_VAR")
            assert result is None

    def test_get_missing_required_env_var_raises(self):
        """Test retrieving missing required env var raises RuntimeError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                get_env("REQUIRED_VAR", required=True)

            assert "REQUIRED_VAR" in str(exc_info.value)
            assert "Missing required environment variable" in str(exc_info.value)


class TestGetApiKeys:
    """Tests for get_api_keys function."""

    def test_get_all_api_keys(self):
        """Test retrieving all API keys."""
        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "anthropic_key",
                "LINEAR_API_KEY": "linear_key",
                "MINTLIFY_API_KEY": "mintlify_key",
            },
        ):
            keys = get_api_keys()
            assert keys["anthropic"] == "anthropic_key"
            assert keys["linear"] == "linear_key"
            assert keys["mintlify"] == "mintlify_key"

    def test_missing_api_keys_return_none(self):
        """Test missing API keys return None."""
        with patch.dict(os.environ, {}, clear=True):
            keys = get_api_keys()
            assert keys["anthropic"] is None
            assert keys["linear"] is None
            assert keys["mintlify"] is None


class TestResolveModelConfig:
    """Tests for resolve_model_config function."""

    def test_resolve_strategy_profile(self):
        """Test resolving strategy model profile."""
        config = resolve_model_config("strategy")
        assert config.name == "claude-opus-4@20250514"
        assert "Skill" in config.allowed_tools
        assert "Read" in config.allowed_tools
        assert "code_execution" not in config.allowed_tools

    def test_resolve_build_profile(self):
        """Test resolving build model profile."""
        config = resolve_model_config("build")
        assert config.name == "claude-opus-4@20250514"
        assert "Skill" in config.allowed_tools
        assert "code_execution" in config.allowed_tools

    def test_resolve_with_code_execution(self):
        """Test resolving with code_execution flag adds beta flags."""
        config = resolve_model_config("strategy", include_code_execution=True)
        # include_code_execution adds beta flags, not the tool itself
        # The tool is only in "build" profile's allowed_tools
        assert "code-execution-2025-08-25" in config.beta_flags
        # Strategy profile doesn't include code_execution in allowed_tools
        assert "code_execution" not in config.allowed_tools

    def test_resolve_invalid_profile_raises(self):
        """Test resolving invalid profile raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            resolve_model_config("invalid_profile")

        assert "invalid_profile" in str(exc_info.value)
        assert "Available profiles" in str(exc_info.value)


class TestGetGoogleCloudCredentialsPath:
    """Tests for get_google_cloud_credentials_path function."""

    def test_get_from_env_var(self, tmp_path):
        """Test getting path from GOOGLE_APPLICATION_CREDENTIALS env var."""
        creds_file = tmp_path / "creds.json"
        creds_file.write_text('{"type": "service_account"}')

        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": str(creds_file)}):
            result = get_google_cloud_credentials_path()
            assert result == creds_file

    def test_get_from_default_location(self, tmp_path, monkeypatch):
        """Test getting path from default location."""
        # Mock PROJECT_ROOT
        default_creds = tmp_path / "config" / "credentials" / "google-service-account.json"
        default_creds.parent.mkdir(parents=True)
        default_creds.write_text('{"type": "service_account"}')

        with patch("config.agent_config.PROJECT_ROOT", tmp_path):
            with patch.dict(os.environ, {}, clear=True):
                result = get_google_cloud_credentials_path()
                assert result == default_creds

    def test_returns_none_when_not_found(self):
        """Test returns None when credentials not found."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("config.agent_config.PROJECT_ROOT", Path("/nonexistent")):
                result = get_google_cloud_credentials_path()
                assert result is None


class TestGetUserEmail:
    """Tests for get_user_email function."""

    def test_get_from_env_var(self):
        """Test getting email from CLAUDE_AGENT_USER_EMAIL env var."""
        with patch.dict(os.environ, {"CLAUDE_AGENT_USER_EMAIL": "user@example.com"}):
            result = get_user_email()
            assert result == "user@example.com"

    def test_get_from_config_file(self, tmp_path, monkeypatch):
        """Test getting email from .claude/user_config.json file."""
        config_file = tmp_path / ".claude" / "user_config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text('{"user": "config@example.com"}')

        with patch("config.agent_config.PROJECT_ROOT", tmp_path):
            with patch.dict(os.environ, {}, clear=True):
                result = get_user_email()
                assert result == "config@example.com"

    def test_env_var_takes_precedence(self, tmp_path, monkeypatch):
        """Test env var takes precedence over config file."""
        config_file = tmp_path / ".claude" / "user_config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text('{"user": "config@example.com"}')

        with patch("config.agent_config.PROJECT_ROOT", tmp_path):
            with patch.dict(os.environ, {"CLAUDE_AGENT_USER_EMAIL": "env@example.com"}):
                result = get_user_email()
                assert result == "env@example.com"

    def test_returns_none_when_not_found(self):
        """Test returns None when email not found."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("config.agent_config.PROJECT_ROOT", Path("/nonexistent")):
                result = get_user_email()
                assert result is None

