# Vertex AI Agent Testing Guide

This guide provides comprehensive instructions for testing Vertex AI API-based Agent execution using the Claude Agent SDK.

## Overview

The Vertex AI testing suite validates that the Claude Agent SDK correctly routes through Google Cloud Vertex AI endpoints and that all agent functionality works as expected.

## Test Suite Structure

The test suite is organized into five phases:

1. **Configuration Validation** - Verifies environment setup and credentials
2. **Basic Agent Execution** - Tests simple agent queries
3. **Tool Execution** - Tests agent tool usage (Read, Write, etc.)
4. **Integration Tests** - Tests multi-step workflows and context management
5. **Advanced Features** - Tests memory, MCP, and system prompts (optional)

## Prerequisites

Before running tests, ensure:

1. **Environment Variables** are set in `.env`:
   ```bash
   CLAUDE_CODE_USE_VERTEX=1
   ANTHROPIC_VERTEX_PROJECT_ID=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   CLOUD_ML_REGION=global  # Optional, defaults to global
   ```

2. **Google Cloud Setup**:
   - Vertex AI API is enabled
   - Service account has `roles/aiplatform.user` role
   - Billing is enabled for the project

3. **Python Dependencies**:
   ```bash
   pip install claude-agent-sdk google-cloud-aiplatform python-dotenv
   ```

## Running Tests

### Run All Tests

Execute the complete test suite:

```bash
cd sdlc-agent-framework
python scripts/run_all_vertex_ai_tests.py
```

This will:
- Run all test phases in sequence
- Generate timestamped test reports in `logs/test_results/`
- Exit with code 0 if all tests pass, 1 if any fail

### Run Specific Test Phases

Run only selected phases:

```bash
# Run only configuration and basic agent tests
python scripts/run_all_vertex_ai_tests.py --phases config agent

# Run only configuration test
python scripts/run_all_vertex_ai_tests.py --phases config
```

Available phases:
- `config` - Configuration validation
- `agent` - Basic agent execution
- `tools` - Tool execution tests
- `integration` - Integration tests
- `advanced` - Advanced features tests

### Run Individual Test Scripts

You can also run individual test scripts directly:

```bash
# Configuration test
python scripts/test_vertex_ai_config.py

# Basic agent test
python scripts/test_vertex_ai_agent.py

# Tool execution tests
python scripts/test_vertex_ai_tools.py

# Integration tests
python scripts/test_vertex_ai_integration.py

# Advanced features tests
python scripts/test_vertex_ai_advanced.py
```

## Test Phases

### Phase 1: Configuration Validation

**Script:** `test_vertex_ai_config.py`

**What it tests:**
- Environment variables are set correctly
- Google Cloud credentials file exists and is valid
- Vertex AI API is accessible
- Service account has proper permissions

**Expected output:**
```
✓ Vertex AI is enabled
✓ Project ID: agents-with-claude
✓ Credentials file found
✓ Vertex AI initialized successfully
```

**Troubleshooting:**
- If credentials not found: Check `GOOGLE_APPLICATION_CREDENTIALS` path
- If API not enabled: Enable Vertex AI API in Google Cloud Console
- If permission denied: Grant `roles/aiplatform.user` to service account

### Phase 2: Basic Agent Execution

**Script:** `test_vertex_ai_agent.py`

**What it tests:**
- Agent can receive and process queries
- Agent returns responses via Vertex AI
- Message streaming works correctly
- Timeout handling works

**Expected output:**
```
✓ Successfully received message(s) from agent
✓ Received content messages
✓ Vertex AI configuration appears to be working
```

**Troubleshooting:**
- If no messages received: Check Vertex AI API status and billing
- If timeout: Increase timeout value or check network connectivity
- If authentication error: Verify service account credentials

### Phase 3: Tool Execution

**Script:** `test_vertex_ai_tools.py`

**What it tests:**
- Agent can use Read tool
- Agent can use Write tool
- Tool permissions work correctly (allowed/disallowed tools)
- Tool results are processed correctly

**Expected output:**
```
✓ Read tool was used
✓ Tool result was received
✓ Write tool was correctly blocked
```

**Troubleshooting:**
- If tools not detected: Check `allowed_tools` configuration
- If tool execution fails: Verify tool permissions in agent options
- If file operations fail: Check file system permissions

### Phase 4: Integration Tests

**Script:** `test_vertex_ai_integration.py`

**What it tests:**
- Multi-step workflows requiring multiple tool calls
- Context management across interactions
- Context compaction with longer conversations
- End-to-end agent workflows

**Expected output:**
```
✓ Multi-step workflow completed successfully
✓ Context was remembered across interactions
✓ Completed all interactions successfully
```

**Troubleshooting:**
- If context not maintained: This may be expected with Vertex AI (see limitations)
- If workflow fails: Check individual tool execution first
- If timeout: Increase timeout for complex workflows

### Phase 5: Advanced Features

**Script:** `test_vertex_ai_advanced.py`

**What it tests:**
- Memory/CLAUDE.md loading (if configured)
- MCP integration (if configured)
- System prompts and agent configuration
- Documents known hook limitations

**Expected output:**
```
✓ Memory/CLAUDE.md appears to be loaded
✓ MCP integration appears to be working
✓ System prompts appear to be applied
```

**Note:** Some features may not be fully supported with Vertex AI backend. See limitations section.

## Test Reports

Test reports are automatically generated in `logs/test_results/` with timestamps:

- **JSON format:** `YYYY-MM-DD_HH-MM-SS_vertex_ai_test_suite_results.json`
- **Markdown format:** `YYYY-MM-DD_HH-MM-SS_vertex_ai_test_suite_results.md`

### Report Contents

Reports include:
- Test suite summary (total tests, passed, failed, success rate)
- Environment configuration
- Individual test results with durations
- Detailed test output and errors
- Timestamps for each test

### Example Report Structure

```markdown
# Vertex AI Agent Test Results

**Test Suite:** vertex_ai_test_suite
**Start Time:** 2025-01-15T10:30:00
**Duration:** 45.23 seconds

## Summary
- **Total Tests:** 5
- **Passed:** 5 ✓
- **Failed:** 0 ✗
- **Success Rate:** 100.0%

## Test Results
### 1. Configuration Validation - ✓ PASS
### 2. Basic Agent Execution - ✓ PASS
...
```

## Expected Test Output

### Successful Test Run

```
============================================================
Vertex AI Agent Test Suite
============================================================

Running phases: config, agent, tools, integration, advanced

============================================================
Phase 1: Configuration Validation
============================================================
✓ Vertex AI is enabled
✓ Project ID configured
✓ Credentials file found and valid
✓ Vertex AI initialized successfully

============================================================
Phase 2: Basic Agent Execution
============================================================
✓ Successfully received message(s) from agent
✓ Received content messages
✓ Vertex AI configuration appears to be working

...

============================================================
Test Suite Complete
============================================================

Reports generated:
  JSON: logs/test_results/2025-01-15_10-30-00_vertex_ai_test_suite_results.json
  Markdown: logs/test_results/2025-01-15_10-30-00_vertex_ai_test_suite_results.md

Summary: 5/5 phases passed

✅ All tests passed!
```

## Troubleshooting

### Common Issues

#### 1. Configuration Errors

**Problem:** `CLAUDE_CODE_USE_VERTEX is not set to 1`

**Solution:**
```bash
# In .env file
CLAUDE_CODE_USE_VERTEX=1
```

#### 2. Credentials Not Found

**Problem:** `Credentials file not found`

**Solution:**
- Verify `GOOGLE_APPLICATION_CREDENTIALS` points to valid service account JSON
- Or place credentials at: `config/credentials/google-service-account.json`

#### 3. Permission Denied

**Problem:** `PERMISSION_DENIED` or `403` error

**Solution:**
```bash
# Grant Vertex AI User role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

#### 4. API Not Enabled

**Problem:** `Vertex AI API may not be enabled`

**Solution:**
```bash
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
```

#### 5. Billing Not Enabled

**Problem:** Billing-related errors

**Solution:**
- Enable billing for your GCP project in Google Cloud Console
- Vertex AI requires an active billing account

#### 6. Timeout Errors

**Problem:** Tests timeout before completion

**Solution:**
- Increase timeout values in test scripts
- Check network connectivity to Vertex AI endpoints
- Verify API quotas are not exceeded

#### 7. Tool Execution Fails

**Problem:** Tools not working or not detected

**Solution:**
- Verify `allowed_tools` in agent options
- Check file system permissions for Read/Write operations
- Ensure tools are included in SDK version

## Known Limitations

### Hooks Not Supported (SDK Bug)

**Issue:** Execution hooks (PreToolUse, PostToolUse, SessionStart, SessionEnd) may not fire when using Vertex AI backend.

**Solution:**
- ✅ **Message-level logging implemented** - Primary approach for all logging
- Works reliably with Vertex AI and all backends
- See `src/utils/message_logger.py` for implementation
- Monitor `query()` return messages for ToolUseBlock and ToolResultBlock

**Note:** This is a known SDK bug affecting all backends (not just Vertex AI). See [GitHub Issue #213](https://github.com/anthropics/claude-agent-sdk-python/issues/213).

For details, see: `docs/HOOK_DEBUGGING.md` and `docs/HOOK_SDK_BUG.md`

### Context Management

**Issue:** Context retention across multiple interactions may work differently with Vertex AI.

**Note:** This is informational, not necessarily a failure. Context management behavior may vary between backends.

## Test Execution Order

Recommended test execution order:

1. **Configuration Test** (fastest, catches setup issues early)
2. **Basic Agent Test** (verifies core functionality)
3. **Tool Execution Test** (confirms tool integration)
4. **Integration Test** (validates complete workflows)
5. **Advanced Features Test** (optional, tests additional features)

## CI/CD Integration

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run Vertex AI Tests
  run: |
    cd sdlc-agent-framework
    python scripts/run_all_vertex_ai_tests.py
  env:
    CLAUDE_CODE_USE_VERTEX: 1
    ANTHROPIC_VERTEX_PROJECT_ID: ${{ secrets.VERTEX_PROJECT_ID }}
    GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_CREDENTIALS }}
```

Exit codes:
- `0` - All tests passed
- `1` - One or more tests failed

## Best Practices

1. **Run configuration test first** - Catches setup issues early
2. **Check test reports** - Review generated reports for detailed results
3. **Run tests regularly** - Catch regressions early
4. **Monitor test duration** - Long-running tests may indicate issues
5. **Keep credentials secure** - Never commit service account keys
6. **Use appropriate timeouts** - Balance between catching issues and avoiding false timeouts

## Additional Resources

- **Vertex AI Setup:** `docs/VERTEX_AI_SETUP.md`
- **Hook Debugging:** `docs/HOOK_DEBUGGING.md`
- **Architecture:** `docs/ARCHITECTURE_QUICK_REFERENCE.md`
- **Claude Agent SDK Docs:** https://docs.anthropic.com/claude/docs/agent-sdk

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test reports for detailed error messages
3. Consult Vertex AI and Claude Agent SDK documentation
4. Check GitHub issues for known problems

