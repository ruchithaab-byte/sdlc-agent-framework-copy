"""Shared constants for agent configuration per SDK best practices."""

# Default max turns to prevent infinite loops (SDK best practice)
# Individual agents may override based on complexity
DEFAULT_MAX_TURNS = 50

# Role-specific max turns
MAX_TURNS_BY_ROLE = {
    "strategy": 50,      # Planning and analysis agents
    "build": 100,        # Code generation agents
    "review": 75,        # QA and code review agents
    "incident": 100,     # Incident investigation (may need extended interaction)
}

# Permission modes for different operation types
PERMISSION_MODES = {
    "default": "default",          # Standard permission prompts
    "accept_edits": "acceptEdits",  # Auto-accept file edits
    "bypass": "bypassPermissions",  # Bypass all (CI/CD only)
}

# Context management thresholds
CONTEXT_CLEAR_THRESHOLD = 50000  # Clear tool uses after this many input tokens

# Model resolution helpers
def get_max_turns_for_role(role: str) -> int:
    """Get the recommended max turns for a given agent role."""
    return MAX_TURNS_BY_ROLE.get(role, DEFAULT_MAX_TURNS)

