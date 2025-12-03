# SDLC Framework - Quick Reference Card

## 🚀 Getting Started (30 seconds)

```bash
# 1. Install framework
cd sdlc-agent-framework && pip install -r requirements.txt

# 2. Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Initialize your project
python main.py init --target /path/to/your-project

# 4. Run first agent
python main.py agent productspec --target /path/to/your-project --requirements "Your requirements"
```

---

## 📋 CLI Commands

| Command | Example |
|---------|---------|
| **Initialize** | `python main.py init --target ./my-project --type microservice` |
| **ProductSpec** | `python main.py agent productspec --target . --requirements "Build auth"` |
| **ArchGuard** | `python main.py agent archguard --target .` |
| **SprintMaster** | `python main.py agent sprintmaster --target .` |
| **CodeCraft** | `python main.py agent codecraft --target . --task-type backend` |
| **QualityGuard** | `python main.py agent qualityguard --target .` |
| **Dashboard** | `python main.py dashboard` |

---

## 📁 Project Structure

```
your-project/
└── .sdlc/
    ├── config.yaml      # ← Edit this
    ├── memories/
    │   ├── prd.xml
    │   ├── architecture_plan.xml
    │   └── sprint_plan.xml
    └── prompts/         # Custom overrides
```

---

## ⚙️ Minimal config.yaml

```yaml
project:
  name: "My Project"
  type: microservice
  description: "Brief description"

tech_stack:
  backend: [python, fastapi]
```

---

## 🔑 Environment Variables

```bash
# Required (choose one)
ANTHROPIC_API_KEY=sk-ant-...          # Direct Anthropic
# OR
GOOGLE_APPLICATION_CREDENTIALS=...     # Vertex AI

# Optional
GITHUB_TOKEN=ghp_...                   # GitHub integration
LINEAR_API_KEY=lin_api_...             # Linear integration
```

---

## 🎯 Project Types

| Type | Use For |
|------|---------|
| `microservice` | Backend APIs, services |
| `frontend` | React, Next.js, Vue apps |
| `monolith` | Full-stack applications |
| `data-pipeline` | ETL, data processing |

---

## 🤖 Agent Pipeline

```
Requirements → ProductSpec → PRD
                    ↓
              ArchGuard → Architecture
                    ↓
            SprintMaster → Tasks
                    ↓
              CodeCraft → Code
                    ↓
            QualityGuard → Review
```

---

## 🔗 Full Documentation

See [MULTI_REPO_USER_GUIDE.md](./MULTI_REPO_USER_GUIDE.md) for complete documentation.

