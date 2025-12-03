# Context Orchestrator: Multi-Repository Platform

## Overview

The **Context Orchestrator** is a sophisticated routing and session management system that enables AI agents to work across multiple repositories intelligently. It implements Anthropic's **Router Pattern** best practices, automatically classifying user prompts and routing them to the appropriate repository with the correct context, tools, and configuration.

### Key Features

- **Intelligent Routing**: Uses LLM (Claude) to analyze user prompts and route to the best-matching repository
- **Repository Registry**: YAML-based configuration for managing multiple repositories
- **Dynamic Tool Loading**: Automatically loads repository-specific tools (GitHub MCP Server)
- **Session Isolation**: Each repository gets its own memory path and working directory
- **Agent Configuration**: Automatically configures agents with repository-specific settings

---

## Architecture

The Context Orchestrator consists of four core components that work together:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Context Orchestrator                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │   Registry   │───▶│    Router    │───▶│   Session    │    │
│  │              │    │              │    │   Manager    │    │
│  │ • YAML Config│    │ • LLM Route  │    │ • Prepares   │    │
│  │ • Repo Lookup│    │ • Classify   │    │   Context    │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│         │                    │                    │            │
│         └────────────────────┼────────────────────┘            │
│                              │                                  │
│                              ▼                                  │
│                    ┌──────────────┐                             │
│                    │ GitHub MCP   │                             │
│                    │    Server    │                             │
│                    │              │                             │
│                    │ • File Ops   │                             │
│                    │ • Branches   │                             │
│                    │ • Commits    │                             │
│                    │ • Pull Reqs  │                             │
│                    └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

1. **Repository Registry** (`src/orchestrator/registry.py`)
   - Loads repository configurations from YAML
   - Provides lookup methods for repository metadata
   - Validates configurations using Pydantic models

2. **Repository Router** (`src/orchestrator/router.py`)
   - Uses Anthropic Claude API to classify user prompts
   - Matches prompts against repository descriptions
   - Returns the best-matching repository ID

3. **Context Orchestrator** (`src/orchestrator/session_manager.py`)
   - Coordinates Registry, Router, and GitHub Server
   - Prepares complete session contexts for agents
   - Manages repository-specific memory paths

4. **GitHub MCP Server** (`src/mcp_servers/github_server.py`)
   - Provides async GitHub API operations
   - Exposes tools as callables for Agent SDK
   - Handles file operations, branches, commits, PRs

---

## Repository Registry

### Configuration File

The repository registry is defined in `config/repo_registry.yaml`:

```yaml
repositories:
  - id: auth-service
    description: >
      Authentication microservice handling user login, registration, JWT token management,
      OAuth 2.0 flows, MFA, password reset, and session management. Built with Python/FastAPI,
      PostgreSQL, and Redis for session caching.
    github_url: https://github.com/organization/auth-service
    local_path: ./repos/auth-service
    branch: main

  - id: frontend-dashboard
    description: >
      Frontend dashboard application built with Next.js, React, and TypeScript. Provides
      admin UI for user management, analytics visualization, settings configuration,
      and real-time monitoring dashboards. Uses Tailwind CSS and ShadCN components.
    github_url: https://github.com/organization/frontend-dashboard
    local_path: ./repos/frontend-dashboard
    branch: main
```

### Repository Configuration Fields

Each repository entry must include:

- **`id`** (required): Unique identifier for the repository (e.g., `auth-service`)
- **`description`** (required): Detailed description of the repository's purpose, tech stack, and functionality. This is critical for LLM routing.
- **`github_url`** (required): Full GitHub repository URL
- **`local_path`** (optional, default: `./repos`): Local filesystem path relative to `PROJECT_ROOT`
- **`branch`** (optional, default: `main`): Default branch to use for operations

### How Registry Works

1. **Initialization**: `RepoRegistry` loads the YAML file on instantiation
2. **Validation**: Each repository entry is validated using Pydantic's `RepoConfig` model
3. **Storage**: Repositories are stored in an internal dictionary keyed by `id`
4. **Lookup**: Methods like `get_repo(repo_id)` and `get_all_repos()` provide access

**Example Usage:**

```python
from src.orchestrator import RepoRegistry

# Initialize registry (loads config/repo_registry.yaml)
registry = RepoRegistry()

# Get a specific repository
auth_repo = registry.get_repo("auth-service")
print(auth_repo.github_url)  # https://github.com/organization/auth-service

# List all repositories
all_repos = registry.get_all_repos()
for repo in all_repos:
    print(f"{repo.id}: {repo.description[:50]}...")
```

### Error Handling

- **`RegistryLoadError`**: Raised when YAML file is missing, invalid, or malformed
- **`RepoNotFoundError`**: Raised when a requested repository ID doesn't exist

---

## Repository Router

### How Routing Works

The `RepoRouter` uses **Anthropic's Claude API** to intelligently classify user prompts and route them to the most appropriate repository.

**Routing Process:**

1. **Prompt Construction**: Builds a classification prompt with:
   - All available repository descriptions
   - The user's task description
   - Instructions to return only the repository ID

2. **LLM Classification**: Calls Claude API with:
   - Model: `claude-sonnet-4-20250514` (default)
   - Max tokens: 50 (only need repo ID)
   - System prompt: Repository routing assistant

3. **Response Parsing**: Extracts and validates the repository ID from the LLM response

4. **Validation**: Ensures the returned ID exists in the registry

**Example Routing:**

```python
from src.orchestrator import RepoRegistry, RepoRouter

registry = RepoRegistry()
router = RepoRouter(registry)

# Route a user prompt
repo_id = router.route("Add password reset endpoint with email verification")
# Returns: "auth-service"

repo_id = router.route("Create a user analytics dashboard with charts")
# Returns: "frontend-dashboard"
```

### Router Prompt Template

The router constructs prompts like this:

```
You are a repository routing assistant. Your task is to analyze the user's request 
and determine which repository is the best match.

## Available Repositories:
- **auth-service**: Authentication microservice handling user login, registration...
- **frontend-dashboard**: Frontend dashboard application built with Next.js, React...

## User's Task:
"Add password reset endpoint with email verification"

## Instructions:
1. Analyze the user's task and match it to the most relevant repository.
2. Consider keywords, technical stack, and the nature of the work described.
3. Return ONLY the repository ID that best matches the task.
4. If the task clearly doesn't match any repository, return "UNKNOWN".

## Response Format:
Return only the repository ID (e.g., "auth-service" or "frontend-dashboard").
```

### Error Handling

- **`RoutingError`**: Raised when:
  - `ANTHROPIC_API_KEY` is missing
  - API call fails
  - LLM returns invalid/unrecognized repository ID
  - Empty prompt provided

---

## Context Orchestrator (Session Manager)

### Session Preparation Flow

The `ContextOrchestrator` coordinates all components to prepare a complete agent session:

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Router.route(prompt)                                  │
│    → Returns: repo_id (e.g., "auth-service")            │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Registry.get_repo(repo_id)                           │
│    → Returns: RepoConfig object                         │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 3. GitHubMCPServer(repo_config.github_url, token)      │
│    → Initializes GitHub client                          │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 4. github_server.get_tools()                            │
│    → Returns: [get_file_contents, create_branch, ...]   │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Create SessionContext with:                          │
│    • repo_config: RepoConfig                            │
│    • memory_path: ./memories/{repo_id}/                 │
│    • tools: List[Callable] from GitHub server            │
│    • agent_config: Dict compatible with ClaudeAgentOptions│
└─────────────────────────────────────────────────────────┘
```

### SessionContext Model

The `SessionContext` is a Pydantic model containing:

```python
class SessionContext:
    repo_config: RepoConfig          # Repository configuration
    repo_id: str                      # Repository ID
    memory_path: str                  # Path to repo-specific memory
    tools: List[Callable]             # GitHub tools for Agent SDK
    agent_config: Dict[str, Any]      # Agent configuration dict
    github_server: Optional[GitHubMCPServer]  # Server instance
```

### Agent Configuration

The orchestrator builds agent configuration using `resolve_model_config()`:

- **Model Profile**: Defaults to `"strategy"` (can be `"build"`, `"vertex-strategy"`, `"vertex-build"`)
- **Allowed Tools**: From model profile (e.g., `["Skill", "Read", "Write", "Bash", "memory"]`)
- **Working Directory**: Repository's `local_path`
- **Memory Path**: `./memories/{repo_id}/`
- **Model**: From profile (e.g., `"claude-opus-4@20250514"`)

**Example Agent Config:**

```python
{
    "cwd": "/path/to/repos/auth-service",
    "setting_sources": ["user", "project"],
    "allowed_tools": ["Skill", "Read", "Write", "Bash", "memory"],
    "model": "claude-opus-4@20250514",
    "memory_path": "/path/to/memories/auth-service",
    "repo_id": "auth-service",
    "repo_branch": "main"
}
```

### Usage Examples

**Full Routing Flow:**

```python
from src.orchestrator import RepoRegistry, RepoRouter, ContextOrchestrator

# Initialize components
registry = RepoRegistry()
router = RepoRouter(registry)
orchestrator = ContextOrchestrator(registry, router)

# Prepare session (routes automatically)
session = orchestrator.prepare_session(
    "Add password reset endpoint with email verification"
)

# Use session with Agent SDK
from claude_agent_sdk import ClaudeAgent, ClaudeAgentOptions

agent_options = ClaudeAgentOptions(
    cwd=session.get_cwd(),
    tools=session.tools,  # GitHub tools from get_tools()
    model=session.agent_config["model"],
    allowed_tools=session.agent_config["allowed_tools"],
)

agent = ClaudeAgent(options=agent_options)
result = await agent.run("Add password reset endpoint")
```

**Bypass Routing (Direct Repository):**

```python
# When you already know the repository
session = orchestrator.prepare_session_for_repo("auth-service")
```

---

## GitHub MCP Server

### Architecture

The `GitHubMCPServer` provides async GitHub operations using PyGithub. Since PyGithub is synchronous, all operations are wrapped with `asyncio.to_thread()` to prevent blocking the event loop.

**Async Wrapper Pattern:**

```python
# Private sync method
def _sync_get_file_contents(self, path: str, branch: str) -> Dict[str, Any]:
    repo = self._get_repo()
    content = repo.get_contents(path, ref=branch)
    # ... process content
    return result

# Public async method
async def get_file_contents(self, path: str, branch: str = "main") -> Dict[str, Any]:
    return await asyncio.to_thread(
        self._sync_get_file_contents, path, branch
    )
```

### Available Tools

The server exposes four async tools:

1. **`get_file_contents(path, branch="main")`**
   - Reads file or directory contents from GitHub
   - Returns: `{"path": str, "content": str, "sha": str, ...}`

2. **`create_branch(new_branch, source_branch="main")`**
   - Creates a new branch from a source branch
   - Returns: `{"branch": str, "source_branch": str, "sha": str, "success": bool}`

3. **`create_commit(branch, path, content, message)`**
   - Creates or updates a file with a commit
   - Returns: `{"commit_sha": str, "path": str, "url": str, "success": bool}`

4. **`create_pull_request(head_branch, base_branch, title, body)`**
   - Creates a pull request
   - Returns: `{"pr_number": int, "title": str, "url": str, "state": str, ...}`

### Tool Exposure

**Critical for Agent SDK Integration:**

The `get_tools()` method returns a list of callables that can be passed directly to the Agent SDK:

```python
def get_tools(self) -> List[Callable]:
    """Returns list of callables for Agent SDK consumption."""
    return [
        self.get_file_contents,
        self.create_branch,
        self.create_commit,
        self.create_pull_request,
    ]
```

These callables are async functions that the Agent SDK can invoke directly.

### Initialization

```python
from src.mcp_servers.github_server import GitHubMCPServer

# Initialize with repository URL
github_server = GitHubMCPServer(
    repo_url="https://github.com/organization/auth-service",
    token=os.getenv("GITHUB_TOKEN")  # Optional, uses env var by default
)

# Get tools for Agent SDK
tools = github_server.get_tools()  # List[Callable]
```

### URL Parsing

The server automatically parses various GitHub URL formats:

- `https://github.com/owner/repo`
- `git@github.com:owner/repo.git`
- `owner/repo`

---

## Complete Flow Example

### Step-by-Step Execution

**1. User provides a prompt:**

```bash
python main.py orchestrate "Add password reset endpoint with email verification"
```

**2. Registry loads repositories:**

```python
registry = RepoRegistry()  # Loads config/repo_registry.yaml
# Loads: auth-service, frontend-dashboard
```

**3. Router classifies the prompt:**

```python
router = RepoRouter(registry)
repo_id = router.route("Add password reset endpoint...")
# LLM analyzes prompt against repo descriptions
# Returns: "auth-service"
```

**4. Orchestrator prepares session:**

```python
orchestrator = ContextOrchestrator(registry, router)
session = orchestrator.prepare_session("Add password reset endpoint...")

# Internally:
# - Gets RepoConfig for "auth-service"
# - Initializes GitHubMCPServer with auth-service's GitHub URL
# - Calls github_server.get_tools() → [get_file_contents, create_branch, ...]
# - Creates memory path: ./memories/auth-service/
# - Builds agent_config with model, tools, cwd, etc.
```

**5. Session context is ready:**

```python
session.repo_id                    # "auth-service"
session.repo_config.github_url     # "https://github.com/..."
session.memory_path                # "/path/to/memories/auth-service"
session.tools                       # [get_file_contents, create_branch, ...]
session.agent_config                # {model, allowed_tools, cwd, ...}
```

**6. Use with Agent SDK:**

```python
from claude_agent_sdk import ClaudeAgent, ClaudeAgentOptions

agent_options = ClaudeAgentOptions(
    cwd=session.get_cwd(),
    tools=session.tools,
    **session.agent_config
)

agent = ClaudeAgent(options=agent_options)
await agent.run("Add password reset endpoint...")
```

---

## CLI Usage

### List Repositories

```bash
python main.py orchestrate --list-repos
```

Output:
```
📦 Available Repositories:
------------------------------------------------------------

  ID: auth-service
  Description: Authentication microservice handling user login, registration...
  GitHub: https://github.com/organization/auth-service
  Branch: main

  ID: frontend-dashboard
  Description: Frontend dashboard application built with Next.js, React...
  GitHub: https://github.com/organization/frontend-dashboard
  Branch: main
```

### Route a Prompt (LLM Classification)

```bash
python main.py orchestrate "Add password reset endpoint with email verification"
```

This will:
1. Use LLM to classify the prompt
2. Route to the appropriate repository
3. Display session context

### Bypass Routing (Direct Repository)

```bash
python main.py orchestrate --repo-id auth-service "Add password reset endpoint"
```

This bypasses LLM routing and directly uses the specified repository.

---

## Configuration

### Environment Variables

Required:

- **`ANTHROPIC_API_KEY`**: Anthropic API key for routing (LLM classification)

Optional:

- **`GITHUB_TOKEN`**: GitHub Personal Access Token for GitHub MCP Server operations
  - Required scopes: `repo`, `read:org`
  - Get from: https://github.com/settings/tokens

### Repository Registry File

Location: `config/repo_registry.yaml`

**Adding a New Repository:**

```yaml
repositories:
  - id: new-service
    description: >
      Detailed description of the service, its purpose, tech stack,
      and functionality. This description is critical for LLM routing.
    github_url: https://github.com/organization/new-service
    local_path: ./repos/new-service
    branch: main
```

**Best Practices for Descriptions:**

- Be specific about the tech stack (e.g., "Python/FastAPI", "Next.js/React")
- Mention key functionality and domain (e.g., "authentication", "analytics")
- Include relevant keywords that users might use in prompts
- Keep it concise but informative (50-200 words)

---

## Error Handling

### Registry Errors

**`RegistryLoadError`**:
- YAML file not found
- Invalid YAML syntax
- Missing `repositories` key
- Invalid repository configuration

**`RepoNotFoundError`**:
- Repository ID doesn't exist in registry

### Router Errors

**`RoutingError`**:
- `ANTHROPIC_API_KEY` not set
- Anthropic API call failed
- LLM returned invalid repository ID
- Empty prompt provided

### Session Errors

**`SessionError`**:
- Routing failed
- Repository not found
- GitHub server initialization failed (non-fatal, logs warning)

### GitHub Server Errors

**`GitHubServerError`**:
- `GITHUB_TOKEN` not set
- Invalid repository URL
- GitHub API authentication failed
- GitHub API operation failed (rate limits, permissions, etc.)

**Note**: GitHub server errors are logged as warnings but don't fail session preparation. The session will be created without GitHub tools.

---

## Integration with Agent SDK

### Passing Tools to Agent SDK

The `SessionContext.tools` is a `List[Callable]` that can be passed directly to `ClaudeAgentOptions`:

```python
from claude_agent_sdk import ClaudeAgent, ClaudeAgentOptions
from src.orchestrator import RepoRegistry, RepoRouter, ContextOrchestrator

# Prepare session
registry = RepoRegistry()
router = RepoRouter(registry)
orchestrator = ContextOrchestrator(registry, router)
session = orchestrator.prepare_session(user_prompt)

# Create agent with session context
agent_options = ClaudeAgentOptions(
    cwd=session.get_cwd(),
    tools=session.tools,  # GitHub tools from get_tools()
    model=session.agent_config["model"],
    allowed_tools=session.agent_config["allowed_tools"],
    # ... other options
)

agent = ClaudeAgent(options=agent_options)
```

### Tool Execution

When the agent invokes a GitHub tool, it calls the async function directly:

```python
# Agent SDK calls:
result = await session.tools[0](
    path="src/auth.py",
    branch="main"
)
# This executes: github_server.get_file_contents("src/auth.py", "main")
```

---

## Memory Isolation

Each repository gets its own isolated memory directory:

```
memories/
├── auth-service/
│   ├── prd.xml
│   ├── architecture_plan.xml
│   └── qa_summary.xml
└── frontend-dashboard/
    ├── prd.xml
    ├── architecture_plan.xml
    └── qa_summary.xml
```

The memory path is automatically created by `ContextOrchestrator._ensure_memory_path()` and is included in the `SessionContext.agent_config`.

---

## Model Profiles

The orchestrator uses model profiles from `config/agent_config.py`:

- **`strategy`**: `claude-opus-4@20250514` with tools: `["Skill", "Read", "Write", "Bash", "memory"]`
- **`build`**: `claude-opus-4@20250514` with tools: `["Skill", "Read", "Write", "Bash", "memory", "code_execution"]`
- **`vertex-strategy`**: `gemini-1.5-pro` (Google Vertex AI)
- **`vertex-build`**: `gemini-1.5-pro` with code execution

Default profile is `"strategy"`, but can be changed in `ContextOrchestrator.__init__(model_profile="build")`.

---

## Dependencies

The Context Orchestrator requires these additional packages (already in `requirements.txt`):

```
pydantic>=2.0.0,<3.0.0      # Configuration models
pyyaml>=6.0.0,<7.0.0        # YAML parsing
pygithub>=2.1.0,<3.0.0      # GitHub API client
anthropic>=0.18.0,<1.0.0    # Anthropic API client
```

---

## Best Practices

### Repository Descriptions

- **Be Specific**: Include tech stack, domain, and key features
- **Use Keywords**: Think about what users might say in prompts
- **Keep Updated**: Update descriptions as repositories evolve

### Routing Prompts

- **Be Descriptive**: More context helps the router make better decisions
- **Mention Tech Stack**: If relevant, mention the technology (e.g., "React component", "Python endpoint")
- **Specify Domain**: Mention the domain area (e.g., "authentication", "dashboard", "API")

### Error Handling

- **Check for GitHub Token**: If GitHub tools aren't needed, the system works without them
- **Handle Routing Failures**: Provide fallback to `--repo-id` if routing is unreliable
- **Validate Registry**: Ensure YAML is valid before deployment

---

## Troubleshooting

### Router Returns Wrong Repository

**Problem**: LLM routes to incorrect repository.

**Solutions**:
1. Improve repository descriptions in `repo_registry.yaml`
2. Be more specific in user prompts
3. Use `--repo-id` to bypass routing

### GitHub Tools Not Available

**Problem**: `session.tools` is empty.

**Solutions**:
1. Check `GITHUB_TOKEN` is set: `echo $GITHUB_TOKEN`
2. Verify token has correct scopes: `repo`, `read:org`
3. Check token is valid: Test with GitHub API directly

### Repository Not Found

**Problem**: `RepoNotFoundError` raised.

**Solutions**:
1. Check repository ID in `config/repo_registry.yaml`
2. Verify YAML syntax is valid
3. Ensure repository entry has all required fields

### Memory Path Issues

**Problem**: Memory directory not created.

**Solutions**:
1. Check write permissions on `memories/` directory
2. Verify `PROJECT_ROOT` is correctly resolved
3. Check disk space

---

## Architecture Decisions

### Why YAML for Registry?

- **Human-readable**: Easy to edit and review
- **Version Control**: Changes are tracked in git
- **Validation**: Pydantic ensures type safety
- **No Code Changes**: Add repositories without modifying Python code

### Why LLM Routing?

- **Flexible**: Handles natural language prompts
- **Context-Aware**: Understands intent, not just keywords
- **Scalable**: Works with many repositories without hardcoded rules
- **Adaptive**: Improves as repository descriptions improve

### Why Async Wrappers for GitHub?

- **Non-Blocking**: PyGithub is synchronous, but we need async for Agent SDK
- **Event Loop**: Prevents blocking the asyncio event loop
- **Performance**: Allows concurrent operations
- **Compatibility**: Works seamlessly with Agent SDK's async model

### Why List[Callable] for Tools?

- **Direct Integration**: Can be passed directly to Agent SDK
- **Type Safety**: Callables are strongly typed
- **Flexibility**: Easy to add/remove tools
- **Standard Pattern**: Matches Agent SDK's expected interface

---

## Future Enhancements

Potential improvements:

1. **Caching**: Cache routing decisions for similar prompts
2. **Routing Confidence**: Return confidence scores with routing decisions
3. **Multi-Repository Tasks**: Support tasks that span multiple repositories
4. **Custom Tools**: Allow repositories to define custom tools beyond GitHub
5. **Routing History**: Track and learn from routing decisions
6. **Fallback Strategies**: Automatic fallback if routing fails

---

## Summary

The Context Orchestrator provides a robust, scalable solution for managing multi-repository agent workflows. By combining:

- **YAML-based Registry** for configuration management
- **LLM-based Routing** for intelligent classification
- **Session Management** for context preparation
- **GitHub MCP Server** for repository operations

It enables agents to work seamlessly across multiple repositories with the correct context, tools, and configuration automatically prepared for each task.

---

**For questions or issues, refer to the code documentation in:**
- `src/orchestrator/registry.py`
- `src/orchestrator/router.py`
- `src/orchestrator/session_manager.py`
- `src/mcp_servers/github_server.py`

