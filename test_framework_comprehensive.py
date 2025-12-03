#!/usr/bin/env python3
"""
Comprehensive Framework Test Suite

Tests the SDLC Agent Framework against Anthropic best practices.
Validates configuration, structure, and integration points.
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestResult:
    """Test result container."""
    def __init__(self, name: str, passed: bool, message: str = "", details: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        result = f"{status}: {self.name}"
        if self.message:
            result += f"\n   {self.message}"
        if self.details:
            result += f"\n   Details: {self.details}"
        return result


def test_model_configuration() -> List[TestResult]:
    """Test model configuration validity."""
    results = []
    
    try:
        from config.agent_config import MODEL_REGISTRY, resolve_model_config
        
        # Test 1: All profiles exist
        expected_profiles = ["strategy", "build", "infra", "vertex-strategy", "vertex-build"]
        for profile in expected_profiles:
            try:
                config = resolve_model_config(profile)
                results.append(TestResult(
                    f"Model profile '{profile}' exists",
                    True,
                    f"Model: {config.name}"
                ))
            except KeyError:
                results.append(TestResult(
                    f"Model profile '{profile}' exists",
                    False,
                    f"Profile not found in MODEL_REGISTRY"
                ))
        
        # Test 2: Model names are valid format
        invalid_models = []
        for profile, config in MODEL_REGISTRY.items():
            model_name = config.name
            # Check for invalid patterns
            if "@" in model_name and "claude-opus-4" in model_name:
                invalid_models.append(f"{profile}: {model_name}")
            elif "claude-sonnet-4-20250514" in model_name:
                invalid_models.append(f"{profile}: {model_name}")
        
        if invalid_models:
            results.append(TestResult(
                "Model names use valid format",
                False,
                f"Invalid model names found: {', '.join(invalid_models)}"
            ))
        else:
            results.append(TestResult(
                "Model names use valid format",
                True,
                "All models use standard Anthropic format"
            ))
        
        # Test 3: Tools are properly configured
        build_config = resolve_model_config("build")
        required_tools = ["Skill", "Read", "Write", "Bash", "memory", "code_execution", "Agent"]
        missing_tools = [t for t in required_tools if t not in build_config.allowed_tools]
        
        if missing_tools:
            results.append(TestResult(
                "Build profile has required tools",
                False,
                f"Missing tools: {', '.join(missing_tools)}"
            ))
        else:
            results.append(TestResult(
                "Build profile has required tools",
                True
            ))
            
    except Exception as e:
        results.append(TestResult(
            "Model configuration loads",
            False,
            f"Error: {str(e)}"
        ))
    
    return results


def test_agent_profiles() -> List[TestResult]:
    """Test agent profile configuration."""
    results = []
    
    try:
        from config.agent_profiles import AGENT_PROFILES, get_agent_profile
        
        # Test 1: All expected agents exist
        expected_agents = [
            "productspec", "archguard", "sprintmaster", "codecraft",
            "qualityguard", "docuscribe", "infraops", "sentinel",
            "sre-triage", "finops"
        ]
        
        for agent_id in expected_agents:
            try:
                profile = get_agent_profile(agent_id)
                results.append(TestResult(
                    f"Agent '{agent_id}' profile exists",
                    True,
                    f"Model: {profile.model_profile}, Budget: ${profile.budget_usd or 0}"
                ))
            except KeyError:
                results.append(TestResult(
                    f"Agent '{agent_id}' profile exists",
                    False,
                    "Profile not found"
                ))
        
        # Test 2: CodeCraft has verification hooks enabled
        codecraft = get_agent_profile("codecraft")
        from src.hooks import HOOKS_PROFILES
        build_hooks = HOOKS_PROFILES.get("build", {})
        
        if build_hooks.get("run_linters"):
            results.append(TestResult(
                "CodeCraft has verification hooks enabled",
                True
            ))
        else:
            results.append(TestResult(
                "CodeCraft has verification hooks enabled",
                False,
                "run_linters not enabled in build profile"
            ))
        
        # Test 3: QualityGuard has Agent tool
        qualityguard = get_agent_profile("qualityguard")
        if "Agent" in qualityguard.extra_allowed_tools:
            results.append(TestResult(
                "QualityGuard has Agent tool for subagents",
                True
            ))
        else:
            results.append(TestResult(
                "QualityGuard has Agent tool for subagents",
                False,
                "Agent tool not in extra_allowed_tools"
            ))
            
    except Exception as e:
        results.append(TestResult(
            "Agent profiles load",
            False,
            f"Error: {str(e)}"
        ))
    
    return results


def test_verification_hooks() -> List[TestResult]:
    """Test verification hooks implementation."""
    results = []
    
    try:
        from src.hooks.verification_hooks import (
            create_verification_hooks,
            LINTER_CONFIG,
            FILE_MODIFYING_TOOLS,
        )
        
        # Test 1: Verification hooks can be created
        hooks = create_verification_hooks(run_linters=True)
        if hooks and "PostToolUse" in hooks:
            results.append(TestResult(
                "Verification hooks can be created",
                True
            ))
        else:
            results.append(TestResult(
                "Verification hooks can be created",
                False,
                "Hooks dict missing PostToolUse"
            ))
        
        # Test 2: Linter config has common file types
        required_linters = [".js", ".ts", ".py"]
        missing = [ext for ext in required_linters if ext not in LINTER_CONFIG]
        
        if missing:
            results.append(TestResult(
                "Linter config covers common file types",
                False,
                f"Missing: {', '.join(missing)}"
            ))
        else:
            results.append(TestResult(
                "Linter config covers common file types",
                True,
                f"Configured for: {', '.join(LINTER_CONFIG.keys())}"
            ))
        
        # Test 3: File modifying tools are tracked
        required_tools = ["Write", "Edit", "MultiEdit"]
        missing = [t for t in required_tools if t not in FILE_MODIFYING_TOOLS]
        
        if missing:
            results.append(TestResult(
                "File modifying tools are tracked",
                False,
                f"Missing: {', '.join(missing)}"
            ))
        else:
            results.append(TestResult(
                "File modifying tools are tracked",
                True
            ))
            
    except Exception as e:
        results.append(TestResult(
            "Verification hooks implementation",
            False,
            f"Error: {str(e)}"
        ))
    
    return results


def test_subagents() -> List[TestResult]:
    """Test subagent definitions."""
    results = []
    
    try:
        subagent_dir = PROJECT_ROOT / ".claude" / "agents"
        
        # Test 1: Required subagents exist
        required_subagents = ["code-reviewer-specialist", "test-generator", "plan-architect"]
        for subagent in required_subagents:
            subagent_file = subagent_dir / f"{subagent}.md"
            if subagent_file.exists():
                # Check it has proper frontmatter
                content = subagent_file.read_text()
                if "---" in content and "name:" in content:
                    results.append(TestResult(
                        f"Subagent '{subagent}' exists and formatted",
                        True
                    ))
                else:
                    results.append(TestResult(
                        f"Subagent '{subagent}' exists and formatted",
                        False,
                        "Missing frontmatter"
                    ))
            else:
                results.append(TestResult(
                    f"Subagent '{subagent}' exists",
                    False,
                    f"File not found: {subagent_file}"
                ))
        
    except Exception as e:
        results.append(TestResult(
            "Subagent definitions",
            False,
            f"Error: {str(e)}"
        ))
    
    return results


def test_skills() -> List[TestResult]:
    """Test skill definitions."""
    results = []
    
    try:
        skills_dir = PROJECT_ROOT / ".claude" / "skills"
        
        # Test 1: Required skills exist
        required_skills = [
            "code-execution",
            "architecture-planner",
            "shadcn-scaffolder",
            "competitor-analysis",
            "linear-integration",
        ]
        
        for skill in required_skills:
            skill_file = skills_dir / skill / "SKILL.md"
            if skill_file.exists():
                content = skill_file.read_text()
                # Check it's not just placeholder code
                if "Placeholder" in content or "# Placeholder" in content:
                    results.append(TestResult(
                        f"Skill '{skill}' is properly documented",
                        False,
                        "Contains placeholder code"
                    ))
                elif len(content) > 500:  # Should be substantial documentation
                    results.append(TestResult(
                        f"Skill '{skill}' is properly documented",
                        True
                    ))
                else:
                    results.append(TestResult(
                        f"Skill '{skill}' is properly documented",
                        False,
                        "Documentation too short"
                    ))
            else:
                results.append(TestResult(
                    f"Skill '{skill}' exists",
                    False,
                    f"File not found: {skill_file}"
                ))
        
    except Exception as e:
        results.append(TestResult(
            "Skill definitions",
            False,
            f"Error: {str(e)}"
        ))
    
    return results


def test_memory_paths() -> List[TestResult]:
    """Test memory path standardization."""
    results = []
    
    try:
        from src.utils.constants import (
            MEMORY_PRD_PATH,
            MEMORY_ARCHITECTURE_PLAN_PATH,
            MEMORY_QA_SUMMARY_PATH,
        )
        
        # Test 1: All paths use .sdlc/memories/ pattern
        paths = [
            MEMORY_PRD_PATH,
            MEMORY_ARCHITECTURE_PLAN_PATH,
            MEMORY_QA_SUMMARY_PATH,
        ]
        
        invalid_paths = [p for p in paths if not p.startswith(".sdlc/memories/")]
        
        if invalid_paths:
            results.append(TestResult(
                "Memory paths use standard .sdlc/memories/ pattern",
                False,
                f"Invalid paths: {', '.join(invalid_paths)}"
            ))
        else:
            results.append(TestResult(
                "Memory paths use standard .sdlc/memories/ pattern",
                True
            ))
        
        # Test 2: Session manager uses correct path
        from src.orchestrator.session_manager import ContextOrchestrator
        from src.orchestrator.registry import RepoRegistry
        from src.orchestrator.router import RepoRouter
        
        # This is a structural test - just verify the method exists
        if hasattr(ContextOrchestrator, "_ensure_memory_path"):
            results.append(TestResult(
                "Session manager has memory path method",
                True
            ))
        else:
            results.append(TestResult(
                "Session manager has memory path method",
                False
            ))
            
    except Exception as e:
        results.append(TestResult(
            "Memory path standardization",
            False,
            f"Error: {str(e)}"
        ))
    
    return results


def test_mcp_servers() -> List[TestResult]:
    """Test MCP server configuration."""
    results = []
    
    try:
        from config.agent_profiles import MCP_SERVER_CONFIGS
        
        # Test 1: Required MCP servers exist
        required_servers = ["code-ops", "infra-observe"]
        for server in required_servers:
            if server in MCP_SERVER_CONFIGS:
                results.append(TestResult(
                    f"MCP server '{server}' configured",
                    True
                ))
            else:
                results.append(TestResult(
                    f"MCP server '{server}' configured",
                    False
                ))
        
        # Test 2: Playwright MCP exists (optional but recommended)
        if "playwright" in MCP_SERVER_CONFIGS:
            results.append(TestResult(
                "Playwright MCP configured for visual feedback",
                True,
                "Enables screenshot-based verification"
            ))
        else:
            results.append(TestResult(
                "Playwright MCP configured for visual feedback",
                False,
                "Missing - recommended for visual feedback"
            ))
        
        # Test 3: CodeCraft uses Playwright
        from config.agent_profiles import get_agent_profile
        codecraft = get_agent_profile("codecraft")
        if "playwright" in codecraft.mcp_servers:
            results.append(TestResult(
                "CodeCraft uses Playwright MCP",
                True
            ))
        else:
            results.append(TestResult(
                "CodeCraft uses Playwright MCP",
                False
            ))
            
    except Exception as e:
        results.append(TestResult(
            "MCP server configuration",
            False,
            f"Error: {str(e)}"
        ))
    
    return results


def test_main_entry_point() -> List[TestResult]:
    """Test main.py entry point."""
    results = []
    
    try:
        main_file = PROJECT_ROOT / "main.py"
        
        if not main_file.exists():
            results.append(TestResult(
                "main.py exists",
                False
            ))
            return results
        
        results.append(TestResult(
            "main.py exists",
            True
        ))
        
        # Test 1: All agents are registered
        content = main_file.read_text()
        expected_agents = [
            "productspec", "archguard", "sprintmaster", "codecraft",
            "qualityguard", "docuscribe", "infraops", "sentinel",
            "sre-triage", "finops"
        ]
        
        missing_agents = [a for a in expected_agents if a not in content]
        
        if missing_agents:
            results.append(TestResult(
                "All agents registered in main.py",
                False,
                f"Missing: {', '.join(missing_agents)}"
            ))
        else:
            results.append(TestResult(
                "All agents registered in main.py",
                True
            ))
        
        # Test 2: Commands are defined
        required_commands = ["init", "agent", "dashboard", "orchestrate"]
        missing_commands = [c for c in required_commands if f'"{c}"' not in content and f"'{c}'" not in content]
        
        if missing_commands:
            results.append(TestResult(
                "All commands defined in main.py",
                False,
                f"Missing: {', '.join(missing_commands)}"
            ))
        else:
            results.append(TestResult(
                "All commands defined in main.py",
                True
            ))
            
    except Exception as e:
        results.append(TestResult(
            "Main entry point",
            False,
            f"Error: {str(e)}"
        ))
    
    return results


def run_all_tests() -> Tuple[int, int]:
    """Run all test suites and return (passed, total)."""
    all_results = []
    
    print("=" * 70)
    print("SDLC Agent Framework - Comprehensive Test Suite")
    print("=" * 70)
    print()
    
    test_suites = [
        ("Model Configuration", test_model_configuration),
        ("Agent Profiles", test_agent_profiles),
        ("Verification Hooks", test_verification_hooks),
        ("Subagent Definitions", test_subagents),
        ("Skill Definitions", test_skills),
        ("Memory Paths", test_memory_paths),
        ("MCP Servers", test_mcp_servers),
        ("Main Entry Point", test_main_entry_point),
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n📋 {suite_name}")
        print("-" * 70)
        results = test_func()
        all_results.extend(results)
        for result in results:
            print(result)
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for r in all_results if r.passed)
    total = len(all_results)
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print("\n❌ Failed Tests:")
        for result in all_results:
            if not result.passed:
                print(f"  - {result.name}: {result.message}")
    
    return passed, total


if __name__ == "__main__":
    passed, total = run_all_tests()
    sys.exit(0 if passed == total else 1)

