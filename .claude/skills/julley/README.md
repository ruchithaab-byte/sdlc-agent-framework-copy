# Julley Platform Skills

This directory contains the unified skill library for the Julley platform. Skills are automatically discovered and loaded by the Claude Agent SDK via `setting_sources=["user", "project"]`.

## Skill Categories

### Frontend Development
| Skill | Description | Primary Agents |
|-------|-------------|----------------|
| `implementing-nextjs-14-production` | Next.js 14 App Router patterns, Server Components, Server Actions, caching | CodeCraft |
| `implementing-react-18-architecture` | React 18 concurrent rendering, hooks, component composition | CodeCraft |
| `implementing-shadcn-ui-production` | shadcn/ui components, CVA patterns, theming | CodeCraft |
| `implementing-radix-ui-production` | Radix UI primitives, asChild composition, accessibility | CodeCraft |
| `implementing-tailwind-enterprise` | Enterprise Tailwind patterns, design tokens, JIT | CodeCraft |

### Backend Development
| Skill | Description | Primary Agents |
|-------|-------------|----------------|
| `implementing-spring-boot-3.2.5-java17` | Spring Boot 3.2.5, MVC-S-R architecture, Virtual Threads | CodeCraft |
| `implementing-jdk-17-architecture` | JDK 17 patterns (Records, Sealed Classes, Pattern Matching) | CodeCraft |
| `implementing-kafka-production` | Apache Kafka production patterns, Schema Registry | CodeCraft |
| `implementing-flowable-7-spring-boot-3` | Flowable BPMN/CMMN/DMN, saga orchestration | CodeCraft |

### Data Layer
| Skill | Description | Primary Agents |
|-------|-------------|----------------|
| `implementing-flyway-db-enterprise` | Flyway 11.x migrations, schema versioning | CodeCraft |
| `implementing-redis-7-alpine-containerized` | Redis 7 Alpine, caching patterns, containerization | CodeCraft |

### Infrastructure & DevOps
| Skill | Description | Primary Agents |
|-------|-------------|----------------|
| `implementing-kong-gateway` | Kong Gateway DB-less mode, API routing | InfraOps, ArchGuard |
| `implementing-kuma-production` | Kuma/Kong Mesh service mesh, mTLS | InfraOps, ArchGuard |
| `implementing-opa-production` | Open Policy Agent, Rego policies, admission control | InfraOps, Sentinel |
| `implementing-unleash-featureops` | Unleash feature flags, gradual rollouts | InfraOps, SRE-Triage |

### Integrations
| Skill | Description | Primary Agents |
|-------|-------------|----------------|
| `implementing-ably-realtime` | Ably realtime messaging, Pub/Sub, presence | CodeCraft |
| `implementing-algolia-search` | Algolia search, indexing, instant search | CodeCraft |
| `implementing-linear-excellence` | Linear workflow patterns, sprint management | ProductSpec, SprintMaster |
| `implementing-permitio-authorization` | Permit.io authorization, RBAC/ABAC | CodeCraft, Sentinel |

### Documentation
| Skill | Description | Primary Agents |
|-------|-------------|----------------|
| `mintlify-documentation` | Mintlify docs setup, OpenAPI integration | DocuScribe |
| `configuring-mintlify` | Mintlify configuration, theming, troubleshooting | DocuScribe |

## How Skills Are Loaded

The Claude Agent SDK automatically discovers skills from this directory when agents are initialized with:

```python
ClaudeAgentOptions(
    setting_sources=["user", "project"],  # Auto-discovers .claude/skills/
    allowed_tools=["Skill", ...],
)
```

## Skill Structure

Each skill follows this structure:

```
implementing-{technology}/
├── SKILL.md              # Main skill file with YAML frontmatter
├── patterns/             # Detailed pattern implementations (optional)
├── templates/            # Code templates (optional)
├── reference/            # Reference documentation (optional)
└── scripts/              # Utility scripts (optional)
```

### SKILL.md Frontmatter

```yaml
---
name: implementing-{technology}
description: Concise description for skill discovery (max 1024 chars)
version: 1.0.0
dependencies:
  - package>=version
---
```

## Creating New Skills

Use the `template/` directory to create new skills:

1. Copy `template/` to a new directory named `implementing-{technology}/`
2. Edit `SKILL.md` with proper frontmatter and content
3. Add patterns, templates, and reference docs as needed
4. The skill will be auto-discovered on next agent run

## Usage in Agent Prompts

Reference skills explicitly in agent prompts for targeted guidance:

```python
prompt = """
Use the implementing-spring-boot-3.2.5-java17 skill for service architecture.
Use the implementing-kafka-production skill for event messaging.
Use the implementing-flyway-db-enterprise skill for database migrations.

Implement the authentication service following these skills.
"""
```

## Skill Discovery

Skills are matched to queries based on:
1. **Name matching** - Direct reference by skill name
2. **Description matching** - Semantic matching against skill description
3. **Dependency matching** - Technology stack alignment

The SDK loads skill descriptions at startup and makes full content available on-demand when referenced.


