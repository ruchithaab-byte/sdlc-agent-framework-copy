#!/usr/bin/env python3
"""
Test runner for all Vertex AI agent tests.

Orchestrates execution of all test scripts and generates consolidated reports.
Supports running individual test phases or the complete test suite.
"""

import argparse
import asyncio
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from scripts.test_result_reporter import TestResultReporter

# Load environment variables
load_dotenv(project_root / ".env")


def run_test_module(module_path: Path, test_function: str = None) -> tuple[bool, Dict[str, Any]]:
    """Run a test module and return results.
    
    Args:
        module_path: Path to the test module
        test_function: Name of the test function to run (if None, runs main)
        
    Returns:
        tuple: (success: bool, results: dict)
    """
    try:
        spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
        if spec is None or spec.loader is None:
            return False, {"error": "Could not load module"}
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_path.stem] = module
        spec.loader.exec_module(module)
        
        # Determine which function to run
        if test_function and hasattr(module, test_function):
            func = getattr(module, test_function)
        elif hasattr(module, "main"):
            func = getattr(module, "main")
        else:
            # Try to find async test function
            if hasattr(module, "test_all_tools"):
                func = getattr(module, "test_all_tools")
            elif hasattr(module, "test_all_integration"):
                func = getattr(module, "test_all_integration")
            elif hasattr(module, "test_all_advanced"):
                func = getattr(module, "test_all_advanced")
            else:
                return False, {"error": "No test function found"}
        
        # Run the function
        start_time = time.time()
        
        if asyncio.iscoroutinefunction(func):
            success, results = asyncio.run(func())
        else:
            result = func()
            if isinstance(result, tuple) and len(result) == 2:
                success, results = result
            elif isinstance(result, bool):
                success = result
                results = {}
            else:
                success = True
                results = {}
        
        duration = time.time() - start_time
        
        results["duration"] = duration
        return success, results
        
    except Exception as e:
        return False, {
            "error": str(e),
            "error_type": type(e).__name__
        }


def run_config_test() -> tuple[bool, Dict[str, Any]]:
    """Run configuration test."""
    print("\n" + "=" * 60)
    print("Phase 1: Configuration Validation")
    print("=" * 60)
    print()
    
    module_path = project_root / "scripts" / "test_vertex_ai_config.py"
    success, results = run_test_module(module_path, "check_vertex_ai_config")
    
    return success, results


def run_agent_test() -> tuple[bool, Dict[str, Any]]:
    """Run basic agent execution test."""
    print("\n" + "=" * 60)
    print("Phase 2: Basic Agent Execution")
    print("=" * 60)
    print()
    
    module_path = project_root / "scripts" / "test_vertex_ai_agent.py"
    success, results = run_test_module(module_path, "test_vertex_ai_agent")
    
    return success, results


def run_tools_test() -> tuple[bool, Dict[str, Any]]:
    """Run tool execution test."""
    print("\n" + "=" * 60)
    print("Phase 3: Tool Execution")
    print("=" * 60)
    print()
    
    module_path = project_root / "scripts" / "test_vertex_ai_tools.py"
    success, results = run_test_module(module_path, "test_all_tools")
    
    return success, results


def run_integration_test() -> tuple[bool, Dict[str, Any]]:
    """Run integration test."""
    print("\n" + "=" * 60)
    print("Phase 4: Integration Tests")
    print("=" * 60)
    print()
    
    module_path = project_root / "scripts" / "test_vertex_ai_integration.py"
    success, results = run_test_module(module_path, "test_all_integration")
    
    return success, results


def run_advanced_test() -> tuple[bool, Dict[str, Any]]:
    """Run advanced features test."""
    print("\n" + "=" * 60)
    print("Phase 5: Advanced Features")
    print("=" * 60)
    print()
    
    module_path = project_root / "scripts" / "test_vertex_ai_advanced.py"
    success, results = run_test_module(module_path, "test_all_advanced")
    
    return success, results


def run_database_websocket_test() -> tuple[bool, Dict[str, Any]]:
    """Run database and WebSocket integration test."""
    print("\n" + "=" * 60)
    print("Phase 6: Database and WebSocket Integration")
    print("=" * 60)
    print()
    
    module_path = project_root / "scripts" / "test_vertex_ai_database_websocket.py"
    success, results = run_test_module(module_path, "run_all_database_websocket_tests")
    
    return success, results


def run_all_tests(phases: Optional[List[str]] = None) -> tuple[bool, Dict[str, Any]]:
    """Run all test phases.
    
    Args:
        phases: List of phases to run. If None, runs all phases.
                Options: 'config', 'agent', 'tools', 'integration', 'advanced'
        
    Returns:
        tuple: (overall_success: bool, all_results: dict)
    """
    reporter = TestResultReporter()
    reporter.start_test_suite()
    
    all_results = {}
    
    # Define test phases
    test_phases = {
        "config": ("Configuration Validation", run_config_test),
        "agent": ("Basic Agent Execution", run_agent_test),
        "tools": ("Tool Execution", run_tools_test),
        "integration": ("Integration Tests", run_integration_test),
        "advanced": ("Advanced Features", run_advanced_test),
        "database_websocket": ("Database and WebSocket Integration", run_database_websocket_test),
    }
    
    # Determine which phases to run
    if phases is None:
        phases_to_run = list(test_phases.keys())
    else:
        phases_to_run = [p for p in phases if p in test_phases]
        if not phases_to_run:
            print(f"Error: No valid phases specified. Available: {', '.join(test_phases.keys())}")
            return False, {}
    
    print("\n" + "=" * 60)
    print("Vertex AI Agent Test Suite")
    print("=" * 60)
    print()
    
    # Check hook status
    try:
        hook_report_path = project_root / "logs" / "test_results"
        if hook_report_path.exists():
            hook_reports = list(hook_report_path.glob("hook_validation_*.json"))
            if hook_reports:
                latest_report = max(hook_reports, key=lambda p: p.stat().st_mtime)
                with open(latest_report) as f:
                    hook_report = json.load(f)
                    hooks_work = hook_report.get("hooks_work", False)
                    print(f"Hook Status: {'Working' if hooks_work else 'Not working (using message-level fallback)'}")
                    print()
    except Exception:
        pass
    
    print(f"Running phases: {', '.join(phases_to_run)}")
    print()
    
    # Run each phase
    for phase_name in phases_to_run:
        phase_title, phase_func = test_phases[phase_name]
        
        try:
            success, results = phase_func()
            all_results[phase_name] = {
                "success": success,
                "results": results
            }
            
            reporter.add_test_result(
                phase_title,
                success,
                results,
                duration=results.get("duration", 0)
            )
            
        except Exception as e:
            print(f"\n✗ Error running {phase_title}: {e}")
            all_results[phase_name] = {
                "success": False,
                "error": str(e)
            }
            
            reporter.add_test_result(
                phase_title,
                False,
                {"error": str(e)},
                duration=0
            )
    
    reporter.end_test_suite()
    
    # Generate reports
    json_path, md_path = reporter.generate_report("vertex_ai_test_suite")
    
    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)
    print()
    print(f"Reports generated:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    print()
    
    # Calculate overall success
    total_phases = len(phases_to_run)
    passed_phases = sum(1 for r in all_results.values() if r.get("success", False))
    
    overall_success = passed_phases == total_phases
    
    print(f"Summary: {passed_phases}/{total_phases} phases passed")
    print()
    
    if overall_success:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total_phases - passed_phases} phase(s) failed")
    
    return overall_success, all_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Vertex AI agent tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_all_vertex_ai_tests.py

  # Run specific phases
  python run_all_vertex_ai_tests.py --phases config agent

  # Run only configuration test
  python run_all_vertex_ai_tests.py --phases config
        """
    )
    
    parser.add_argument(
        "--phases",
        nargs="+",
        choices=["config", "agent", "tools", "integration", "advanced", "database_websocket"],
        help="Test phases to run (default: all)"
    )
    
    args = parser.parse_args()
    
    success, results = run_all_tests(args.phases)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

