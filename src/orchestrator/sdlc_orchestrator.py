"""SDLC orchestrator coordinating all agents with shared hooks."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

from config.agent_config import PROJECT_ROOT, get_user_email, resolve_model_config
from src.config.project_config import ProjectConfig, load_project_config
from src.hooks import documentation_hooks


class SDLCOrchestrator:
    """Creates agent option objects with hooks enabled.
    
    The orchestrator can operate in two modes:
    1. Framework mode: When no target_dir is provided, operates on the framework itself
    2. Target mode: When target_dir is provided, operates on a target repository
    
    In target mode, the orchestrator loads project config from .sdlc/config.yaml
    and uses the target directory as the working directory for agents.
    """

    def __init__(
        self, 
        project_path: str | None = None,
        target_dir: Optional[Path] = None,
        project_config: Optional[ProjectConfig] = None,
    ) -> None:
        """Initialize the SDLC orchestrator.
        
        Args:
            project_path: Legacy path argument (deprecated, use target_dir)
            target_dir: Path to target repository to operate on
            project_config: Pre-loaded project config (loaded from target_dir if not provided)
        """
        # Determine the working directory
        if target_dir:
            self.target_dir = Path(target_dir)
            self.project_path = str(target_dir)
        else:
            self.target_dir = Path(project_path) if project_path else PROJECT_ROOT
            self.project_path = project_path or str(PROJECT_ROOT)
        
        # Load project config if not provided
        self.project_config = project_config
        if self.project_config is None and self.target_dir:
            self.project_config = load_project_config(self.target_dir)
        
        self.hooks: Dict[str, List[HookMatcher]] = {
            "PreToolUse": [HookMatcher(hooks=[documentation_hooks.pre_tool_use_logger])],
            "PostToolUse": [HookMatcher(hooks=[documentation_hooks.post_tool_use_logger])],
            "SessionStart": [HookMatcher(hooks=[documentation_hooks.session_start_logger])],
            "SessionEnd": [HookMatcher(hooks=[documentation_hooks.session_end_logger])],
            "Stop": [HookMatcher(hooks=[documentation_hooks.stop_logger])],
        }

    def get_memory_path(self, memory_type: str = "prd") -> Path:
        """Get the path to a memory file.
        
        Args:
            memory_type: Type of memory (prd, architecture_plan, qa_summary, etc.)
            
        Returns:
            Path to the memory file in target's .sdlc/memories/ directory
        """
        if self.project_config:
            memories_dir = self.project_config.get_memory_path(self.target_dir)
        else:
            memories_dir = self.target_dir / ".sdlc" / "memories"
        
        memories_dir.mkdir(parents=True, exist_ok=True)
        return memories_dir / f"{memory_type}.xml"
    
    def get_project_context(self) -> Dict[str, any]:
        """Get project context for prompt injection.
        
        Returns:
            Dictionary with project context, or empty dict if no config
        """
        if self.project_config:
            return self.project_config.to_context_dict()
        return {}

    def _base_options(
        self,
        model_key: str,
        tools: Iterable[str],
        include_code_execution: bool = False,
        agent_name: Optional[str] = None,
    ) -> ClaudeAgentOptions:
        """Build base agent options with project config integration.
        
        Args:
            model_key: Model profile key (strategy, build, etc.)
            tools: Base tools to include
            include_code_execution: Whether to enable code execution
            agent_name: Agent name for applying overrides
        """
        model = resolve_model_config(model_key, include_code_execution=include_code_execution)
        allowed_tools = list(dict.fromkeys([*tools, *model.allowed_tools]))
        
        # Apply budget override from project config if available
        budget = None
        if agent_name and self.project_config:
            override = self.project_config.get_agent_override(agent_name)
            if override and override.budget_usd:
                budget = override.budget_usd
        
        # Note: Beta features are auto-enabled via setting_sources and allowed_tools
        # SDK 0.1.10 doesn't support betas parameter directly
        # Note: user parameter removed - email should be configured via .claude/user_config.json
        # or CLAUDE_AGENT_USER_EMAIL env var, which is read by setting_sources=["user", "project"]
        options = ClaudeAgentOptions(
            cwd=self.project_path,
            setting_sources=["user", "project"],
            allowed_tools=allowed_tools,
            model=model.name,
            hooks=self.hooks,
        )
        
        # Set budget if available (check if SDK supports it)
        if budget is not None:
            try:
                options.budget_usd = budget
            except AttributeError:
                pass  # SDK version doesn't support budget_usd
        
        return options

    def strategy_options(self, agent_name: Optional[str] = None) -> ClaudeAgentOptions:
        """Get options for strategy agents (ProductSpec, ArchGuard, SprintMaster)."""
        return self._base_options(
            "strategy", 
            tools=["Skill", "Read", "Write", "Bash", "memory"],
            agent_name=agent_name,
        )

    def strategy_with_code_execution(self, agent_name: Optional[str] = None) -> ClaudeAgentOptions:
        """Get options for strategy agents that need code execution."""
        return self._base_options(
            "strategy",
            tools=["Skill", "Read", "Write", "Bash", "memory", "code_execution"],
            include_code_execution=True,
            agent_name=agent_name,
        )

    def build_options(self, agent_name: Optional[str] = None) -> ClaudeAgentOptions:
        """Get options for build agents (CodeCraft, QualityGuard)."""
        return self._base_options(
            "build",
            tools=["Skill", "Read", "Write", "Bash", "memory", "code_execution"],
            include_code_execution=True,
            agent_name=agent_name,
        )


__all__ = ["SDLCOrchestrator"]

