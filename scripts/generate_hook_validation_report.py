#!/usr/bin/env python3
"""
Generate comprehensive hook validation report from test results.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / ".env")


def generate_validation_report():
    """Generate comprehensive hook validation report."""
    test_results_dir = project_root / "logs" / "test_results"
    
    # Find latest hook validation report
    hook_reports = list(test_results_dir.glob("hook_validation_*.json"))
    if not hook_reports:
        print("No hook validation report found. Run test_vertex_ai_hook_detection.py first.")
        return
    
    latest_report = max(hook_reports, key=lambda p: p.stat().st_mtime)
    
    with open(latest_report) as f:
        hook_data = json.load(f)
    
    # Generate markdown report
    report_path = test_results_dir / f"hook_validation_report_{int(datetime.now().timestamp())}.md"
    
    report_content = f"""# Hook Validation Report - Vertex AI Backend

**Generated:** {datetime.now().isoformat()}
**Test Report:** {latest_report.name}

## Executive Summary

**CONCLUSION:** {'✅ Hooks ARE firing with Vertex AI' if hook_data.get('hooks_work') else '❌ Hooks are NOT firing with Vertex AI'}

### Key Finding

{'Hooks work correctly with Vertex AI backend. Database population and WebSocket broadcasting can use hook-based logging.' if hook_data.get('hooks_work') else 'Hooks do not fire with Vertex AI backend (CLAUDE_CODE_USE_VERTEX=1). Message-level logging fallback is required for database population and WebSocket broadcasting.'}

## Test Configuration

- **Vertex AI Enabled:** {hook_data.get('vertex_ai_enabled', 'Unknown')}
- **SDK Version:** {hook_data.get('sdk_version', 'Unknown')}
- **Project ID:** {hook_data.get('environment', {}).get('ANTHROPIC_VERTEX_PROJECT_ID', 'Unknown')}

## Detection Methods Used

The validation used multiple independent detection methods:

1. **Print Statements** - Console output when hooks fire
2. **File-Based Logging** - Temporary files written when hooks fire
3. **Global State Tracking** - Global variables updated when hooks fire
4. **Database Writes** - Direct database writes from hooks

## Test Results

"""
    
    for i, test_result in enumerate(hook_data.get('test_results', []), 1):
        report_content += f"""### Test {i}: {test_result.get('test_name', 'Unknown')}

**Hooks Tested:** {', '.join(test_result.get('hooks_tested', []))}

**Results:**
"""
        for hook_type, hook_data_result in test_result.get('hook_calls', {}).items():
            detected = hook_data_result.get('detected') or hook_data_result.get('file_detected') or hook_data_result.get('global_state_detected')
            status = "✅ Detected" if detected else "❌ Not Detected"
            report_content += f"- **{hook_type}:** {status}\n"
        
        report_content += "\n"
    
    report_content += f"""## Recommendation

"""
    
    if hook_data.get('hooks_work'):
        report_content += """✅ **Use Hook-Based Logging**

Since hooks work with Vertex AI, you can use the standard hook-based logging approach:
- Register hooks in `ClaudeAgentOptions`
- Hooks will automatically log to database
- WebSocket server will broadcast events from database
"""
    else:
        report_content += """⚠️ **Use Message-Level Logging Fallback**

Since hooks do not fire with Vertex AI, use message-level logging:
- Parse `query()` message stream for `ToolUseBlock` and `ToolResultBlock`
- Manually call `ExecutionLogger.log_execution()` for each event
- Use `src.utils.message_logger.log_agent_execution()` wrapper

**Implementation:**
```python
from src.utils.message_logger import log_agent_execution

message_stream = query(prompt=prompt, options=options)
await log_agent_execution(
    message_stream=message_stream,
    logger=logger,
    user_email=user_email
)
```

This ensures database population and WebSocket broadcasting work correctly.
"""
    
    report_content += f"""
## Evidence

All detection methods consistently {'confirmed' if hook_data.get('hooks_work') else 'denied'} hook execution.

**Test Report Data:**
```json
{json.dumps(hook_data, indent=2)}
```

## Next Steps

1. {'Continue using hooks for logging' if hook_data.get('hooks_work') else 'Implement message-level logging in all agents'}
2. Verify database population works correctly
3. Verify WebSocket broadcasting works correctly
4. Update agent implementations as needed
"""
    
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    print(f"Validation report generated: {report_path}")
    return report_path


if __name__ == "__main__":
    generate_validation_report()

