"""Validation tools for agent outputs."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path

def run_linting(file_path: str, language: str) -> Dict[str, Any]:
    """
    Run linting on a specific file based on language.
    
    Args:
        file_path: Path to the file to lint.
        language: Language of the file (python, typescript, javascript).
        
    Returns:
        Dict with status and issues found.
    """
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}
        
    if language == "python":
        # Check if pylint is installed
        try:
            subprocess.run(["pylint", "--version"], check=True, capture_output=True)
            result = subprocess.run(
                ["pylint", file_path, "--output-format=json"],
                capture_output=True,
                text=True
            )
            try:
                issues = json.loads(result.stdout)
                return {"status": "success", "tool": "pylint", "issues": issues}
            except json.JSONDecodeError:
                # If valid JSON isn't returned, maybe it passed perfectly or crashed
                return {"status": "success", "tool": "pylint", "issues": [], "raw_output": result.stdout}
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"status": "warning", "message": "pylint not installed or failed to run"}
            
    elif language in ["typescript", "javascript"]:
        # Check for eslint
        try:
            # Assuming npm run lint or direct eslint usage
            # This is a simplified check
            cmd = ["npx", "eslint", file_path, "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            try:
                issues = json.loads(result.stdout)
                return {"status": "success", "tool": "eslint", "issues": issues}
            except json.JSONDecodeError:
                 return {"status": "success", "tool": "eslint", "issues": [], "raw_output": result.stdout}
        except (subprocess.CalledProcessError, FileNotFoundError):
             return {"status": "warning", "message": "eslint not installed or failed to run"}
             
    return {"status": "error", "message": f"Unsupported language: {language}"}

def validate_structure(content: str, required_sections: List[str]) -> Dict[str, Any]:
    """
    Validate that text content contains required sections (e.g. for PRDs).
    
    Args:
        content: The text content to check.
        required_sections: List of section headers expected.
        
    Returns:
        Dict with validation results.
    """
    missing = []
    for section in required_sections:
        if section not in content:
            missing.append(section)
            
    return {
        "valid": len(missing) == 0,
        "missing_sections": missing
    }

