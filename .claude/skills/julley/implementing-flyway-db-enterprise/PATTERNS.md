# Flyway Patterns

## Standard Single-Database
For standard Spring Boot applications:
- **Configuration**: Auto-configured via `spring.flyway.*` properties.
- **Location**: `src/main/resources/db/migration/`.
- **Execution**: Automatic on startup.

## Multi-Datasource Isolation
For multiple isolated databases (e.g., primary + audit):
1. **Disable Auto-configuration**: `spring.flyway.enabled=false`.
2. **Manual Configuration**: Define `Flyway` beans per datasource.
3. **Isolation**: Use separate locations (e.g., `db/migration/primary`, `db/migration/audit`) and history tables.

See `templates/multi-datasource-config.template` for implementation.

## Multi-Schema Management
For single datasource with multiple schemas:
1. **Strategy**: Implement `FlywayMigrationStrategy`.
2. **Execution**: Explicitly trigger migration for each schema in correct order.

See `templates/multi-schema-config.template` for implementation.

## Callback Integration
Execute logic at lifecycle events (BEFORE_MIGRATE, AFTER_MIGRATE).
- **SQL Callbacks**: Event-named files (e.g., `afterMigrate.sql`) in migration folder.
- **Java Callbacks**: Implement `Callback` interface and register as Spring bean.

See `templates/java-callback.template`.

