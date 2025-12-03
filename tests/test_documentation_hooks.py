"""Unit tests for documentation_hooks module."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.hooks.documentation_hooks import (
    post_tool_use_logger,
    pre_tool_use_logger,
    session_end_logger,
    session_start_logger,
    stop_logger,
)


@pytest.fixture
def mock_logger():
    """Create a mock ExecutionLogger."""
    logger = MagicMock()
    logger.log_execution = MagicMock()
    return logger


@pytest.fixture
def mock_input_data():
    """Create sample input data for hooks."""
    return {
        "session_id": "test-session-123",
        "tool_name": "Read",
        "tool_input": {"path": "/test/file.txt"},
    }


class TestPreToolUseLogger:
    """Tests for pre_tool_use_logger hook."""

    @pytest.mark.asyncio
    async def test_logs_tool_use(self, mock_input_data):
        """Test logs tool use before execution."""
        with patch("src.hooks.documentation_hooks._get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.log_execution = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = await pre_tool_use_logger(
                mock_input_data, tool_use_id="tool-123", context=None
            )

            # Hook returns empty dict, not input_data
            assert result == {}
            mock_logger.log_execution.assert_called_once()
            call_args = mock_logger.log_execution.call_args
            assert call_args[1]["session_id"] == "test-session-123"
            assert call_args[1]["tool_name"] == "Read"
            assert call_args[1]["hook_event"] == "PreToolUse"

    @pytest.mark.asyncio
    async def test_records_timing(self, mock_input_data):
        """Test records execution timing."""
        with patch("src.hooks.documentation_hooks._get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            start_time = time.time()
            await pre_tool_use_logger(
                mock_input_data, tool_use_id="tool-123", context=None
            )
            end_time = time.time()

            # Check that timing was recorded (stored in _execution_timings)
            from src.hooks.documentation_hooks import _execution_timings

            assert "tool-123" in _execution_timings
            assert _execution_timings["tool-123"] >= start_time
            assert _execution_timings["tool-123"] <= end_time


class TestPostToolUseLogger:
    """Tests for post_tool_use_logger hook."""

    @pytest.mark.asyncio
    async def test_logs_successful_tool_use(self, mock_input_data):
        """Test logs successful tool execution."""
        with patch("src.hooks.documentation_hooks._get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.log_execution = MagicMock(return_value=1)
            mock_logger.update_tool_usage = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Set up timing
            from src.hooks.documentation_hooks import _execution_timings

            _execution_timings["tool-123"] = time.time() - 0.1  # 100ms ago

            # Add tool_response to input_data
            mock_input_data["tool_response"] = {"success": True, "output": "content"}

            result = await post_tool_use_logger(
                mock_input_data,
                tool_use_id="tool-123",
                context=None,
            )

            # Hook returns empty dict
            assert result == {}
            mock_logger.log_execution.assert_called_once()
            call_args = mock_logger.log_execution.call_args
            assert call_args[1]["status"] == "success"
            assert call_args[1]["duration_ms"] is not None
            assert call_args[1]["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_logs_failed_tool_use(self, mock_input_data):
        """Test logs failed tool execution."""
        with patch("src.hooks.documentation_hooks._get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.log_execution = MagicMock(return_value=1)
            mock_logger.update_tool_usage = MagicMock()
            mock_get_logger.return_value = mock_logger

            from src.hooks.documentation_hooks import _execution_timings

            _execution_timings["tool-123"] = time.time() - 0.05  # 50ms ago

            # Add tool_response with error to input_data
            mock_input_data["tool_response"] = {"success": False, "error": "File not found"}

            result = await post_tool_use_logger(
                mock_input_data,
                tool_use_id="tool-123",
                context=None,
            )

            # Hook returns empty dict
            assert result == {}
            call_args = mock_logger.log_execution.call_args
            assert call_args[1]["status"] == "error"


class TestSessionStartLogger:
    """Tests for session_start_logger hook."""

    @pytest.mark.asyncio
    async def test_logs_session_start(self):
        """Test logs session start."""
        input_data = {"session_id": "new-session-456"}

        with patch("src.hooks.documentation_hooks._get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.log_execution = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = await session_start_logger(input_data, tool_use_id=None, context=None)

            # Hook returns empty dict
            assert result == {}
            mock_logger.log_execution.assert_called_once()
            call_args = mock_logger.log_execution.call_args
            assert call_args[1]["session_id"] == "new-session-456"
            assert call_args[1]["hook_event"] == "SessionStart"


class TestSessionEndLogger:
    """Tests for session_end_logger hook."""

    @pytest.mark.asyncio
    async def test_logs_session_end(self):
        """Test logs session end."""
        input_data = {"session_id": "ending-session-789"}

        with patch("src.hooks.documentation_hooks._get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.log_execution = MagicMock()
            mock_logger.get_session_summary = MagicMock(return_value="Summary")
            mock_get_logger.return_value = mock_logger

            result = await session_end_logger(input_data, tool_use_id=None, context=None)

            # Hook returns empty dict
            assert result == {}
            mock_logger.log_execution.assert_called_once()
            call_args = mock_logger.log_execution.call_args
            assert call_args[1]["session_id"] == "ending-session-789"
            assert call_args[1]["hook_event"] == "SessionEnd"


class TestStopLogger:
    """Tests for stop_logger hook."""

    @pytest.mark.asyncio
    async def test_logs_stop_event(self):
        """Test logs stop event."""
        input_data = {"session_id": "stopped-session-999"}

        with patch("src.hooks.documentation_hooks._get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.log_execution = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = await stop_logger(input_data, tool_use_id=None, context=None)

            # Hook returns empty dict
            assert result == {}
            mock_logger.log_execution.assert_called_once()
            call_args = mock_logger.log_execution.call_args
            assert call_args[1]["session_id"] == "stopped-session-999"
            assert call_args[1]["hook_event"] == "Stop"

