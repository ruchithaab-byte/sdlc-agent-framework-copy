"""
Safety Tests for ReliableEditor (Gap 2 Fix Verification)

Tests the mandatory validation and auto-revert mechanisms that prevent
agents from corrupting files with syntax errors.

Reference: "No Vibes Allowed" - Gap 2: The Edit Gap
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.editor import ReliableEditor, EditValidationError, AmbiguousEditError


class TestEditorSafety:
    """Test suite for ReliableEditor safety mechanisms."""
    
    TEST_FILE = "safety_sandbox.py"
    
    def setup_method(self):
        """Create a clean file before each test."""
        with open(self.TEST_FILE, "w") as f:
            f.write("def calculate_sum(a, b):\n    return a + b\n")
    
    def teardown_method(self):
        """Cleanup after test."""
        if os.path.exists(self.TEST_FILE):
            os.remove(self.TEST_FILE)
    
    def test_valid_edit_succeeds(self):
        """
        Scenario 1: Agent writes valid Python.
        
        This should succeed and the file should be updated.
        """
        print("\n[TEST 1] Testing valid edit...")
        editor = ReliableEditor(mandatory_validation=True)
        
        # Valid edit: Changing the return statement
        result = editor.search_and_replace(
            self.TEST_FILE,
            find_block="return a + b",
            replace_block="return a * b"
        )
        
        assert result.success is True, "Edit should succeed"
        assert result.syntax_valid is True, "Syntax should be valid"
        
        with open(self.TEST_FILE, "r") as f:
            content = f.read()
            assert "return a * b" in content, "New code should be present"
            assert "return a + b" not in content, "Old code should be replaced"
        
        print("✅ PASS: Valid edit succeeded and file was updated")
    
    def test_auto_revert_on_syntax_error(self):
        """
        Scenario 2: Agent writes broken Python (The 'Slop' Case).
        
        This is the CRITICAL test for Gap 2 fix.
        The editor MUST auto-revert the file if validation fails.
        """
        print("\n[TEST 2] Testing auto-revert on syntax error...")
        editor = ReliableEditor(mandatory_validation=True)
        
        original_content = "def calculate_sum(a, b):\n    return a + b\n"
        
        # Invalid edit: Syntax error (missing colon)
        # This simulates an agent hallucinating syntax
        try:
            editor.search_and_replace(
                self.TEST_FILE,
                find_block="def calculate_sum(a, b):",
                replace_block="def calculate_sum(a, b)\n    return a + b"  # Missing colon
            )
            pytest.fail("Should have raised EditValidationError")
        except EditValidationError as e:
            print(f"✅ Caught expected error: {str(e)[:100]}...")
        
        # THE CRITICAL CHECK: Did the file revert?
        with open(self.TEST_FILE, "r") as f:
            current_content = f.read()
            assert current_content == original_content, "CRITICAL FAIL: File was not reverted!"
            print("✅ Auto-revert successful: File restored to original state")
        
        print("✅ PASS: Invalid edit was caught and auto-reverted")
    
    def test_auto_revert_on_indentation_error(self):
        """
        Scenario 2b: Agent writes Python with invalid indentation.
        
        Tests that indentation errors are also caught.
        """
        print("\n[TEST 2b] Testing auto-revert on indentation error...")
        editor = ReliableEditor(mandatory_validation=True)
        
        original_content = "def calculate_sum(a, b):\n    return a + b\n"
        
        # Invalid edit: Bad indentation
        try:
            editor.search_and_replace(
                self.TEST_FILE,
                find_block="    return a + b",
                replace_block="  return a + b\n    print('test')"  # Inconsistent indent
            )
            pytest.fail("Should have raised EditValidationError")
        except EditValidationError as e:
            print(f"✅ Caught expected error: {str(e)[:100]}...")
        
        # Verify file reverted
        with open(self.TEST_FILE, "r") as f:
            current_content = f.read()
            assert current_content == original_content, "File should be reverted"
        
        print("✅ PASS: Indentation error caught and auto-reverted")
    
    def test_ambiguous_anchor_rejected(self):
        """
        Scenario 3: Agent uses a non-unique anchor.
        
        This should be rejected BEFORE any edit is attempted.
        """
        print("\n[TEST 3] Testing ambiguous anchor rejection...")
        editor = ReliableEditor(mandatory_validation=True)
        
        # Write file with duplicate lines
        with open(self.TEST_FILE, "w") as f:
            f.write("print('hello')\nprint('hello')\n")
        
        try:
            editor.search_and_replace(
                self.TEST_FILE,
                find_block="print('hello')",  # Ambiguous! Exists twice.
                replace_block="print('world')"
            )
            pytest.fail("Should have raised AmbiguousEditError")
        except AmbiguousEditError as e:
            print(f"✅ Caught expected error: {str(e)[:100]}...")
            assert "found 2 times" in str(e).lower() or "multiple" in str(e).lower()
        
        print("✅ PASS: Ambiguous anchor was rejected")
    
    def test_anchor_not_found(self):
        """
        Scenario 4: Agent uses an anchor that doesn't exist.
        
        This should be rejected BEFORE any edit is attempted.
        """
        print("\n[TEST 4] Testing anchor not found...")
        editor = ReliableEditor(mandatory_validation=True)
        
        try:
            editor.search_and_replace(
                self.TEST_FILE,
                find_block="def nonexistent_function():",  # Doesn't exist
                replace_block="def new_function():"
            )
            pytest.fail("Should have raised AmbiguousEditError")
        except AmbiguousEditError as e:
            print(f"✅ Caught expected error: {str(e)[:100]}...")
            assert "not found" in str(e).lower()
        
        print("✅ PASS: Missing anchor was rejected")
    
    def test_json_validation(self):
        """
        Scenario 5: Test JSON file validation.
        
        Ensures JSON syntax errors are caught.
        """
        print("\n[TEST 5] Testing JSON validation...")
        
        # Create JSON test file
        json_file = "test_config.json"
        with open(json_file, "w") as f:
            f.write('{"name": "test", "value": 123}')
        
        try:
            editor = ReliableEditor(mandatory_validation=True)
            
            # Invalid JSON edit: Trailing comma
            try:
                editor.search_and_replace(
                    json_file,
                    find_block='"value": 123',
                    replace_block='"value": 123,'  # Trailing comma = invalid JSON
                )
                pytest.fail("Should have raised EditValidationError")
            except EditValidationError as e:
                print(f"✅ Caught expected error: {str(e)[:100]}...")
            
            # Verify file reverted
            with open(json_file, "r") as f:
                content = f.read()
                assert '"value": 123}' in content, "JSON should be reverted"
                assert '"value": 123,' not in content, "Invalid JSON should not persist"
            
            print("✅ PASS: JSON validation works")
        finally:
            if os.path.exists(json_file):
                os.remove(json_file)


if __name__ == "__main__":
    # Allow running directly for debugging
    pytest.main([__file__, "-v", "-s"])

