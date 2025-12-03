#!/usr/bin/env python3
"""
Test result reporter for Vertex AI agent tests.

Generates structured test reports in JSON and Markdown formats
with timestamps, test duration, pass/fail status, and detailed results.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / ".env")


class TestResultReporter:
    """Reporter for generating test result reports."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the reporter.
        
        Args:
            output_dir: Directory to store test results. Defaults to logs/test_results/
        """
        if output_dir is None:
            output_dir = project_root / "logs" / "test_results"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def start_test_suite(self):
        """Mark the start of a test suite."""
        self.start_time = datetime.now()
        self.test_results = []
    
    def add_test_result(self, test_name: str, success: bool, results: Dict[str, Any], 
                       duration: Optional[float] = None):
        """Add a test result to the report.
        
        Args:
            test_name: Name of the test
            success: Whether the test passed
            results: Detailed test results
            duration: Test duration in seconds
        """
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "duration": duration,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
    
    def end_test_suite(self):
        """Mark the end of a test suite."""
        self.end_time = datetime.now()
    
    def generate_report(self, suite_name: str = "vertex_ai_tests") -> tuple[Path, Path]:
        """Generate JSON and Markdown reports.
        
        Args:
            suite_name: Name of the test suite
            
        Returns:
            tuple: (json_path, markdown_path) - Paths to generated reports
        """
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.end_time is None:
            self.end_time = datetime.now()
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("success", False))
        failed_tests = total_tests - passed_tests
        
        # Get environment info
        env_info = {
            "CLAUDE_CODE_USE_VERTEX": os.getenv("CLAUDE_CODE_USE_VERTEX", "NOT SET"),
            "ANTHROPIC_VERTEX_PROJECT_ID": os.getenv("ANTHROPIC_VERTEX_PROJECT_ID", "NOT SET"),
            "CLOUD_ML_REGION": os.getenv("CLOUD_ML_REGION", "NOT SET"),
            "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "NOT SET"),
        }
        
        # Create report data
        report_data = {
            "suite_name": suite_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "environment": env_info,
            "test_results": self.test_results
        }
        
        # Generate timestamp for filename
        timestamp = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Generate JSON report
        json_path = self.output_dir / f"{timestamp}_{suite_name}_results.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate Markdown report
        markdown_path = self.output_dir / f"{timestamp}_{suite_name}_results.md"
        markdown_content = self._generate_markdown(report_data)
        with open(markdown_path, 'w') as f:
            f.write(markdown_content)
        
        return json_path, markdown_path
    
    def _generate_markdown(self, report_data: Dict[str, Any]) -> str:
        """Generate Markdown report content.
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            str: Markdown content
        """
        lines = []
        lines.append("# Vertex AI Agent Test Results")
        lines.append("")
        lines.append(f"**Test Suite:** {report_data['suite_name']}")
        lines.append(f"**Start Time:** {report_data['start_time']}")
        lines.append(f"**End Time:** {report_data['end_time']}")
        lines.append(f"**Duration:** {report_data['duration_seconds']:.2f} seconds")
        lines.append("")
        
        # Summary
        summary = report_data['summary']
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Tests:** {summary['total_tests']}")
        lines.append(f"- **Passed:** {summary['passed_tests']} ✓")
        lines.append(f"- **Failed:** {summary['failed_tests']} ✗")
        lines.append(f"- **Success Rate:** {summary['success_rate']:.1f}%")
        lines.append("")
        
        # Environment
        lines.append("## Environment Configuration")
        lines.append("")
        env = report_data['environment']
        for key, value in env.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")
        
        # Test Results
        lines.append("## Test Results")
        lines.append("")
        
        for i, test_result in enumerate(report_data['test_results'], 1):
            status = "✓ PASS" if test_result['success'] else "✗ FAIL"
            lines.append(f"### {i}. {test_result['test_name']} - {status}")
            lines.append("")
            
            if test_result.get('duration'):
                lines.append(f"**Duration:** {test_result['duration']:.2f} seconds")
                lines.append("")
            
            lines.append(f"**Timestamp:** {test_result['timestamp']}")
            lines.append("")
            
            # Add detailed results if available
            if test_result.get('results'):
                lines.append("**Details:**")
                lines.append("")
                self._add_results_to_markdown(test_result['results'], lines, indent=2)
                lines.append("")
        
        # Overall Status
        lines.append("## Overall Status")
        lines.append("")
        if summary['failed_tests'] == 0:
            lines.append("✅ **All tests passed!**")
        else:
            lines.append(f"❌ **{summary['failed_tests']} test(s) failed.**")
        lines.append("")
        
        return "\n".join(lines)
    
    def _add_results_to_markdown(self, results: Dict[str, Any], lines: List[str], indent: int = 0):
        """Recursively add results to markdown.
        
        Args:
            results: Results dictionary
            lines: List of markdown lines to append to
            indent: Indentation level
        """
        prefix = "  " * indent
        
        for key, value in results.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}- **{key}:**")
                self._add_results_to_markdown(value, lines, indent + 1)
            elif isinstance(value, list):
                lines.append(f"{prefix}- **{key}:** {len(value)} item(s)")
            elif isinstance(value, bool):
                status = "✓" if value else "✗"
                lines.append(f"{prefix}- **{key}:** {status}")
            else:
                lines.append(f"{prefix}- **{key}:** {value}")


def create_reporter(output_dir: Optional[Path] = None) -> TestResultReporter:
    """Create a test result reporter instance.
    
    Args:
        output_dir: Optional output directory
        
    Returns:
        TestResultReporter instance
    """
    return TestResultReporter(output_dir)


if __name__ == "__main__":
    # Example usage
    reporter = create_reporter()
    reporter.start_test_suite()
    
    # Add example test results
    reporter.add_test_result(
        "example_test",
        True,
        {"message": "Test passed successfully"},
        duration=1.5
    )
    
    reporter.end_test_suite()
    json_path, md_path = reporter.generate_report("example")
    
    print(f"Generated reports:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")

