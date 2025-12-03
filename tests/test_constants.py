"""Unit tests for constants module."""

from src.utils.constants import (
    BUILD_TOOLS,
    MEMORY_ARCHITECTURE_PLAN_PATH,
    MEMORY_PRD_PATH,
    MEMORY_QA_SUMMARY_PATH,
    STRATEGY_TOOLS,
    TOOL_BASH,
    TOOL_CODE_EXECUTION,
    TOOL_MEMORY,
    TOOL_READ,
    TOOL_SKILL,
    TOOL_WRITE,
)


class TestMemoryPaths:
    """Tests for memory path constants."""

    def test_memory_prd_path(self):
        """Test PRD memory path constant."""
        assert MEMORY_PRD_PATH == "/memories/prd.xml"

    def test_memory_architecture_plan_path(self):
        """Test architecture plan memory path constant."""
        assert MEMORY_ARCHITECTURE_PLAN_PATH == "/memories/architecture_plan.xml"

    def test_memory_qa_summary_path(self):
        """Test QA summary memory path constant."""
        assert MEMORY_QA_SUMMARY_PATH == "/memories/qa_summary.xml"


class TestToolNames:
    """Tests for tool name constants."""

    def test_tool_skill(self):
        """Test Skill tool constant."""
        assert TOOL_SKILL == "Skill"

    def test_tool_read(self):
        """Test Read tool constant."""
        assert TOOL_READ == "Read"

    def test_tool_write(self):
        """Test Write tool constant."""
        assert TOOL_WRITE == "Write"

    def test_tool_bash(self):
        """Test Bash tool constant."""
        assert TOOL_BASH == "Bash"

    def test_tool_memory(self):
        """Test memory tool constant."""
        assert TOOL_MEMORY == "memory"

    def test_tool_code_execution(self):
        """Test code_execution tool constant."""
        assert TOOL_CODE_EXECUTION == "code_execution"


class TestToolLists:
    """Tests for tool list constants."""

    def test_strategy_tools(self):
        """Test strategy tools list."""
        assert TOOL_SKILL in STRATEGY_TOOLS
        assert TOOL_READ in STRATEGY_TOOLS
        assert TOOL_WRITE in STRATEGY_TOOLS
        assert TOOL_BASH in STRATEGY_TOOLS
        assert TOOL_MEMORY in STRATEGY_TOOLS
        assert TOOL_CODE_EXECUTION not in STRATEGY_TOOLS

    def test_build_tools(self):
        """Test build tools list."""
        assert TOOL_SKILL in BUILD_TOOLS
        assert TOOL_READ in BUILD_TOOLS
        assert TOOL_WRITE in BUILD_TOOLS
        assert TOOL_BASH in BUILD_TOOLS
        assert TOOL_MEMORY in BUILD_TOOLS
        assert TOOL_CODE_EXECUTION in BUILD_TOOLS

    def test_build_tools_includes_code_execution(self):
        """Test build tools includes code execution."""
        assert len(BUILD_TOOLS) == len(STRATEGY_TOOLS) + 1
        assert TOOL_CODE_EXECUTION in BUILD_TOOLS

