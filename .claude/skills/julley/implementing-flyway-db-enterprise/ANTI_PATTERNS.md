# Flyway Anti-Patterns

## ❌ Mutable Versioned Scripts
**Bad**: Editing `V005__Add_Table.sql` after execution.
**Good**: Adding `V006__Fix_Table.sql`.
**Why**: Modifying executed scripts changes checksums, causing validation failures on other environments.

## ❌ Over-Reliance on Undo Scripts
**Bad**: Relying on `U__` scripts for rollbacks.
**Good**: Designing backward-compatible schema changes and using backups.
**Why**: Undo scripts cannot handle partial failures (DDL is often non-transactional) and add complexity.

## ❌ Shared Development Database
**Bad**: Multiple developers using one DB instance.
**Good**: Local Docker containers or isolated DBs per developer.
**Why**: Prevents conflicts and ensures migrations are tested in isolation.

## ❌ Missing Database-Specific Module
**Bad**: Depending only on `flyway-core`.
**Good**: Including `flyway-postgresql` (or relevant DB module).
**Why**: Flyway 10+ removed DB support from core; application will fail to start.

