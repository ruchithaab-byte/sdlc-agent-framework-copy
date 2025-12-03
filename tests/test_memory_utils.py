"""Unit tests for memory_utils module."""

import tempfile
from pathlib import Path

import pytest

from src.utils.memory_utils import (
    ensure_memory_initialized,
    read_memory,
    write_memory,
)


class TestReadMemory:
    """Tests for read_memory function."""

    def test_read_existing_file(self, tmp_path):
        """Test reading an existing memory file."""
        memory_file = tmp_path / "test_memory.xml"
        content = "<test>content</test>"
        memory_file.write_text(content, encoding="utf-8")

        result = read_memory(str(memory_file))
        assert result == content

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file returns None."""
        result = read_memory("/nonexistent/path/file.xml")
        assert result is None

    def test_read_empty_file(self, tmp_path):
        """Test reading an empty file returns empty string."""
        memory_file = tmp_path / "empty.xml"
        memory_file.write_text("", encoding="utf-8")

        result = read_memory(str(memory_file))
        assert result == ""


class TestWriteMemory:
    """Tests for write_memory function."""

    def test_write_new_file(self, tmp_path):
        """Test writing to a new file."""
        memory_file = tmp_path / "new_memory.xml"
        content = "<test>new content</test>"

        write_memory(str(memory_file), content)

        assert memory_file.exists()
        assert memory_file.read_text(encoding="utf-8") == content

    def test_write_overwrites_existing(self, tmp_path):
        """Test writing overwrites existing content."""
        memory_file = tmp_path / "existing.xml"
        memory_file.write_text("<old>content</old>", encoding="utf-8")

        new_content = "<new>content</new>"
        write_memory(str(memory_file), new_content)

        assert memory_file.read_text(encoding="utf-8") == new_content

    def test_write_creates_parent_directories(self, tmp_path):
        """Test writing creates parent directories if they don't exist."""
        memory_file = tmp_path / "nested" / "deep" / "memory.xml"
        content = "<test>content</test>"

        write_memory(str(memory_file), content)

        assert memory_file.exists()
        assert memory_file.read_text(encoding="utf-8") == content


class TestEnsureMemoryInitialized:
    """Tests for ensure_memory_initialized function."""

    def test_initializes_missing_file(self, tmp_path):
        """Test initializing a missing file with template."""
        memory_file = tmp_path / "init_memory.xml"
        template = "<template>default</template>"

        result = ensure_memory_initialized(str(memory_file), template)

        assert result == template
        assert memory_file.exists()
        assert memory_file.read_text(encoding="utf-8") == template

    def test_returns_existing_content(self, tmp_path):
        """Test returns existing content without overwriting."""
        memory_file = tmp_path / "existing_memory.xml"
        existing_content = "<existing>content</existing>"
        memory_file.write_text(existing_content, encoding="utf-8")
        template = "<template>should not be used</template>"

        result = ensure_memory_initialized(str(memory_file), template)

        assert result == existing_content
        assert memory_file.read_text(encoding="utf-8") == existing_content

    def test_handles_unicode_content(self, tmp_path):
        """Test handles unicode characters correctly."""
        memory_file = tmp_path / "unicode_memory.xml"
        unicode_content = "<test>测试内容 🚀</test>"

        write_memory(str(memory_file), unicode_content)
        result = read_memory(str(memory_file))

        assert result == unicode_content

