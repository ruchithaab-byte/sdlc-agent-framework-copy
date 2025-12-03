# Multi-Repository SDLC Framework - User Guide

## Overview

The SDLC Agent Framework is a reusable system that manages the entire Software Development Life Cycle (SDLC) for **any target repository**. It operates as an "Installed Tool" pattern where:

- **Framework** stays centralized (one installation)
- **Target projects** get lightweight `.sdlc/` configuration
- **Agents** operate on target repos with project-specific context

### Key Features

- 🎯 **Multi-Repository Support**: Manage SDLC across multiple projects from one framework
- 🤖 **10 Specialized Agents**: ProductSpec, ArchGuard, SprintMaster, CodeCraft, QualityGuard, DocuScribe, InfraOps, Sentinel, SRE-Triage, FinOps
- 📝 **Parameterized Prompts**: Jinja2 templates adapt to each project's context
- 📊 **Execution Dashboard**: Real-time monitoring with per-repository tracking
- 🔧 **Auto-Detection**: Detects project info from package.json/pyproject.toml

---

## Prerequisites

### 1. System Requirements

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| Python | 3.11+ | Required for Claude Agent SDK |
| Git | 2.x | For repository operations |
| Node.js | 18+ | Only for dashboard React app |

### 2. Clone and Install Framework

```bash
# Clone the repository
git clone https://github.com/JulleyOnline-in/agentic-coding-framework.git
cd agentic-coding-framework/sdlc-agent-framework

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in `sdlc-agent-framework/`:

```bash
# ============================================
# REQUIRED: Choose ONE AI Provider
# ============================================

# Option A: Anthropic API (Direct)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Option B: Google Vertex AI (Enterprise)
GOOGLE_APPLICATION_CREDENTIALS=config/credentials/google-service-account.json
ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project-id
CLOUD_ML_REGION=us-central1

# ============================================
# OPTIONAL: Integrations
# ============================================

# GitHub (for PR creation, branch management)
GITHUB_TOKEN=ghp_...

# Linear (for project management integration)
LINEAR_API_KEY=lin_api_...

# ============================================
# OPTIONAL: User Tracking
# ============================================

# User email for execution attribution
AGENT_USER_EMAIL=your-email@company.com
```

### 4. Verify Installation

```bash
# Check CLI is working
python main.py --help

# Expected output:
# usage: main.py [-h] {init,agent,dashboard,api,orchestrate} ...
```

---

## Quick Start Guide

### Step 1: Initialize Your Target Project

Navigate to the framework and initialize any repository:

```bash
cd /path/to/sdlc-agent-framework

# Initialize with auto-detection
python main.py init --target /path/to/your-project

# Or specify project type explicitly
python main.py init \
  --target /path/to/your-project \
  --type microservice \
  --name "My Awesome Project" \
  --description "A microservice for handling payments"
```

**Project Types:**
- `microservice` - Backend services (FastAPI, Spring Boot, etc.)
- `frontend` - Web applications (React, Next.js, Vue, etc.)
- `monolith` - Full-stack applications
- `data-pipeline` - Data processing systems

### Step 2: Review Generated Configuration

The init command creates `.sdlc/` in your target project:

```
your-project/
├── .sdlc/
│   ├── config.yaml          # Project configuration ← Edit this!
│   ├── memories/
│   │   ├── prd.xml          # PRD template
│   │   ├── architecture.xml # Architecture template
│   │   └── sprint.xml       # Sprint template
│   └── prompts/             # Custom prompt overrides (optional)
├── src/
└── ... (your existing code)
```

### Step 3: Customize Project Configuration

Edit `.sdlc/config.yaml`:

```yaml
# Project metadata
project:
  name: "Payment Service"
  type: microservice
  description: |
    Payment processing microservice handling transactions,
    refunds, and payment method management.

# Technology stack (used in prompt rendering)
tech_stack:
  backend:
    - python
    - fastapi
    - postgresql
    - redis
  infrastructure:
    - docker
    - kubernetes
    - github-actions

# Skills to auto-load (from agent-framework/agents/agent-skills/)
skills:
  - implementing-python-production
  - implementing-fastapi-production
  - implementing-redis-production

# Per-agent configuration
agents:
  productspec:
    budget_usd: 5.0
  codecraft:
    budget_usd: 10.0
    task_type: backend
  qualityguard:
    coverage_target: 80

# External integrations
integrations:
  linear:
    enabled: false
    team_id: ""
  github:
    enabled: true
```

### Step 4: Run the SDLC Pipeline

Execute agents in sequence to manage your project's SDLC:

```bash
# 1. Create PRD from requirements
python main.py agent productspec \
  --target /path/to/your-project \
  --requirements "Build payment processing with Stripe integration, 
                  support for cards and bank transfers, 
                  webhook handling, and transaction history"

# 2. Design architecture (reads PRD from .sdlc/memories/prd.xml)
python main.py agent archguard --target /path/to/your-project

# 3. Break down into sprint tasks
python main.py agent sprintmaster --target /path/to/your-project

# 4. Implement backend code
python main.py agent codecraft \
  --target /path/to/your-project \
  --task-type backend

# 5. Run quality review
python main.py agent qualityguard --target /path/to/your-project
```

---

## CLI Reference

### Commands Overview

| Command | Description |
|---------|-------------|
| `init` | Initialize a target repository for SDLC management |
| `agent` | Run a specific SDLC agent |
| `dashboard` | Start the monitoring dashboard |
| `api` | Start HTTP API server only |
| `orchestrate` | Route prompts to repositories (multi-repo) |

### `init` Command

```bash
python main.py init [OPTIONS]

Options:
  --target, -t PATH    Path to target repository (required)
  --type TYPE          Project type: microservice|frontend|monolith|data-pipeline
  --name NAME          Project name (auto-detected if not provided)
  --description TEXT   Project description
  --no-register        Don't register in repo_registry.yaml
```

**Examples:**

```bash
# Auto-detect everything
python main.py init --target ~/projects/my-app

# Specify all options
python main.py init \
  --target ~/projects/my-app \
  --type frontend \
  --name "My Dashboard" \
  --description "Admin dashboard for user management"
```

### `agent` Command

```bash
python main.py agent AGENT_NAME [OPTIONS]

Agents:
  productspec    Create PRDs from requirements
  archguard      Design system architecture
  sprintmaster   Plan sprints and tasks
  codecraft      Implement code
  qualityguard   Code review and QA
  docuscribe     Generate documentation
  infraops       Infrastructure automation
  sentinel       Security scanning
  sre-triage     Incident response
  finops         Cost optimization

Options:
  --target, -t PATH      Target project directory
  --task-type TYPE       Task type (for codecraft: backend|frontend|data)
  --requirements TEXT    Requirements text (for productspec)
```

**Examples:**

```bash
# ProductSpec with requirements
python main.py agent productspec \
  --target ~/projects/my-app \
  --requirements "Build user authentication with OAuth2"

# CodeCraft for frontend work
python main.py agent codecraft \
  --target ~/projects/my-app \
  --task-type frontend

# Run from within target project (auto-detect)
cd ~/projects/my-app
python /path/to/framework/main.py agent archguard
```

### `dashboard` Command

```bash
python main.py dashboard [OPTIONS]

Options:
  --host TEXT       Host to bind (default: 0.0.0.0)
  --port INT        WebSocket port (default: 8765)
  --api-port INT    HTTP API port (default: 8766)
  --no-api          Don't start HTTP API server
```

---

## Architecture

### Framework Structure

```
sdlc-agent-framework/                    # Central framework
├── main.py                              # CLI entry point
├── requirements.txt                     # Python dependencies
├── .env                                 # Environment variables
│
├── config/
│   ├── agent_config.py                  # Model configurations
│   ├── agent_profiles.py                # Agent profiles
│   └── repo_registry.yaml               # Multi-repo registry
│
├── src/
│   ├── agents/                          # Agent implementations
│   │   ├── productspec_agent.py
│   │   ├── archguard_agent.py
│   │   ├── codecraft_agent.py
│   │   └── ... (10 agents total)
│   │
│   ├── commands/                        # CLI commands
│   │   └── init_project.py              # Init command
│   │
│   ├── config/                          # Configuration loading
│   │   └── project_config.py            # .sdlc/config.yaml loader
│   │
│   ├── hooks/                           # Execution hooks
│   │   ├── documentation_hooks.py       # Logging hooks
│   │   └── cost_tracker.py              # Cost tracking
│   │
│   ├── orchestrator/                    # Multi-repo orchestration
│   │   ├── registry.py                  # Repository registry
│   │   ├── router.py                    # LLM-based routing
│   │   └── session_manager.py           # Session context
│   │
│   ├── logging/                         # Execution logging
│   │   └── execution_logger.py          # SQLite logger
│   │
│   └── utils/
│       ├── prompt_renderer.py           # Jinja2 rendering
│       └── constants.py                 # Memory path helpers
│
├── prompts/agents/                      # Jinja2 prompt templates
│   ├── productspec.md
│   ├── archguard.md
│   ├── codecraft.md
│   └── ...
│
├── examples/
│   ├── templates/                       # Project templates
│   │   ├── microservice/
│   │   ├── frontend/
│   │   └── monolith/
│   └── sample-project-config.yaml
│
└── logs/
    └── agent_execution.db               # SQLite execution log
```

### Target Project Structure

```
your-project/                            # Any Git repository
├── .sdlc/                               # SDLC configuration
│   ├── config.yaml                      # Project config
│   ├── memories/                        # Agent memories
│   │   ├── prd.xml                      # Product Requirements
│   │   ├── architecture_plan.xml        # Architecture design
│   │   ├── sprint_plan.xml              # Sprint breakdown
│   │   └── qa_summary.xml               # QA results
│   └── prompts/                         # Custom prompt overrides
│       └── codecraft.md                 # (optional)
│
├── src/                                 # Your source code
├── tests/
├── package.json / pyproject.toml        # For auto-detection
└── README.md
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SDLC Agent Framework                             │
│                                                                          │
│  ┌──────────────┐                                                       │
│  │     CLI      │  python main.py agent codecraft --target /project     │
│  └──────┬───────┘                                                       │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐        │
│  │  Load Target │───▶│ Load Project │───▶│  Render Prompt     │        │
│  │  Directory   │    │ Config       │    │  with Jinja2       │        │
│  └──────────────┘    └──────────────┘    └────────────────────┘        │
│                                                   │                      │
│                                                   ▼                      │
│                      ┌────────────────────────────────────────┐         │
│                      │           Claude Agent SDK              │         │
│                      │   (with project-specific context)       │         │
│                      └────────────────────────────────────────┘         │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────────┐        │
│  │  Execution   │◀───│   Hooks      │◀───│  Agent Execution   │        │
│  │  Logger      │    │  (logging)   │    │                    │        │
│  └──────────────┘    └──────────────┘    └────────────────────┘        │
│         │                                          │                     │
│         ▼                                          ▼                     │
│  ┌──────────────┐                     ┌────────────────────┐           │
│  │  Dashboard   │                     │  Target Project    │           │
│  │  (real-time) │                     │  .sdlc/memories/   │           │
│  └──────────────┘                     └────────────────────┘           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Reference

### SDLC Pipeline Agents

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| **ProductSpec** | Create PRDs | Requirements text | `.sdlc/memories/prd.xml` |
| **ArchGuard** | Design architecture | PRD | `.sdlc/memories/architecture_plan.xml`, ADRs |
| **SprintMaster** | Plan sprints | PRD + Architecture | `.sdlc/memories/sprint_plan.xml`, Linear issues |
| **CodeCraft** | Implement code | Architecture | Source code files |
| **QualityGuard** | Code review | Source code | `.sdlc/memories/qa_summary.xml` |

### Supporting Agents

| Agent | Purpose |
|-------|---------|
| **DocuScribe** | Generate documentation |
| **InfraOps** | Infrastructure as code (Terraform, K8s) |
| **Sentinel** | Security scanning and remediation |
| **SRE-Triage** | Incident response and runbooks |
| **FinOps** | Cloud cost optimization |

---

## Configuration Reference

### `.sdlc/config.yaml` Schema

```yaml
# Project metadata (required)
project:
  name: string              # Display name
  type: string              # microservice|frontend|monolith|data-pipeline
  description: string       # Brief description

# Technology stack (recommended)
tech_stack:
  backend: [string]         # e.g., [python, fastapi, postgresql]
  frontend: [string]        # e.g., [react, typescript, tailwind]
  infrastructure: [string]  # e.g., [docker, kubernetes]
  data: [string]            # e.g., [postgresql, redis, kafka]

# Skills to load (optional)
skills: [string]            # Skill IDs from agent-skills/

# Agent overrides (optional)
agents:
  <agent_name>:
    budget_usd: float       # Max cost per run
    task_type: string       # For codecraft: backend|frontend|data
    coverage_target: int    # For qualityguard: min coverage %

# Integrations (optional)
integrations:
  linear:
    enabled: boolean
    team_id: string
    project_id: string
  github:
    enabled: boolean

# Memory configuration (optional)
memories:
  path: string              # Default: memories/
  auto_save: boolean        # Default: true

# Environment settings (optional)
environments:
  development:
    api_base_url: string
  staging:
    api_base_url: string
  production:
    api_base_url: string
```

---

## Dashboard & Monitoring

### Start the Dashboard

```bash
# Start both WebSocket and HTTP API
python main.py dashboard

# Dashboard UI: Open React app in browser
cd src/dashboard/react-app
npm install
npm run dev
# Visit http://localhost:5173
```

### Execution Tracking

All agent executions are logged with:
- Session ID
- Repository ID (target project)
- Agent name
- Tool usage
- Duration and cost
- Artifacts (PRs, commits, files)

### Query Executions by Repository

```bash
# Using SQLite directly
sqlite3 logs/agent_execution.db "
  SELECT r.repo_name, COUNT(e.id) as executions
  FROM repositories r
  JOIN execution_log e ON e.repository_id = r.id
  GROUP BY r.id
"
```

---

## Multi-Repository Orchestration

### Register Multiple Repositories

Edit `config/repo_registry.yaml`:

```yaml
repositories:
  - id: payment-service
    description: Payment processing microservice
    github_url: https://github.com/org/payment-service
    local_path: /path/to/payment-service
    branch: main

  - id: frontend-dashboard
    description: Admin dashboard
    github_url: https://github.com/org/frontend-dashboard
    local_path: /path/to/frontend-dashboard
    branch: main
```

### Route Prompts Automatically

```bash
# LLM routes to correct repository based on prompt
python main.py orchestrate "Add Stripe webhook handling"
# → Routes to payment-service

python main.py orchestrate "Fix the login button styling"
# → Routes to frontend-dashboard

# Or specify repository explicitly
python main.py orchestrate --repo-id payment-service "Add refund endpoint"
```

---

## Customization

### Custom Prompt Overrides

Create custom prompts in your target project's `.sdlc/prompts/`:

```
your-project/.sdlc/prompts/
└── codecraft.md    # Overrides framework's prompts/agents/codecraft.md
```

The prompt renderer checks target project first, then falls back to framework.

### Template Variables

Prompts support Jinja2 variables:

| Variable | Description |
|----------|-------------|
| `{{ project.name }}` | Project name |
| `{{ project.type }}` | Project type |
| `{{ project.description }}` | Description |
| `{{ tech_stack }}` | Technology stack dict |
| `{{ tech_stack.backend }}` | Backend technologies list |
| `{{ skills }}` | Skills list |

**Example prompt template:**

```markdown
# CodeCraft Agent

## Project: {{ project.name }}

{% if tech_stack.backend %}
## Backend Stack
{{ tech_stack.backend | join(", ") }}
{% endif %}

{% for skill in skills %}
- Apply: {{ skill }}
{% endfor %}
```

---

## Troubleshooting

### Common Issues

**1. "Module not found" errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**2. "ANTHROPIC_API_KEY not set"**
```bash
# Check .env file exists and is loaded
cat .env | grep ANTHROPIC
# Or set directly
export ANTHROPIC_API_KEY=sk-ant-...
```

**3. "Target directory does not exist"**
```bash
# Use absolute path
python main.py init --target /full/path/to/project
```

**4. "No .sdlc/config.yaml found"**
```bash
# Initialize the project first
python main.py init --target /path/to/project
```

**5. Dashboard not showing executions**
```bash
# Check database exists
ls -la logs/agent_execution.db

# Verify repository is registered
sqlite3 logs/agent_execution.db "SELECT * FROM repositories"
```

### Debug Mode

```bash
# Enable verbose logging
export SDLC_DEBUG=1
python main.py agent codecraft --target /path/to/project
```

---

## Best Practices

### 1. Version Control `.sdlc/`

Add to your project's git:
```bash
git add .sdlc/config.yaml .sdlc/memories/
git commit -m "Add SDLC configuration"
```

### 2. Use Consistent Project Types

Match project type to your architecture:
- `microservice` → Single-purpose backend services
- `frontend` → Web/mobile UI applications
- `monolith` → Full-stack applications
- `data-pipeline` → ETL/data processing

### 3. Keep Memories Updated

Agent memories are cumulative. The PRD informs architecture, which informs sprint planning, etc.

### 4. Set Appropriate Budgets

Configure per-agent budgets to control costs:
```yaml
agents:
  productspec:
    budget_usd: 5.0
  codecraft:
    budget_usd: 15.0  # Higher for code generation
```

### 5. Review Generated Artifacts

Always review:
- PRDs before architecture design
- Architecture before implementation
- Code before merging

---

## Support

- **Repository**: https://github.com/JulleyOnline-in/agentic-coding-framework
- **Issues**: https://github.com/JulleyOnline-in/agentic-coding-framework/issues

---

*Last Updated: 2025-11-30*

