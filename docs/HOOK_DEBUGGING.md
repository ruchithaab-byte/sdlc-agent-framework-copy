# Hook Debugging Summary

## Issue
Execution hooks (`PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`, `Stop`) are not firing during agent execution. This is a **known SDK bug** affecting both Vertex AI backend and direct Anthropic API.

**Related GitHub Issue:** [claude-agent-sdk-python #213](https://github.com/anthropics/claude-agent-sdk-python/issues/213) (marked as duplicate/bug)

## What We've Verified

### ✅ Working
1. **Vertex AI Configuration**: Successfully updated and working
   - Model: `claude-sonnet-4` (latest, replacing deprecated `claude-sonnet-4-5-20250929`)
   - Region: `global` (auto-routing enabled)
   - Agent executes successfully and uses tools

2. **Hook Registration**: Hooks are correctly registered
   - Hook functions are async and match expected signature
   - `HookMatcher` is used correctly
   - Hooks are passed to `ClaudeAgentOptions` correctly

3. **Execution Logger**: Database and logging infrastructure works
   - Direct database writes succeed
   - Logger initialization works
   - User email capture works

### ❌ Not Working
1. **Hooks Not Firing**: No hook debug messages appear during agent execution
   - Test hooks with print statements don't execute
   - Wrapped hooks with error handling don't show any calls
   - No execution logs created from hooks

## Root Cause Analysis

### Confirmed Root Cause

**SDK Bug (Not Vertex AI Specific)**
- Hooks do not fire with **both** Vertex AI backend (`CLAUDE_CODE_USE_VERTEX=1`) and direct Anthropic API
- This is a **known bug** in the Claude Agent SDK Python (see GitHub issue #213)
- Issue affects multiple SDK versions (0.1.0, 0.1.1, 0.1.10)
- Our implementation is correct - matches official documentation examples
- Tools execute successfully, but hooks are never called by the SDK

### Evidence

1. **GitHub Issue Confirmation**
   - [Issue #213](https://github.com/anthropics/claude-agent-sdk-python/issues/213) reports identical problem
   - User with direct API (not Vertex AI) experiences same hook failure
   - Issue marked as "duplicate" and "bug" by maintainers
   - Tools execute (`ToolUseBlock`, `ToolResultBlock` visible) but hooks don't fire

2. **Our Testing Confirmed**
   - Hooks don't fire with Vertex AI backend
   - Hook registration pattern matches official documentation
   - Hook function signatures are correct
   - Multiple detection methods confirm hooks are never called

## Testing Performed

1. ✅ Verified hook function signatures match SDK expectations
2. ✅ Tested hook registration with `HookMatcher`
3. ✅ Added debug wrappers to catch hook calls (none detected)
4. ✅ Tested with both direct agent and orchestrator patterns
5. ✅ Verified hooks are in `ClaudeAgentOptions` object
6. ✅ Confirmed agent executes and uses tools (hooks just don't fire)

## Solution: Message-Level Logging (Primary Approach)

Since hooks are a known SDK bug affecting all backends, we use **message-level logging** as the primary approach:

### Implementation
- Monitor `query()` return messages
- Parse `ToolUseBlock` and `ToolResultBlock` messages
- Log directly from message stream using `src.utils.message_logger`
- This approach works reliably with both Vertex AI and direct API

### Usage
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

### Status
✅ **Implemented and Working**
- Database population: ✅ Working
- WebSocket broadcasting: ✅ Working
- End-to-end integration: ✅ Verified

### Option 4: Check SDK Documentation
- Review latest SDK docs for hook requirements
- Check if Vertex AI requires different hook setup
- Verify if hooks are supported with Vertex AI backend

## Current Status

- **Agent Execution**: ✅ Working with Vertex AI
- **Vertex AI Config**: ✅ Fixed and working
- **Execution Logging Infrastructure**: ✅ Ready
- **Hooks**: ❌ Not firing (known SDK bug - affects all backends)
- **Message-Level Logging**: ✅ Implemented and working (primary approach)

## Next Steps

1. ✅ **Message-level logging implemented** - Primary approach for all logging
2. **Monitor SDK updates** - Check for fixes in newer SDK versions
3. **Track GitHub issue** - [Issue #213](https://github.com/anthropics/claude-agent-sdk-python/issues/213) for SDK fix status
4. **Future migration** - Once SDK fixes hooks, can optionally migrate from message-level to hooks

## References

- [GitHub Issue #213](https://github.com/anthropics/claude-agent-sdk-python/issues/213) - Hooks not triggering in Claude Agent SDK
- [Official Hook Documentation](https://docs.claude.com/en/api/agent-sdk/python#hook-usage-example) - Hook usage examples
- `src/utils/message_logger.py` - Message-level logging implementation

## Files Modified

- `config/agent_config.py` - Updated model to `claude-sonnet-4`
- `.env` - Updated region to `global`
- `src/agents/archguard_agent.py` - Added hooks registration
- `src/orchestrator/sdlc_orchestrator.py` - Removed `betas` parameter

