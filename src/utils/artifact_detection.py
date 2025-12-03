"""
Artifact detection utilities for parsing tool outputs and identifying deployments, PRs, commits.
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional


def detect_artifacts_from_output(
    tool_name: str, output_data: Dict, input_data: Optional[Dict] = None
) -> List[Dict]:
    """
    Detect artifacts (deployments, PRs, commits) from tool output.
    
    Args:
        tool_name: Name of the tool that produced the output
        output_data: Tool output dictionary
        input_data: Tool input dictionary (optional)
        
    Returns:
        List of detected artifacts with type, url, identifier, metadata
    """
    artifacts = []
    
    # Combine all text output for pattern matching
    output_text = ""
    if isinstance(output_data, dict):
        output_text = json.dumps(output_data)
        # Also check common output fields
        if "stdout" in output_data:
            output_text += "\n" + str(output_data["stdout"])
        if "content" in output_data:
            output_text += "\n" + str(output_data["content"])
        if "result" in output_data:
            output_text += "\n" + str(output_data["result"])
    else:
        output_text = str(output_data)
    
    # Detect Pull Request URLs
    pr_patterns = [
        r"https?://(?:github|gitlab|bitbucket)\.com/[^/\s]+/[^/\s]+/pull[s]?/(\d+)",
        r"pull request #(\d+)",
        r"PR #(\d+)",
        r"https?://.*pull.*/(\d+)",
    ]
    for pattern in pr_patterns:
        matches = re.finditer(pattern, output_text, re.IGNORECASE)
        for match in matches:
            pr_number = match.group(1) if match.lastindex else None
            artifacts.append({
                "artifact_type": "pr",
                "artifact_url": match.group(0),
                "identifier": pr_number or match.group(0),
                "metadata": {"source": "pattern_match", "tool": tool_name},
            })
    
    # Detect Deployment URLs
    deployment_patterns = [
        r"https?://.*deploy.*\.(?:com|io|net|org|app)[^\s]*",
        r"deployment.*(?:https?://[^\s]+)",
        r"deployed.*to.*(?:https?://[^\s]+)",
        r"https?://.*\.vercel\.app[^\s]*",
        r"https?://.*\.netlify\.app[^\s]*",
        r"https?://.*\.herokuapp\.com[^\s]*",
        r"https?://.*\.railway\.app[^\s]*",
        r"https?://.*\.fly\.dev[^\s]*",
    ]
    for pattern in deployment_patterns:
        matches = re.finditer(pattern, output_text, re.IGNORECASE)
        for match in matches:
            url = match.group(0)
            # Extract deployment identifier from URL
            identifier = url.split("/")[-1] if "/" in url else url
            artifacts.append({
                "artifact_type": "deployment",
                "artifact_url": url,
                "identifier": identifier,
                "metadata": {"source": "pattern_match", "tool": tool_name},
            })
    
    # Detect Git Commits
    commit_patterns = [
        r"commit\s+([a-f0-9]{7,40})",
        r"\[commit\s+([a-f0-9]{7,40})\]",
        r"https?://.*commit[s]?/([a-f0-9]{7,40})",
    ]
    for pattern in commit_patterns:
        matches = re.finditer(pattern, output_text, re.IGNORECASE)
        for match in matches:
            commit_hash = match.group(1)
            commit_url = match.group(0) if match.group(0).startswith("http") else None
            artifacts.append({
                "artifact_type": "commit",
                "artifact_url": commit_url,
                "identifier": commit_hash,
                "metadata": {"source": "pattern_match", "tool": tool_name},
            })
    
    # Detect file changes (for code execution)
    if tool_name in ["Write", "code_execution"] and input_data:
        file_path = input_data.get("path") or input_data.get("file")
        if file_path:
            artifacts.append({
                "artifact_type": "file",
                "artifact_url": None,
                "identifier": file_path,
                "metadata": {"source": "tool_input", "tool": tool_name},
            })
    
    # Remove duplicates (same type + identifier)
    seen = set()
    unique_artifacts = []
    for artifact in artifacts:
        key = (artifact["artifact_type"], artifact["identifier"])
        if key not in seen:
            seen.add(key)
            unique_artifacts.append(artifact)
    
    return unique_artifacts


__all__ = ["detect_artifacts_from_output"]

