"""
Verification Hooks for SDLC Agents.

Implements Anthropic's best practice: "Agents that can check and improve their
own output are fundamentally more reliable."

Provides hooks for:
- Running linters after code generation (eslint, ruff, tsc)
- Executing tests after code changes
- Feeding back errors to the agent for self-correction

Reference: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
"The best form of feedback is providing clearly defined rules for an output,
then explaining which rules failed and why."

Usage:
    from src.hooks.verification_hooks import create_verification_hooks
    
    # Add to build_hooks() in hooks/__init__.py
    hooks = create_verification_hooks(
        run_linters=True,
        run_tests=False,  # Only for full verification
        auto_fix=False,   # Let agent decide fixes
    )
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from claude_agent_sdk import HookMatcher


# Tools that modify files and need verification
FILE_MODIFYING_TOOLS = {
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
}

# File extension to linter mapping
LINTER_CONFIG = {
    # JavaScript/TypeScript
    ".js": {"cmd": ["npx", "eslint", "--fix"], "name": "ESLint"},
    ".jsx": {"cmd": ["npx", "eslint", "--fix"], "name": "ESLint"},
    ".ts": {"cmd": ["npx", "tsc", "--noEmit"], "name": "TypeScript"},
    ".tsx": {"cmd": ["npx", "tsc", "--noEmit"], "name": "TypeScript"},
    # Python
    ".py": {"cmd": ["ruff", "check", "--fix"], "name": "Ruff"},
    # Go
    ".go": {"cmd": ["go", "vet"], "name": "Go Vet"},
    # Rust
    ".rs": {"cmd": ["cargo", "clippy", "--fix", "--allow-dirty"], "name": "Clippy"},
}

# Test command detection patterns
TEST_PATTERNS = {
    "package.json": "npm test",
    "pyproject.toml": "pytest",
    "Cargo.toml": "cargo test",
    "go.mod": "go test ./...",
    "Makefile": "make test",
}


class VerificationResult:
    """Result of a verification check (lint/test)."""
    
    def __init__(
        self,
        success: bool,
        tool: str,
        file_path: str,
        output: str = "",
        errors: List[str] = None,
        warnings: List[str] = None,
    ):
        self.success = success
        self.tool = tool
        self.file_path = file_path
        self.output = output
        self.errors = errors or []
        self.warnings = warnings or []
    
    def to_feedback_message(self) -> str:
        """Convert to a message for agent feedback."""
        if self.success:
            return f"✅ {self.tool} passed for {self.file_path}"
        
        parts = [f"❌ {self.tool} failed for {self.file_path}:"]
        
        if self.errors:
            parts.append("\nErrors:")
            for error in self.errors[:10]:  # Limit to 10 errors
                parts.append(f"  - {error}")
            if len(self.errors) > 10:
                parts.append(f"  ... and {len(self.errors) - 10} more errors")
        
        if self.warnings:
            parts.append("\nWarnings:")
            for warning in self.warnings[:5]:  # Limit to 5 warnings
                parts.append(f"  - {warning}")
        
        parts.append("\nPlease fix these issues and try again.")
        return "\n".join(parts)


def _detect_project_root(file_path: str) -> Optional[Path]:
    """Detect project root by looking for package.json, pyproject.toml, etc."""
    path = Path(file_path).resolve()
    
    for parent in [path.parent, *path.parents]:
        for marker in ["package.json", "pyproject.toml", "Cargo.toml", "go.mod", ".git"]:
            if (parent / marker).exists():
                return parent
    
    return path.parent


def _run_linter(file_path: str, cwd: Optional[str] = None) -> VerificationResult:
    """
    Run the appropriate linter for a file.
    
    Args:
        file_path: Path to the file to lint
        cwd: Working directory for the linter
        
    Returns:
        VerificationResult with lint outcome
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext not in LINTER_CONFIG:
        return VerificationResult(
            success=True,
            tool="none",
            file_path=file_path,
            output="No linter configured for this file type",
        )
    
    config = LINTER_CONFIG[ext]
    cmd = config["cmd"] + [str(path)]
    linter_name = config["name"]
    
    # Detect project root for proper linter config
    project_root = _detect_project_root(file_path)
    working_dir = cwd or str(project_root) if project_root else None
    
    try:
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        # Parse errors from output
        errors = []
        warnings = []
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "error" in line.lower():
                errors.append(line)
            elif "warning" in line.lower() or "warn" in line.lower():
                warnings.append(line)
        
        return VerificationResult(
            success=success,
            tool=linter_name,
            file_path=file_path,
            output=output,
            errors=errors,
            warnings=warnings,
        )
        
    except FileNotFoundError:
        return VerificationResult(
            success=True,  # Don't fail if linter not installed
            tool=linter_name,
            file_path=file_path,
            output=f"{linter_name} not installed, skipping verification",
        )
    except subprocess.TimeoutExpired:
        return VerificationResult(
            success=False,
            tool=linter_name,
            file_path=file_path,
            output=f"{linter_name} timed out after 60 seconds",
            errors=[f"{linter_name} timed out"],
        )
    except Exception as e:
        return VerificationResult(
            success=False,
            tool=linter_name,
            file_path=file_path,
            output=str(e),
            errors=[str(e)],
        )


def _run_typecheck(file_path: str, cwd: Optional[str] = None) -> VerificationResult:
    """
    Run TypeScript type checking for TS/TSX files.
    
    Runs as separate check since tsc --noEmit doesn't fix, just checks.
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext not in [".ts", ".tsx"]:
        return VerificationResult(
            success=True,
            tool="none",
            file_path=file_path,
        )
    
    project_root = _detect_project_root(file_path)
    if not project_root:
        return VerificationResult(
            success=True,
            tool="TypeScript",
            file_path=file_path,
            output="Could not find project root for TypeScript check",
        )
    
    # Check if tsconfig.json exists
    tsconfig = project_root / "tsconfig.json"
    if not tsconfig.exists():
        return VerificationResult(
            success=True,
            tool="TypeScript",
            file_path=file_path,
            output="No tsconfig.json found, skipping type check",
        )
    
    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120,  # TypeScript can be slow
        )
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        # Parse TypeScript errors (format: file(line,col): error TS1234: message)
        errors = []
        for line in output.split("\n"):
            if "error TS" in line:
                errors.append(line.strip())
        
        return VerificationResult(
            success=success,
            tool="TypeScript",
            file_path=file_path,
            output=output,
            errors=errors,
        )
        
    except Exception as e:
        return VerificationResult(
            success=True,  # Don't fail if tsc not available
            tool="TypeScript",
            file_path=file_path,
            output=str(e),
        )


# Global configuration for verification hooks
_verification_config = {
    "run_linters": True,
    "run_tests": False,
    "auto_fix": False,
    "verbose": True,
}


def configure_verification(
    run_linters: bool = True,
    run_tests: bool = False,
    auto_fix: bool = False,
    verbose: bool = True,
) -> None:
    """
    Configure verification hook behavior.
    
    Args:
        run_linters: Run linters after file modifications
        run_tests: Run tests after file modifications (expensive)
        auto_fix: Automatically apply linter fixes
        verbose: Print detailed verification output
    """
    global _verification_config
    _verification_config.update({
        "run_linters": run_linters,
        "run_tests": run_tests,
        "auto_fix": auto_fix,
        "verbose": verbose,
    })


async def verification_post_tool_hook(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Run verification after file-modifying tools complete.
    
    This hook implements Anthropic's verification loop by:
    1. Detecting which file was modified
    2. Running appropriate linters
    3. Feeding back any errors to the agent
    
    Returns:
        Dict with systemMessage if errors need fixing
    """
    tool_name = input_data.get("tool_name", "")
    
    # Only verify file-modifying tools
    if tool_name not in FILE_MODIFYING_TOOLS:
        return {}
    
    # Skip if linters disabled
    if not _verification_config.get("run_linters", True):
        return {}
    
    # Get the file path from tool input
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path")
    
    if not file_path:
        return {}
    
    # Get working directory
    cwd = input_data.get("cwd")
    session_id = input_data.get("session_id", "unknown")
    
    # Run linter
    lint_result = _run_linter(file_path, cwd)
    
    # Run TypeScript check if applicable
    type_result = _run_typecheck(file_path, cwd)
    
    # Collect all feedback
    feedback_parts = []
    has_errors = False
    
    if not lint_result.success:
        feedback_parts.append(lint_result.to_feedback_message())
        has_errors = True
        if _verification_config.get("verbose"):
            print(f"🔍 [Verification] {lint_result.tool} found {len(lint_result.errors)} errors in {file_path}")
    elif _verification_config.get("verbose"):
        print(f"✅ [Verification] {lint_result.tool} passed for {file_path}")
    
    if not type_result.success:
        feedback_parts.append(type_result.to_feedback_message())
        has_errors = True
        if _verification_config.get("verbose"):
            print(f"🔍 [Verification] TypeScript found {len(type_result.errors)} errors")
    
    # If errors found, return feedback to agent
    if has_errors and feedback_parts:
        return {
            "systemMessage": (
                "⚠️ Code verification found issues that should be fixed:\n\n"
                + "\n\n".join(feedback_parts)
            )
        }
    
    return {}


async def test_runner_post_tool_hook(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str],
    context: Any,
) -> Dict[str, Any]:
    """
    Run tests after significant code changes.
    
    This is more expensive than linting, so it's disabled by default.
    Enable with configure_verification(run_tests=True).
    
    Returns:
        Dict with systemMessage if tests fail
    """
    tool_name = input_data.get("tool_name", "")
    
    # Only run after file modifications
    if tool_name not in FILE_MODIFYING_TOOLS:
        return {}
    
    # Skip if tests disabled
    if not _verification_config.get("run_tests", False):
        return {}
    
    # Get working directory
    cwd = input_data.get("cwd")
    if not cwd:
        return {}
    
    # Detect test command
    test_cmd = None
    for marker, cmd in TEST_PATTERNS.items():
        if (Path(cwd) / marker).exists():
            test_cmd = cmd
            break
    
    if not test_cmd:
        return {}
    
    session_id = input_data.get("session_id", "unknown")
    
    if _verification_config.get("verbose"):
        print(f"🧪 [Verification] Running tests: {test_cmd}")
    
    try:
        result = subprocess.run(
            test_cmd.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for tests
        )
        
        if result.returncode != 0:
            # Extract test failures
            output = result.stdout + result.stderr
            
            return {
                "systemMessage": (
                    f"⚠️ Tests failed after code change. Output:\n\n"
                    f"```\n{output[:2000]}\n```\n\n"
                    "Please fix the failing tests."
                )
            }
        elif _verification_config.get("verbose"):
            print(f"✅ [Verification] Tests passed")
            
    except subprocess.TimeoutExpired:
        print(f"⚠️ [Verification] Tests timed out after 5 minutes")
    except Exception as e:
        print(f"⚠️ [Verification] Test error: {e}")
    
    return {}


def create_verification_hooks(
    run_linters: bool = True,
    run_tests: bool = False,
    auto_fix: bool = False,
    verbose: bool = True,
) -> Dict[str, List[HookMatcher]]:
    """
    Create verification hooks for agent options.
    
    Args:
        run_linters: Enable linter verification
        run_tests: Enable test execution (expensive)
        auto_fix: Automatically apply linter fixes
        verbose: Print detailed output
        
    Returns:
        Dict of hooks to merge with other hooks
        
    Example:
        >>> from src.hooks.verification_hooks import create_verification_hooks
        >>> hooks = create_verification_hooks(run_linters=True)
        >>> # Merge with other hooks in build_hooks()
    """
    # Configure global settings
    configure_verification(
        run_linters=run_linters,
        run_tests=run_tests,
        auto_fix=auto_fix,
        verbose=verbose,
    )
    
    post_tool_hooks = []
    
    if run_linters:
        post_tool_hooks.append(verification_post_tool_hook)
    
    if run_tests:
        post_tool_hooks.append(test_runner_post_tool_hook)
    
    if not post_tool_hooks:
        return {}
    
    return {
        "PostToolUse": [HookMatcher(hooks=post_tool_hooks)],
    }


__all__ = [
    "create_verification_hooks",
    "configure_verification",
    "verification_post_tool_hook",
    "test_runner_post_tool_hook",
    "VerificationResult",
    "LINTER_CONFIG",
]

