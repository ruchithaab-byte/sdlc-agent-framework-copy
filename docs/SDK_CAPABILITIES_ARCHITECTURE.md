# SDK Capabilities Architecture

A comprehensive guide to the Claude Agent SDK integration in the SDLC Agent Framework.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Core Components](#core-components)
4. [Configuration](#configuration)
5. [Usage Guide](#usage-guide)
6. [SDK Capabilities Reference](#sdk-capabilities-reference)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The SDLC Agent Framework integrates with the Claude Agent SDK to provide:

| Capability | Description | SDK Feature |
|------------|-------------|-------------|
| **Centralized Configuration** | Single source of truth for all 10 agents | `ClaudeAgentOptions` |
| **Structured Outputs** | Type-safe JSON responses with Pydantic | `output_format` |
| **Cost Tracking** | Token usage and budget enforcement | `usage`, `total_cost_usd` |
| **System Prompts** | Agent personas with repo context | `system_prompt` |
| **Hooks** | All 6 supported Python SDK hooks | `hooks` |
| **Session Management** | Resume and fork sessions | `resume`, `fork_session` |

### Python SDK Supported Hooks

```python
# ✅ SUPPORTED in Python SDK
"PreToolUse"       # Before tool execution
"PostToolUse"      # After tool execution
"UserPromptSubmit" # When user submits prompt
"Stop"             # When agent stops
"SubagentStop"     # When subagent completes
"PreCompact"       # Before context compaction

# ❌ NOT SUPPORTED in Python SDK
"SessionStart"     # Do NOT use
"SessionEnd"       # Do NOT use
"Notification"     # Do NOT use
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SDLC Agent Framework                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐ │
│  │  Agent Profiles  │────▶│  Options Builder │────▶│  Claude SDK      │ │
│  │  (config/)       │     │  (src/agents/)   │     │  Client          │ │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘ │
│          │                        │                        │            │
│          │                        │                        │            │
│          ▼                        ▼                        ▼            │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐ │
│  │  Model Registry  │     │  Hooks Builder   │     │  Agent Runner    │ │
│  │  (agent_config)  │     │  (src/hooks/)    │     │  (runner.py)     │ │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘ │
│                                   │                        │            │
│                                   │                        │            │
│                                   ▼                        ▼            │
│                           ┌──────────────────┐     ┌──────────────────┐ │
│                           │  Cost Tracker    │     │  Agent Result    │ │
│                           │  (cost_tracker)  │     │  (dataclass)     │ │
│                           └──────────────────┘     └──────────────────┘ │
│                                                            │            │
│  ┌──────────────────┐     ┌──────────────────┐            │            │
│  │  System Prompts  │     │  Output Schemas  │◀───────────┘            │
│  │  (prompts/)      │     │  (src/schemas/)  │                         │
│  └──────────────────┘     └──────────────────┘                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Agent Profiles (`config/agent_profiles.py`)

Centralized configuration for all 10 SDLC agents.

```python
from config.agent_profiles import AGENT_PROFILES, get_agent_profile

# Get a specific profile
profile = get_agent_profile("codecraft")

# Profile attributes
profile.model_profile      # "build" or "strategy"
profile.max_turns          # Prevents infinite loops
profile.permission_mode    # "default", "acceptEdits", etc.
profile.output_schema      # Schema name from SCHEMA_REGISTRY
profile.system_prompt_file # Prompt file from prompts/agents/
profile.hooks_profile      # "default", "build", "security"
profile.budget_usd         # Cost limit for budget enforcement
profile.mcp_servers        # MCP server configurations
profile.extra_allowed_tools # Additional tools beyond model defaults
```

### 2. Options Builder (`src/agents/options_builder.py`)

Single source of truth for building `ClaudeAgentOptions`.

```python
from src.agents.options_builder import build_agent_options

# Build options with all SDK capabilities
options, cost_tracker = build_agent_options(
    agent_id="codecraft",
    resume="session-123",           # Resume previous session
    permission_mode_override=None,  # Override profile setting
    extra_allowed_tools=["WebSearch"],
    cwd_override="/custom/path",
    session_id="my-session",        # For cost tracking
    repo_name="auth-service",       # For system prompt context
    repo_branch="feature/oauth",
)
```

### 3. Agent Runner (`src/agents/runner.py`)

Standardized execution with result aggregation.

```python
from src.agents.runner import run_agent, run_agent_streaming, AgentResult

# Standard execution
result: AgentResult = await run_agent(
    agent_id="codecraft",
    prompt="Build the authentication module",
    on_message=lambda m: print(m),
    collect_messages=True,
)

# Streaming execution
async for message in run_agent_streaming("productspec", requirements):
    yield message

# Multi-turn conversation
result = await run_agent_with_continuation(
    "codecraft",
    ["Analyze the code", "Implement the fix", "Add tests"],
)
```

### 4. Agent Result (`AgentResult`)

```python
@dataclass
class AgentResult:
    session_id: Optional[str]           # For session resumption
    structured_output: Optional[BaseModel]  # Validated Pydantic model
    raw_output: Optional[Dict]          # Raw JSON before validation
    cost_usd: float                     # Total cost (actual or estimated)
    cost_summary: Optional[CostSummary] # Full token breakdown
    budget_exceeded: bool               # True if over budget
    messages: List[Any]                 # Collected messages
    error: Optional[str]                # Error message if failed
```

---

## Configuration

### Agent Profiles Reference

| Agent | Model | Max Turns | Schema | Prompt | Budget |
|-------|-------|-----------|--------|--------|--------|
| `codecraft` | build | 100 | `code_craft` | `codecraft` | $5.00 |
| `qualityguard` | strategy | 75 | `quality_review` | `qualityguard` | $3.00 |
| `sentinel` | strategy | 75 | `security_scan` | `sentinel` | $3.00 |
| `sre-triage` | strategy | 100 | `incident_triage` | `sre_triage` | $2.00 |
| `sprintmaster` | strategy | 50 | `sprint_plan` | - | $1.50 |
| `archguard` | strategy | 50 | `architecture_review` | - | $2.00 |
| `finops` | strategy | 50 | `cost_analysis` | - | $1.50 |
| `infraops` | build | 75 | - | - | $5.00 |
| `docuscribe` | strategy | 50 | - | - | $2.00 |
| `productspec` | strategy | 50 | - | - | $2.00 |

### Hooks Profiles

```python
HOOKS_PROFILES = {
    "default": {
        "pre_tool_use": True,
        "post_tool_use": True,
        "user_prompt_submit": True,
        "stop": True,
        "subagent_stop": True,
        "pre_compact": True,
    },
    "build": { ... },      # Full observability for code agents
    "security": { ... },   # Extra validation for Sentinel
    "minimal": { ... },    # Lightweight for simple operations
}
```

### Output Schemas Reference

| Schema Name | Agent | Key Fields |
|-------------|-------|------------|
| `quality_review` | QualityGuard | `overall_score`, `issues`, `test_coverage`, `quality_gates` |
| `sprint_plan` | SprintMaster | `sprint_goals`, `work_items`, `team_capacity`, `risks` |
| `code_craft` | CodeCraft | `files_changed`, `implementations`, `tests_run`, `skills_applied` |
| `architecture_review` | ArchGuard | `architecture_score`, `violations`, `technical_debt` |
| `security_scan` | Sentinel | `security_score`, `vulnerabilities`, `secrets_found` |
| `incident_triage` | SRE-Triage | `timeline`, `root_cause_hypotheses`, `remediation_steps` |
| `cost_analysis` | FinOps | `cost_by_category`, `optimizations`, `budgets` |

---

## Usage Guide

### Basic Agent Execution

```python
import asyncio
from src.agents.runner import run_agent

async def main():
    result = await run_agent(
        "qualityguard",
        "Review the authentication module for code quality issues"
    )
    
    print(f"Session: {result.session_id}")
    print(f"Cost: ${result.cost_usd:.4f}")
    
    if result.structured_output:
        review = result.structured_output
        print(f"Score: {review.overall_score}/100")
        print(f"Issues: {len(review.issues)}")
        for issue in review.issues:
            print(f"  [{issue.severity}] {issue.title}")

asyncio.run(main())
```

### With Repository Context

```python
result = await run_agent(
    "codecraft",
    "Implement user authentication with JWT",
    repo_name="auth-service",
    repo_branch="feature/jwt-auth",
)
```

### Resume a Session

```python
# First call
result1 = await run_agent("codecraft", "Analyze the codebase")
session_id = result1.session_id

# Later: resume the conversation
result2 = await run_agent(
    "codecraft",
    "Now implement the changes we discussed",
    resume=session_id,
)
```

### Stream Messages

```python
async for message in run_agent_streaming("sre-triage", incident_details):
    if hasattr(message, 'subtype') and message.subtype == 'init':
        print(f"Session started: {message.session_id}")
    elif hasattr(message, 'content'):
        print(message.content)
```

### Budget Enforcement

```python
result = await run_agent("codecraft", complex_task)

if result.budget_exceeded:
    print(f"⚠️ Budget exceeded!")
    print(f"Used: ${result.cost_usd:.4f}")
    print(f"Budget: ${result.cost_summary.budget_usd:.2f}")
```

### Validate Profiles at Startup

```python
from src.utils.validation import validate_all_profiles

# In your application startup
validate_all_profiles(raise_on_error=True)
```

---

## SDK Capabilities Reference

### 1. Structured Outputs

Use Pydantic schemas for type-safe responses.

```python
from src.schemas import SCHEMA_REGISTRY, get_output_format, validate_output

# Get JSON Schema for SDK
output_format = get_output_format("quality_review")
# Returns: {"type": "json_schema", "schema": {...}}

# Validate raw output
validated = validate_output("quality_review", raw_json_dict)
# Returns: QualityReviewResult (Pydantic model)
```

### 2. Cost Tracking

Track token usage and enforce budgets.

```python
from src.hooks import CostTracker

tracker = CostTracker(
    budget_usd=5.0,
    model="claude-sonnet-4-20250514",
    session_id="my-session",
)

# Process messages
tracker.process_message(message)

# Check status
if tracker.is_budget_exceeded():
    raise BudgetExceededError(tracker.get_summary())

# Get summary
summary = tracker.get_summary()
print(f"Input tokens: {summary.total_input_tokens}")
print(f"Output tokens: {summary.total_output_tokens}")
print(f"Cost: ${summary.actual_cost_usd or summary.estimated_cost_usd:.4f}")
```

### 3. System Prompts

Load agent personas with repository context.

```python
from src.utils.prompt_loader import (
    load_system_prompt,
    get_system_prompt_config,
    build_repo_context,
)

# Build context
context = build_repo_context(
    repo_name="auth-service",
    branch="main",
    additional_info={"sprint": "Sprint 23"},
)

# Get SDK-ready config (preset + append)
config = get_system_prompt_config(
    "codecraft",
    repo_context=context,
    use_preset=True,  # Uses claude_code preset
)
# Returns: {"type": "preset", "preset": "claude_code", "append": "..."}
```

### 4. Hooks

Build complete hooks configuration.

```python
from src.hooks import build_hooks, CostTracker

tracker = CostTracker(budget_usd=5.0)

hooks = build_hooks(
    hooks_profile="default",  # or "build", "security", "minimal"
    cost_tracker=tracker,
)

# Hooks dict is ready for ClaudeAgentOptions
options = ClaudeAgentOptions(hooks=hooks, ...)
```

---

## Best Practices

### 1. Always Set max_turns

Prevents infinite loops in agent execution.

```python
# ✅ Good: max_turns defined
AgentProfile(max_turns=100, ...)

# ❌ Bad: No max_turns (could run forever)
AgentProfile(max_turns=None, ...)
```

### 2. Use Structured Outputs for Programmatic Results

When you need to process agent output programmatically, define a schema.

```python
# ✅ Good: Schema for structured processing
profile = AgentProfile(output_schema="quality_review", ...)
result = await run_agent("qualityguard", prompt)
if result.structured_output:
    score = result.structured_output.overall_score

# ❌ Bad: Parsing free-form text
result = await run_agent("qualityguard", prompt)
# Try to extract score from raw text... error-prone
```

### 3. Use Preset with Append for System Prompts

Leverage Claude Code's built-in capabilities.

```python
# ✅ Good: Extend Claude Code's capabilities
system_prompt = {
    "type": "preset",
    "preset": "claude_code",
    "append": "You are CodeCraft, a senior engineer...",
}

# ❌ Bad: Replace entire system prompt (loses built-in features)
system_prompt = "You are CodeCraft..."
```

### 4. Track Costs for Budget Control

Enable budget enforcement for production agents.

```python
# ✅ Good: Budget defined
AgentProfile(budget_usd=5.0, ...)

# After execution
if result.budget_exceeded:
    alert_admin(result.cost_summary)
```

### 5. Validate Profiles at Startup

Catch configuration errors early.

```python
# In main.py or startup script
from src.utils.validation import validate_all_profiles

validate_all_profiles(raise_on_error=True)
# Throws ProfileValidationError if any profile is invalid
```

---

## Troubleshooting

### "Unknown agent 'xyz'"

The agent ID doesn't exist in `AGENT_PROFILES`.

```python
from config.agent_profiles import list_agent_ids
print(list_agent_ids())
# ['archguard', 'codecraft', 'docuscribe', ...]
```

### "Unknown output_schema 'xyz'"

The schema isn't registered in `SCHEMA_REGISTRY`.

```python
from src.schemas import SCHEMA_REGISTRY
print(list(SCHEMA_REGISTRY.keys()))
# ['quality_review', 'sprint_plan', 'code_craft', ...]
```

### "System prompt file not found"

The prompt file doesn't exist in `prompts/agents/`.

```python
from src.utils.prompt_loader import list_available_prompts
print(list_available_prompts())
# ['codecraft', 'qualityguard', 'sentinel', 'sre_triage']
```

### Budget Exceeded Mid-Task

The agent hit its budget limit. Hooks inject a system message at 80% and block at 100%.

```python
result = await run_agent("codecraft", complex_task)
if result.budget_exceeded:
    # Task was stopped due to budget
    print(f"Partial result available in result.messages")
    print(f"Cost: ${result.cost_usd:.4f} of ${result.cost_summary.budget_usd:.2f}")
```

### SessionStart/SessionEnd Hooks Not Working

These hooks are **NOT SUPPORTED** in the Python SDK. Use alternatives:

- `UserPromptSubmit`: Called when prompt is submitted (similar to session start)
- `Stop`: Called when agent stops (similar to session end)

---

## File Structure

```
sdlc-agent-framework/
├── config/
│   ├── agent_config.py       # MODEL_REGISTRY, base settings
│   └── agent_profiles.py     # AGENT_PROFILES for all 10 agents
├── prompts/
│   └── agents/
│       ├── codecraft.md      # CodeCraft agent persona
│       ├── qualityguard.md   # QualityGuard agent persona
│       ├── sentinel.md       # Sentinel agent persona
│       └── sre_triage.md     # SRE-Triage agent persona
├── src/
│   ├── agents/
│   │   ├── options_builder.py # build_agent_options()
│   │   ├── runner.py          # run_agent(), AgentResult
│   │   └── *_agent.py         # Individual agent files
│   ├── hooks/
│   │   ├── __init__.py        # build_hooks(), exports
│   │   ├── documentation_hooks.py # Logging hooks
│   │   ├── cost_tracker.py    # CostTracker class
│   │   └── cost_hooks.py      # Budget enforcement hooks
│   ├── schemas/
│   │   ├── __init__.py        # SCHEMA_REGISTRY, helpers
│   │   ├── base.py            # Common types
│   │   └── *.py               # Individual schemas
│   └── utils/
│       ├── prompt_loader.py   # System prompt loading
│       └── validation.py      # Profile validation
└── docs/
    └── SDK_CAPABILITIES_ARCHITECTURE.md  # This document
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-11 | Initial SDK capabilities integration |

---

*This document is part of the SDLC Agent Framework. For SDK documentation, see [Claude Agent SDK](https://docs.anthropic.com/claude/agent-sdk).*

