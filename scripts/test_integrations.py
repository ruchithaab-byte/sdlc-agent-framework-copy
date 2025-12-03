#!/usr/bin/env python3
"""
Test script to verify all framework integrations are working.

Tests:
1. Vertex AI configuration
2. User email configuration
3. Service account credentials
4. Agent initialization
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config.agent_config import (
    get_user_email,
    get_google_cloud_credentials_path,
    PROJECT_ROOT,
    get_env,
)


def test_vertex_ai_config():
    """Test Vertex AI configuration."""
    print("=" * 60)
    print("1. Vertex AI Configuration")
    print("=" * 60)
    
    checks = {
        "CLAUDE_CODE_USE_VERTEX": get_env("CLAUDE_CODE_USE_VERTEX") == "1",
        "ANTHROPIC_VERTEX_PROJECT_ID": get_env("ANTHROPIC_VERTEX_PROJECT_ID"),
        "CLOUD_ML_REGION": get_env("CLOUD_ML_REGION"),
        "GOOGLE_APPLICATION_CREDENTIALS": get_env("GOOGLE_APPLICATION_CREDENTIALS"),
    }
    
    all_pass = True
    for key, value in checks.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value or 'Not set'}")
        if not value:
            all_pass = False
    
    # Check service account file
    sa_path = get_google_cloud_credentials_path()
    if sa_path and sa_path.exists():
        print(f"  ✓ Service Account File: {sa_path} ({sa_path.stat().st_size} bytes)")
    else:
        print(f"  ✗ Service Account File: Not found")
        all_pass = False
    
    print()
    return all_pass


def test_user_email():
    """Test user email configuration."""
    print("=" * 60)
    print("2. User Email Configuration")
    print("=" * 60)
    
    email = get_user_email()
    if email:
        print(f"  ✓ Email configured: {email}")
        
        # Check config file
        config_file = PROJECT_ROOT / ".claude" / "user_config.json"
        if config_file.exists():
            print(f"  ✓ Config file exists: {config_file}")
        else:
            print(f"  ⚠ Config file not found (using env var)")
        
        print()
        return True
    else:
        print(f"  ✗ Email not configured")
        print(f"  Run: python3 scripts/setup_user_email.py")
        print()
        return False


def test_agent_initialization():
    """Test that agents can be initialized."""
    print("=" * 60)
    print("3. Agent Initialization")
    print("=" * 60)
    
    try:
        from src.agents import (
            run_productspec_agent,
            run_archguard_agent,
            run_sprintmaster_agent,
            run_codecraft_agent,
            run_qualityguard_agent,
        )
        
        agents = {
            "ProductSpec": run_productspec_agent,
            "ArchGuard": run_archguard_agent,
            "SprintMaster": run_sprintmaster_agent,
            "CodeCraft": run_codecraft_agent,
            "QualityGuard": run_qualityguard_agent,
        }
        
        all_pass = True
        for name, agent_fn in agents.items():
            try:
                # Just check if function is callable
                if callable(agent_fn):
                    print(f"  ✓ {name} agent: Available")
                else:
                    print(f"  ✗ {name} agent: Not callable")
                    all_pass = False
            except Exception as e:
                print(f"  ✗ {name} agent: Error - {e}")
                all_pass = False
        
        print()
        return all_pass
    except ImportError as e:
        print(f"  ✗ Failed to import agents: {e}")
        print()
        return False


def test_orchestrator():
    """Test orchestrator configuration."""
    print("=" * 60)
    print("4. Orchestrator Configuration")
    print("=" * 60)
    
    try:
        from src.orchestrator.sdlc_orchestrator import SDLCOrchestrator
        
        orchestrator = SDLCOrchestrator()
        
        # Test option creation
        try:
            strategy_opts = orchestrator.strategy_options()
            print(f"  ✓ Strategy options: Created")
        except Exception as e:
            print(f"  ✗ Strategy options: Error - {e}")
            return False
        
        try:
            build_opts = orchestrator.build_options()
            print(f"  ✓ Build options: Created")
        except Exception as e:
            print(f"  ✗ Build options: Error - {e}")
            return False
        
        print()
        return True
    except Exception as e:
        print(f"  ✗ Orchestrator error: {e}")
        print()
        return False


def main():
    """Run all integration tests."""
    print()
    print("=" * 60)
    print("Framework Integration Tests")
    print("=" * 60)
    print()
    
    results = {
        "Vertex AI": test_vertex_ai_config(),
        "User Email": test_user_email(),
        "Agent Initialization": test_agent_initialization(),
        "Orchestrator": test_orchestrator(),
    }
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_pass = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_pass = False
    
    print()
    print("=" * 60)
    if all_pass:
        print("✓ All integration tests passed!")
        print("=" * 60)
        print()
        print("You can now run agents:")
        print("  python3 main.py agent productspec --requirements 'Your requirements'")
        return 0
    else:
        print("✗ Some integration tests failed")
        print("=" * 60)
        print()
        print("Please fix the issues above before running agents.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

