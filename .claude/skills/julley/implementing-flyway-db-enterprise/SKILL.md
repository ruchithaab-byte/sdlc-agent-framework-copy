---
name: implementing-flyway-db-enterprise
description: Implements Flyway database migrations in Spring Boot 3.2.5. Covers single/multi-datasource patterns, multi-schema management, callbacks, best practices (immutability, zero-padding, SQL-first), workarounds (baseline, manual scripts), and anti-patterns. Use for schema versioning and lifecycle management.
version: 1.0.0
dependencies:
  - spring-boot>=3.2.5
  - flyway-core>=11.14.1
---

# Implementing Flyway DB Enterprise

## Overview
Procedural knowledge for implementing Flyway migrations in Spring Boot 3.2.5. Covers configuration, patterns, and operational best practices.

**Key Requirement**: Spring Boot 3.2.5 manages Flyway 11.14.1. You **MUST** include a database-specific module (e.g., `flyway-postgresql`) or startup will fail.

## Quick Start
1. Add `flyway-core` and `flyway-{db}` dependencies.
2. Configure `spring.flyway` properties in `application.yml`.
3. Add SQL scripts to `src/main/resources/db/migration/` naming them `V001__Desc.sql`.

## Documentation Index

| Topic | File | Description |
|-------|------|-------------|
| **Patterns** | [PATTERNS.md](PATTERNS.md) | Multi-datasource, Multi-schema, Callbacks |
| **Best Practices** | [BEST_PRACTICES.md](BEST_PRACTICES.md) | Naming, Security, Immutability |
| **Anti-Patterns** | [ANTI_PATTERNS.md](ANTI_PATTERNS.md) | What to avoid (Mutable scripts, etc.) |
| **Troubleshooting** | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common errors and Workarounds |
| **Examples** | [EXAMPLES.md](EXAMPLES.md) | Config snippets and code examples |

## Essential Configuration

**Minimal `application.yml`**:
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/app_db
    username: ${DB_USER}
    password: ${DB_PASS}
  flyway:
    enabled: true
    locations: classpath:db/migration
    user: ${FLYWAY_USER} # Dedicated DDL user (Recommended)
    password: ${FLYWAY_PASS}
```

## Templates
Use the `templates/` directory for production-ready code:
- `application.yml.template`: Standard configuration
- `multi-datasource-config.template`: Java config for multiple DBs
- `java-migration.template`: Skeleton for Java migrations
