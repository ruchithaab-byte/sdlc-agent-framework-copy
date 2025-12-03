# Live Integration Test Guide

## Overview

This guide walks through testing the **Tool Bridge** - the critical integration point between the Context Orchestrator and the Claude Agent SDK.

## Prerequisites

### 1. Environment Setup

Ensure your `.env` file contains:

```bash
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...  # Must have 'repo' scope
```

### 2. Sandbox Repository

The sandbox repository has been added to `config/repo_registry.yaml`:

```yaml
- id: sandbox
  description: A temporary playground repository for testing...
  github_url: https://github.com/your-username/test-sandbox
  local_path: ./repos/sandbox
  branch: main
```

The local directory `repos/sandbox/` has been created with a `README.md` file.

## Running the Integration Test

### Step 1: Basic Session Test (No Agent Execution)

Test that session preparation works:

```bash
python main.py orchestrate --repo-id sandbox "test"
```

**Expected Output:**
- ✅ Session prepared successfully
- Repository: sandbox
- Tools Available: 4 (if GITHUB_TOKEN is set) or 0 (if not set)

### Step 2: Full Integration Test (With Agent Execution)

Run the comprehensive integration test:

```bash
python test_tool_integration.py --repo-id sandbox
```

**What This Test Does:**

1. **Environment Check**: Verifies API keys are set
2. **Session Preparation**: Creates session context with tools
3. **Agent Options**: Builds `ClaudeAgentOptions` with session context
4. **Agent Execution**: Runs agent with test prompt
5. **Tool Verification**: Checks if tools were actually executed

**Success Criteria:**

✅ Agent executes without errors  
✅ Tool calls are detected in output  
✅ Agent can read files via GitHub tools  
✅ Tool bridge is functional

### Step 3: Custom Prompt Test

Test with a specific prompt:

```bash
python test_tool_integration.py --repo-id sandbox --prompt "Read README.md and summarize it"
```

## Understanding Tool Integration

### Current Architecture

The Context Orchestrator prepares:
- `session.tools`: List of async callables from `GitHubMCPServer.get_tools()`
- `session.agent_config`: Dict with `allowed_tools`, `model`, etc.

### SDK Integration Challenge

The Claude Agent SDK uses:
- `allowed_tools`: List of tool names (strings) like `["Read", "Write", "Bash"]`
- `mcp_servers`: Dict for registering MCP servers with custom tools

**Key Question**: How do we pass our async callable tools to the SDK?

### Possible Solutions

#### Option 1: MCP Server Registration

Register GitHub tools as an MCP server:

```python
agent_options = ClaudeAgentOptions(
    mcp_servers={
        "github": {
            # MCP server configuration
        }
    }
)
```

#### Option 2: Tool Name Mapping

Map GitHub tool callables to tool names that the SDK recognizes:

```python
# If SDK supports custom tool registration
agent_options.allowed_tools.extend(["get_file_contents", "create_branch", ...])
```

#### Option 3: Direct Tool Injection

If SDK supports it, inject tools directly (may require SDK update):

```python
# Hypothetical - needs SDK support
agent_options.tools = session.tools
```

## Diagnostic Output

The test script provides detailed diagnostics:

- **Environment Status**: API keys present/absent
- **Session Context**: Repository, paths, tools available
- **Agent Options**: Model, allowed_tools, cwd
- **Execution Log**: Tool calls and agent responses
- **Success Criteria**: Pass/fail indicators

## Troubleshooting

### Issue: "No tool calls detected"

**Possible Causes:**
1. Tools not properly registered with SDK
2. SDK requires MCP server registration
3. Tools need to be exposed differently

**Solutions:**
1. Check if SDK supports direct tool injection
2. Implement MCP server registration
3. Review SDK documentation for custom tool patterns

### Issue: "GITHUB_TOKEN not found"

**Solution:**
- Set `GITHUB_TOKEN` in `.env` file
- Verify token has `repo` scope
- Test token with: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`

### Issue: "ANTHROPIC_API_KEY not found"

**Solution:**
- Set `ANTHROPIC_API_KEY` in `.env` file
- Verify key is valid
- Check key format: `sk-ant-...`

## Next Steps After Test

### If Test Passes (Tools Execute)

✅ **Tool Bridge is Working!**
- Context Orchestrator is production-ready
- GitHub tools are functional
- Agent SDK integration is complete

### If Test Partially Passes (Agent Runs, No Tools)

⚠️ **Tool Registration Needed**
- Implement MCP server registration
- Or find SDK-supported method for custom tools
- Update `session_manager.py` to register tools properly

### If Test Fails (Agent Errors)

❌ **Integration Issue**
- Check SDK version compatibility
- Review error messages
- Verify agent options are correctly formatted

## Expected Test Output

### Successful Test Output

```
🔬 LIVE INTEGRATION TEST: Tool Bridge Verification
================================================================================

📋 Step 1: Environment Check
--------------------------------------------------------------------------------
✅ ANTHROPIC_API_KEY: ********************...xyz1
✅ GITHUB_TOKEN: ********************...abc2
   GitHub tools will be available

📋 Step 2: Prepare Session Context
--------------------------------------------------------------------------------
✅ Session prepared for repository: sandbox
   Memory Path: /path/to/memories/sandbox
   Working Directory: /path/to/repos/sandbox
   Tools Available: 4

   📧 GitHub Tools:
      1. get_file_contents
      2. create_branch
      3. create_commit
      4. create_pull_request

📋 Step 3: Create Agent Options with Tools
--------------------------------------------------------------------------------
   ✅ Agent options created
      Model: claude-opus-4@20250514
      Allowed Tools: ['Skill', 'Read', 'Write', 'Bash', 'memory']

📋 Step 4: Execute Agent with Tool Test
--------------------------------------------------------------------------------
   🚀 Starting agent execution...
   ----------------------------------------------------------------------------

   🔧 [TOOL CALL] get_file_contents(path='README.md', branch='main')
   💬 [AGENT] The README.md file contains...

📋 Step 5: Verify Tool Execution
--------------------------------------------------------------------------------
   ✅ Tool calls detected: 1
      1. get_file_contents(path='README.md', branch='main')

   ✅ Agent responses received: 1

📋 Step 6: Success Criteria Check
--------------------------------------------------------------------------------
   ✅ SUCCESS: Tools were executed by agent
   ✅ Tool Bridge is WORKING

================================================================================
🎉 INTEGRATION TEST: PASSED
================================================================================

✅ Tool Bridge is fully functional!
✅ Agent SDK accepts and executes tools from Context Orchestrator
✅ GitHub tools are working correctly
```

## Conclusion

This integration test validates the most critical part of the Context Orchestrator: **The Tool Bridge**. If this test passes, the entire system is production-ready and can route prompts to repositories, prepare sessions, and execute GitHub operations via the Agent SDK.

