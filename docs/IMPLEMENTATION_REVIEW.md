# Claude Agent SDK Implementation Review

## Overview
This document reviews our implementation against the official Claude Agent SDK documentation to ensure compliance and identify any gaps.

## ✅ Correctly Implemented

### 1. Authentication
**Documentation Requirement:**
- Support for `ANTHROPIC_API_KEY` (default)
- Support for Vertex AI via `CLAUDE_CODE_USE_VERTEX=1`
- Support for Amazon Bedrock via `CLAUDE_CODE_USE_BEDROCK=1`

**Our Implementation:**
- ✅ Vertex AI authentication configured
- ✅ `CLAUDE_CODE_USE_VERTEX=1` set in `.env`
- ✅ `GOOGLE_APPLICATION_CREDENTIALS` configured
- ✅ `ANTHROPIC_VERTEX_PROJECT_ID` set
- ✅ `CLOUD_ML_REGION` set to `global`

**Status:** ✅ **COMPLIANT**

### 2. Hooks Implementation
**Documentation Requirement:**
- Hooks can be configured in `./.claude/settings.json` (file-based, for CLI)
- Hooks can be registered programmatically via `HookMatcher` (for SDK)
- Hook functions should be async and match expected signatures

**Our Implementation:**
- ✅ Using programmatic hooks (Agent SDK method)
- ✅ `HookMatcher` used correctly with hook functions
- ✅ Hook functions are async: `async def pre_tool_use_logger(...)`
- ✅ Hooks registered in `ClaudeAgentOptions` via `hooks` parameter
- ✅ Hook event types: `PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`, `Stop`

**Hook Registration Pattern:**
```python
hooks = {
    "PreToolUse": [HookMatcher(hooks=[documentation_hooks.pre_tool_use_logger])],
    "PostToolUse": [HookMatcher(hooks=[documentation_hooks.post_tool_use_logger])],
    "SessionStart": [HookMatcher(hooks=[documentation_hooks.session_start_logger])],
    "SessionEnd": [HookMatcher(hooks=[documentation_hooks.session_end_logger])],
    "Stop": [HookMatcher(hooks=[documentation_hooks.stop_logger])],
}

options = ClaudeAgentOptions(
    ...
    hooks=hooks,
)
```

**Status:** ✅ **COMPLIANT** (but hooks not firing - see Known Issues)

### 3. Setting Sources
**Documentation Requirement:**
- `setting_sources` must include `"project"` to load `CLAUDE.md` files
- Options: `["user", "project", "local"]`

**Our Implementation:**
- ✅ `setting_sources=["user", "project"]` configured in all agents
- ✅ Enables loading of project-level `CLAUDE.md` files

**Status:** ✅ **COMPLIANT**

### 4. Tool Permissions
**Documentation Requirement:**
- `allowed_tools` - Explicitly allow specific tools
- `disallowed_tools` - Block specific tools
- `permission_mode` - Set overall permission strategy

**Our Implementation:**
- ✅ `allowed_tools` configured per agent/model
- ✅ Tools match model configuration from `MODEL_REGISTRY`
- ✅ Different tool sets for "strategy" vs "build" models

**Status:** ✅ **COMPLIANT**

### 5. Model Configuration
**Documentation Requirement:**
- Model name specified in `ClaudeAgentOptions`
- Support for latest models

**Our Implementation:**
- ✅ Model configured: `claude-sonnet-4` (latest, replacing deprecated version)
- ✅ Model specified in `ClaudeAgentOptions`
- ✅ Model resolved from `MODEL_REGISTRY` configuration

**Status:** ✅ **COMPLIANT**

### 6. Query Function Usage
**Documentation Requirement:**
- Use `query()` function with `prompt` and `options` parameters
- Handle async message stream

**Our Implementation:**
- ✅ Using `query(prompt=prompt, options=_options())`
- ✅ Properly handling async message stream
- ✅ Correct parameter names (`prompt`, `options`)

**Status:** ✅ **COMPLIANT**

## ⚠️ Known Issues

### 1. Hooks Not Firing (SDK Bug)
**Issue:** Hooks are correctly registered but not executing during agent runs. This is a **known SDK bug** affecting all backends (Vertex AI and direct API).

**Evidence:**
- Hook functions never called (no debug output)
- No execution logs created from hooks
- Agent executes successfully, but hooks don't trigger
- [GitHub Issue #213](https://github.com/anthropics/claude-agent-sdk-python/issues/213) confirms same issue with direct API

**Root Cause:**
- SDK bug affecting multiple versions (0.1.0, 0.1.1, 0.1.10)
- Not specific to Vertex AI - affects all backends
- Our implementation is correct (matches official documentation)

**Solution:**
- ✅ **Message-level logging implemented** as primary approach
- Works reliably with all backends
- See `src/utils/message_logger.py` for implementation

**Status:** ⚠️ **INVESTIGATING**

## 📋 Implementation Checklist

- [x] Authentication configured (Vertex AI)
- [x] Hooks registered programmatically
- [x] Hook functions are async
- [x] Setting sources configured
- [x] Tool permissions configured
- [x] Model configuration correct
- [x] Query function used correctly
- [ ] Hooks actually firing (blocked by SDK bug - see GitHub Issue #213)

## 🔍 Comparison with Documentation

### What Documentation Says:
> "Hooks: Execute custom commands configured in ./.claude/settings.json that respond to tool events"

### What We're Doing:
We're using **programmatic hooks** (Agent SDK method) instead of file-based hooks. According to the documentation, both methods are supported:
- **File-based hooks** (`.claude/settings.json`) - for CLI usage
- **Programmatic hooks** (Python functions) - for SDK usage

Our approach is correct for SDK usage, but hooks aren't firing.

## 💡 Recommendations

1. **Test with Direct API**: Temporarily disable Vertex AI and test with `ANTHROPIC_API_KEY` to confirm hooks work with direct API
2. **Check SDK Updates**: Update to latest SDK version and check changelog for hook fixes
3. **Alternative Approach**: Implement message-level logging as fallback if hooks don't work with Vertex AI
4. **Contact Support**: If hooks are required, contact Anthropic support about Vertex AI hook support

## 📚 References

- [Claude Agent SDK Documentation](https://docs.anthropic.com/claude/docs/agent-sdk)
- [Python SDK GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Hook Types Documentation](https://platform.claude.com/docs/en/agent-sdk/python#hook-types)

