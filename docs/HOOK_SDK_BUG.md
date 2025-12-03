# Hooks SDK Bug - Known Issue

## Summary

Execution hooks (`PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`, `Stop`) do not fire in the Claude Agent SDK Python. This is a **confirmed SDK bug** affecting all backends (Vertex AI and direct Anthropic API).

## GitHub Issue

**Issue:** [claude-agent-sdk-python #213](https://github.com/anthropics/claude-agent-sdk-python/issues/213)
- Status: Open, marked as "duplicate" and "bug"
- Reported: October 7, 2025
- Affected Versions: 0.1.0, 0.1.1, 0.1.10 (and likely others)

## Problem Description

### Symptoms
- Hooks are correctly registered using `HookMatcher`
- Hook function signatures match documentation
- Tools execute successfully (`ToolUseBlock`, `ToolResultBlock` visible)
- **Hooks never fire** - no hook function calls detected

### Affected Backends
- ✅ Vertex AI (`CLAUDE_CODE_USE_VERTEX=1`)
- ✅ Direct Anthropic API (`ANTHROPIC_API_KEY`)
- Likely affects all backends

## Our Implementation Status

### ✅ Correct Implementation
Our hook registration matches the official documentation:

```python
hooks = {
    "PreToolUse": [HookMatcher(hooks=[pre_tool_use_logger])],
    "PostToolUse": [HookMatcher(hooks=[post_tool_use_logger])],
    "SessionStart": [HookMatcher(hooks=[session_start_logger])],
    "SessionEnd": [HookMatcher(hooks=[session_end_logger])],
}

options = ClaudeAgentOptions(
    hooks=hooks,
    # ... other options
)
```

### ✅ Workaround: Message-Level Logging
Since hooks don't work, we use message-level logging as the primary approach:

```python
from src.utils.message_logger import log_agent_execution

message_stream = query(prompt=prompt, options=options)
await log_agent_execution(
    message_stream=message_stream,
    logger=logger,
    user_email=user_email,
    agent_name="ArchGuard",
    phase="strategy"
)
```

**Status:** ✅ Fully implemented and working
- Database population: ✅ Working
- WebSocket broadcasting: ✅ Working
- End-to-end integration: ✅ Verified

## Testing Performed

### Hook Detection Tests
- ✅ Multiple detection methods (file logging, global state, database writes)
- ✅ Hook wrappers with debug output
- ✅ Stream lifecycle monitoring
- ✅ Message-hook correlation analysis

**Result:** All tests confirm hooks are never called by the SDK.

### Stream Management Tests
- ✅ Stream lifecycle monitoring
- ✅ Stream keep-alive attempts
- ✅ SDK internal inspection
- ✅ Message timing correlation

**Result:** Stream management does not enable hooks - root cause is SDK bug, not stream lifecycle.

## Impact

### What Works
- ✅ Agent execution
- ✅ Tool execution
- ✅ Message stream parsing
- ✅ Database logging (via message-level logging)
- ✅ WebSocket broadcasting (via message-level logging)

### What Doesn't Work
- ❌ Hook execution (SDK bug)
- ❌ Hook-based permission control
- ❌ Hook-based logging (use message-level instead)

## Recommendations

1. **Use Message-Level Logging**
   - Primary approach for all execution logging
   - Works reliably with all backends
   - Already implemented in `src/utils/message_logger.py`

2. **Monitor SDK Updates**
   - Check for newer SDK versions with hook fixes
   - Track GitHub issue #213 for resolution status

3. **Future Migration Path**
   - Once SDK fixes hooks, can optionally migrate from message-level to hooks
   - Message-level logging will remain as fallback

## References

- [GitHub Issue #213](https://github.com/anthropics/claude-agent-sdk-python/issues/213) - Hooks not triggering
- [Official Hook Documentation](https://docs.claude.com/en/api/agent-sdk/python#hook-usage-example)
- `src/utils/message_logger.py` - Message-level logging implementation
- `docs/HOOK_DEBUGGING.md` - Detailed debugging summary
- `scripts/test_vertex_ai_hook_detection.py` - Hook detection tests
- `scripts/test_vertex_ai_stream_management.py` - Stream management tests


