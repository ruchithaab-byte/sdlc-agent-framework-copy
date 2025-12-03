"""
Reliable Editor with Anchored Edits.

Implements the "Search and Replace Blocks" pattern (Gap 2 fix):
- NO line numbers allowed - LLMs are bad at counting
- Uses unique anchor strings (3-5 lines of context)
- Validates uniqueness before applying edits
- Handles whitespace normalization
- Phase 7: MANDATORY post-edit syntax validation with auto-revert

Reference: "12-Factor Agents" - Table 2: Tool Definition Formats
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class AmbiguousEditError(Exception):
    """Raised when edit anchor is ambiguous (0 or >1 matches)."""
    pass


class EditValidationError(Exception):
    """Raised when edit validation fails."""
    pass


@dataclass
class EditResult:
    """Result of an edit operation."""
    success: bool
    file_path: str
    old_content_preview: str = ""
    new_content_preview: str = ""
    lines_changed: int = 0
    timestamp: datetime = None
    
    # Phase 7: Validation results
    syntax_valid: bool = True
    lint_issues: List[Any] = None
    validation_message: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class EditHistoryEntry:
    """Entry in the edit history for potential rollback."""
    file_path: str
    original_content: str
    new_content: str
    find_block: str
    replace_block: str
    timestamp: datetime


class ReliableEditor:
    """
    Reliable file editor using anchored search-and-replace.
    
    This is the ONLY allowed edit primitive for agents. It enforces:
    
    1. **No line numbers**: LLMs struggle with line counting, leading to corruption
    2. **Unique anchors**: The find_block must match EXACTLY 1 location
    3. **Whitespace normalization**: Handles trailing spaces, tabs, etc.
    4. **Validation**: Checks content before and after edit
    
    System Prompt Constraint (add to all coding agents):
    ```
    CRITICAL: You MUST NOT use line numbers for edits. 
    Use search_and_replace with a unique anchor string (3-5 lines of context).
    ```
    
    Example:
        >>> editor = ReliableEditor()
        >>> 
        >>> # CORRECT: Using unique anchor block
        >>> result = editor.search_and_replace(
        ...     "src/models/user.py",
        ...     find_block='''
        ... def authenticate(self, password: str) -> bool:
        ...     \"\"\"Authenticate the user.\"\"\"
        ...     return check_password(password, self.password_hash)
        ... ''',
        ...     replace_block='''
        ... def authenticate(self, password: str) -> bool:
        ...     \"\"\"Authenticate the user with rate limiting.\"\"\"
        ...     if self.is_locked_out():
        ...         raise AuthenticationError("Account locked")
        ...     return check_password(password, self.password_hash)
        ... '''
        ... )
        >>> 
        >>> # WRONG: Using line numbers (will be rejected)
        >>> # editor.replace_lines("file.py", 10, 15, new_content)  # NOT ALLOWED
    """
    
    def __init__(
        self,
        normalize_whitespace: bool = True,
        keep_history: bool = True,
        max_history: int = 100,
        mandatory_validation: bool = True,
        enable_linting: bool = False,
    ):
        """
        Initialize the Reliable Editor.
        
        Args:
            normalize_whitespace: Whether to normalize whitespace when matching.
            keep_history: Whether to keep edit history for rollback.
            max_history: Maximum history entries to keep.
            mandatory_validation: If True, automatically validates syntax after edit (Phase 7).
            enable_linting: If True, runs full linter checks (slower but thorough).
        """
        self.normalize_whitespace = normalize_whitespace
        self.keep_history = keep_history
        self.max_history = max_history
        self.mandatory_validation = mandatory_validation
        self.enable_linting = enable_linting
        
        self._history: List[EditHistoryEntry] = []
    
    def search_and_replace(
        self,
        file_path: str,
        find_block: str,
        replace_block: str,
        *,
        strict: bool = True,
        dry_run: bool = False,
    ) -> EditResult:
        """
        The ONLY allowed edit primitive.
        
        Searches for find_block and replaces it with replace_block.
        
        Validation rules:
        - find_block must match EXACTLY 1 location
        - 0 matches = AmbiguousEditError("Anchor not found")
        - >1 matches = AmbiguousEditError("Anchor found multiple times")
        
        Args:
            file_path: Path to the file to edit.
            find_block: Unique anchor block to find (3-5 lines recommended).
            replace_block: Content to replace anchor with.
            strict: If True, require exact match. If False, normalize whitespace.
            dry_run: If True, validate but don't apply changes.
            
        Returns:
            EditResult indicating success/failure.
            
        Raises:
            AmbiguousEditError: If anchor matches 0 or >1 times.
            EditValidationError: If file doesn't exist or other validation fails.
        """
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            raise EditValidationError(f"File not found: {file_path}")
        
        # Read current content
        content = path.read_text(encoding='utf-8')
        
        # Normalize if needed
        find_normalized = self._normalize(find_block) if self.normalize_whitespace and not strict else find_block
        content_normalized = self._normalize(content) if self.normalize_whitespace and not strict else content
        
        # Count matches
        match_count = content_normalized.count(find_normalized)
        
        if match_count == 0:
            # Try with additional whitespace normalization
            if not strict:
                match_count = self._fuzzy_match_count(content, find_block)
                
            if match_count == 0:
                raise AmbiguousEditError(
                    f"Anchor not found in {file_path}. "
                    f"Provide more context in find_block or check for whitespace differences.\n\n"
                    f"Looking for:\n{find_block[:200]}..."
                )
        
        if match_count > 1:
            raise AmbiguousEditError(
                f"Anchor found {match_count} times in {file_path}. "
                f"Provide more unique context in find_block to identify a single location."
            )
        
        # Apply replacement
        if self.normalize_whitespace and not strict:
            new_content = self._normalized_replace(content, find_block, replace_block)
        else:
            new_content = content.replace(find_block, replace_block)
        
        # Validate replacement happened
        if new_content == content:
            raise EditValidationError(
                f"Replacement had no effect in {file_path}. "
                f"Check that find_block and replace_block are different."
            )
        
        # Calculate lines changed
        old_lines = content.count('\n')
        new_lines = new_content.count('\n')
        lines_changed = abs(new_lines - old_lines) + 1
        
        # Dry run - return without writing
        if dry_run:
            return EditResult(
                success=True,
                file_path=file_path,
                old_content_preview=find_block[:100],
                new_content_preview=replace_block[:100],
                lines_changed=lines_changed,
            )
        
        # Save history
        if self.keep_history:
            self._add_history(EditHistoryEntry(
                file_path=file_path,
                original_content=content,
                new_content=new_content,
                find_block=find_block,
                replace_block=replace_block,
                timestamp=datetime.utcnow(),
            ))
        
        # Write new content
        path.write_text(new_content, encoding='utf-8')
        
        result = EditResult(
            success=True,
            file_path=file_path,
            old_content_preview=find_block[:100],
            new_content_preview=replace_block[:100],
            lines_changed=lines_changed,
        )
        
        # Phase 7: MANDATORY post-edit validation
        # This prevents agents from breaking syntax, even with valid anchored edits
        if self.mandatory_validation:
            validation_result = self._validate_post_edit(file_path, content, new_content)
            
            result.syntax_valid = validation_result["valid"]
            result.validation_message = validation_result["reason"]
            
            if not validation_result["valid"]:
                # AUTO-REVERT on validation failure
                print(f"⚠️  [Editor] Syntax validation failed, reverting...")
                print(f"   File: {file_path}")
                print(f"   Reason: {validation_result['reason']}")
                
                # Revert to original content
                path.write_text(content, encoding='utf-8')
                
                # Remove from history (edit was reverted)
                if self.keep_history and self._history:
                    self._history.pop()
                
                raise EditValidationError(
                    f"Edit validation failed in {file_path}. "
                    f"Reason: {validation_result['reason']}\n"
                    f"The file has been reverted to its original state. "
                    f"Please fix the syntax error in your replacement block."
                )
        
        # Optional: Run full linter if enabled (slower but more thorough)
        if self.enable_linting:
            from src.tools.validation import run_linting
            language = self._detect_language(file_path)
            if language:
                lint_result = run_linting(file_path, language)
                if lint_result.get("status") == "success":
                    result.lint_issues = lint_result.get("issues", [])
                    if result.lint_issues:
                        print(f"⚠️  [Editor] Linting found {len(result.lint_issues)} issue(s)")
                        # Note: We don't revert on lint issues, just report them
        
        return result
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension."""
        suffix = Path(file_path).suffix.lower()
        
        if suffix == '.py':
            return "python"
        elif suffix in ('.ts', '.tsx'):
            return "typescript"
        elif suffix in ('.js', '.jsx'):
            return "javascript"
        elif suffix in ('.java',):
            return "java"
        elif suffix in ('.go',):
            return "go"
        
        return None
    
    def _normalize(self, text: str) -> str:
        """Normalize whitespace for matching."""
        # Replace tabs with spaces
        text = text.replace('\t', '    ')
        # Normalize line endings
        text = text.replace('\r\n', '\n')
        # Remove trailing whitespace from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        return text
    
    def _fuzzy_match_count(self, content: str, find_block: str) -> int:
        """Count matches with fuzzy whitespace handling."""
        # Normalize both for comparison
        content_norm = self._normalize(content)
        find_norm = self._normalize(find_block)
        
        # Try exact normalized match first
        count = content_norm.count(find_norm)
        if count > 0:
            return count
        
        # Try with collapsed whitespace
        content_collapsed = re.sub(r'\s+', ' ', content_norm)
        find_collapsed = re.sub(r'\s+', ' ', find_norm)
        
        return content_collapsed.count(find_collapsed)
    
    def _normalized_replace(self, content: str, find_block: str, replace_block: str) -> str:
        """Perform replacement with whitespace normalization."""
        # Try exact match first
        if find_block in content:
            return content.replace(find_block, replace_block, 1)
        
        # Try normalized match
        content_lines = content.split('\n')
        find_lines = [line.rstrip() for line in find_block.split('\n')]
        replace_lines = replace_block.split('\n')
        
        # Find the start position
        start_idx = self._find_block_start(content_lines, find_lines)
        if start_idx == -1:
            # Fall back to basic replacement with normalized content
            return self._normalize(content).replace(
                self._normalize(find_block),
                replace_block,
                1
            )
        
        # Perform the replacement
        end_idx = start_idx + len(find_lines)
        result_lines = content_lines[:start_idx] + replace_lines + content_lines[end_idx:]
        
        return '\n'.join(result_lines)
    
    def _find_block_start(self, content_lines: List[str], find_lines: List[str]) -> int:
        """Find the starting line index of a block."""
        if not find_lines:
            return -1
        
        first_line_stripped = find_lines[0].strip()
        
        for i, line in enumerate(content_lines):
            if line.strip() == first_line_stripped:
                # Check if rest of block matches
                if self._block_matches(content_lines[i:], find_lines):
                    return i
        
        return -1
    
    def _block_matches(self, content_lines: List[str], find_lines: List[str]) -> bool:
        """Check if content lines match find lines (ignoring trailing whitespace)."""
        if len(content_lines) < len(find_lines):
            return False
        
        for i, find_line in enumerate(find_lines):
            if content_lines[i].rstrip() != find_line.rstrip():
                return False
        
        return True
    
    def _add_history(self, entry: EditHistoryEntry) -> None:
        """Add entry to history, maintaining max size."""
        self._history.append(entry)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
    
    def undo_last(self) -> Optional[EditResult]:
        """
        Undo the last edit.
        
        Returns:
            EditResult if undo was successful, None if no history.
        """
        if not self._history:
            return None
        
        entry = self._history.pop()
        path = Path(entry.file_path)
        
        # Verify current content matches what we replaced with
        current = path.read_text(encoding='utf-8')
        if current != entry.new_content:
            raise EditValidationError(
                f"Cannot undo: file {entry.file_path} has been modified since last edit"
            )
        
        # Restore original
        path.write_text(entry.original_content, encoding='utf-8')
        
        return EditResult(
            success=True,
            file_path=entry.file_path,
            old_content_preview=entry.replace_block[:100],
            new_content_preview=entry.find_block[:100],
        )
    
    def get_history(self, file_path: Optional[str] = None) -> List[EditHistoryEntry]:
        """
        Get edit history.
        
        Args:
            file_path: Optional filter for specific file.
            
        Returns:
            List of edit history entries.
        """
        if file_path:
            return [e for e in self._history if e.file_path == file_path]
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear edit history."""
        self._history.clear()
    
    def _validate_post_edit(
        self,
        file_path: str,
        original_content: str,
        new_content: str,
    ) -> Dict[str, Any]:
        """
        Validate file after edit (Phase 7: Mandatory validation).
        
        Performs lightweight syntax checks to ensure the edit didn't
        break the file. This is MANDATORY to prevent agents from
        corrupting code with syntactically invalid replacements.
        
        Args:
            file_path: Path to the edited file
            original_content: Original file content (for comparison)
            new_content: New file content after edit
            
        Returns:
            Dict with "valid" (bool) and "reason" (str) keys
        """
        # Detect language from file extension
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        # Python syntax validation
        if suffix == '.py':
            try:
                import ast
                ast.parse(new_content)
                return {"valid": True, "reason": ""}
            except SyntaxError as e:
                return {
                    "valid": False,
                    "reason": f"Python syntax error: {e.msg} at line {e.lineno}"
                }
        
        # JavaScript/TypeScript validation (basic)
        elif suffix in ('.js', '.jsx', '.ts', '.tsx'):
            # Check for basic bracket/brace matching
            validation = self._check_bracket_matching(new_content)
            if not validation["valid"]:
                return validation
        
        # JSON validation
        elif suffix == '.json':
            try:
                import json
                json.loads(new_content)
                return {"valid": True, "reason": ""}
            except json.JSONDecodeError as e:
                return {
                    "valid": False,
                    "reason": f"JSON syntax error: {e.msg} at line {e.lineno}"
                }
        
        # YAML validation
        elif suffix in ('.yaml', '.yml'):
            try:
                import yaml
                yaml.safe_load(new_content)
                return {"valid": True, "reason": ""}
            except yaml.YAMLError as e:
                return {
                    "valid": False,
                    "reason": f"YAML syntax error: {str(e)}"
                }
        
        # For other file types, check basic sanity
        # (at minimum, ensure file is not corrupted)
        if len(new_content) == 0 and len(original_content) > 0:
            return {
                "valid": False,
                "reason": "Edit resulted in empty file (possible corruption)"
            }
        
        # Default: assume valid
        return {"valid": True, "reason": ""}
    
    def _check_bracket_matching(self, content: str) -> Dict[str, Any]:
        """
        Check if brackets, braces, and parentheses are balanced.
        
        This is a lightweight check for JS/TS files.
        
        Args:
            content: File content to check
            
        Returns:
            Dict with "valid" and "reason" keys
        """
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        line_num = 1
        
        for i, char in enumerate(content):
            if char == '\n':
                line_num += 1
            
            if char in pairs:
                stack.append((char, line_num))
            elif char in pairs.values():
                if not stack:
                    return {
                        "valid": False,
                        "reason": f"Unmatched closing bracket '{char}' at line {line_num}"
                    }
                opening, opening_line = stack.pop()
                if pairs[opening] != char:
                    return {
                        "valid": False,
                        "reason": f"Mismatched brackets: '{opening}' at line {opening_line} closed with '{char}' at line {line_num}"
                    }
        
        if stack:
            opening, line = stack[-1]
            return {
                "valid": False,
                "reason": f"Unclosed bracket '{opening}' at line {line}"
            }
        
        return {"valid": True, "reason": ""}
    
    def validate_anchor(
        self,
        file_path: str,
        find_block: str,
    ) -> Tuple[bool, str]:
        """
        Validate an anchor without making changes.
        
        Args:
            file_path: Path to the file.
            find_block: Anchor block to validate.
            
        Returns:
            Tuple of (is_valid, message).
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False, f"File not found: {file_path}"
            
            content = path.read_text(encoding='utf-8')
            
            # Count matches
            match_count = content.count(find_block)
            
            if self.normalize_whitespace and match_count == 0:
                match_count = self._fuzzy_match_count(content, find_block)
            
            if match_count == 0:
                return False, "Anchor not found. Provide more context or check whitespace."
            elif match_count == 1:
                return True, "Anchor is unique and valid."
            else:
                return False, f"Anchor found {match_count} times. Provide more unique context."
                
        except Exception as e:
            return False, f"Validation error: {e}"


# System prompt constraint to add to coding agents
EDIT_SYSTEM_PROMPT = """
## CRITICAL: Edit Protocol

You MUST NOT use line numbers for edits. LLMs are unreliable at counting lines.

Use `search_and_replace` with a unique anchor string:
1. Include 3-5 lines of context around the change
2. The anchor must be unique in the file
3. Include surrounding code that won't change

Example (CORRECT):
```
find_block = '''
def process_user(self, user_id: str) -> User:
    \"\"\"Process a user request.\"\"\"
    user = self.db.get_user(user_id)
    return user
'''

replace_block = '''
def process_user(self, user_id: str) -> User:
    \"\"\"Process a user request with validation.\"\"\"
    if not user_id:
        raise ValueError("user_id is required")
    user = self.db.get_user(user_id)
    return user
'''
```

Example (WRONG - will fail):
```
# DO NOT use line numbers
replace_lines(10, 15, new_content)  # FORBIDDEN
```
"""


__all__ = [
    "ReliableEditor",
    "EditResult",
    "EditHistoryEntry",
    "AmbiguousEditError",
    "EditValidationError",
    "EDIT_SYSTEM_PROMPT",
]

