# Flyway Best Practices

## Dependency Management
**Flyway 10+ Requirement**: You MUST include a database-specific module (e.g., `flyway-postgresql`, `flyway-mysql`) alongside `flyway-core`.
- **Maven**: `flyway-core` + `flyway-postgresql`
- **Gradle**: `implementation 'org.flywaydb:flyway-core'`, `implementation 'org.flywaydb:flyway-postgresql'`

## Immutability Principle
Treat versioned scripts (`V__`) as immutable.
- **Never modify** a script after it has been executed.
- **Fixes**: Create a new version (`V_N+1`) to correct mistakes.
- **Consequence**: Modifying executed scripts causes checksum errors and startup failures.

## Script Naming & Organization
- **Zero-Padding**: Use `V001__`, `V010__` to ensure file sorting matches execution order.
- **Format**: `V{Version}__{Description}.sql` (Two underscores).
- **Location**: Default `src/main/resources/db/migration`.

## Backward Compatibility
Design schema changes to be compatible with the *previous* application version.
- Allows rolling back application code without database rollback.
- Avoids reliance on Flyway Undo scripts (which are often insufficient).

## SQL-First Approach
Prefer SQL migrations over Java migrations.
- **SQL**: Concise, declarative, easy to audit.
- **Java**: Use only for complex logic, large data updates, or conditional execution.

## Security
- **Dedicated DDL User**: Configure `spring.flyway.user/password` with elevated privileges.
- **Least Privilege**: Application runtime user (`spring.datasource.*`) should have restricted permissions.
- **Secrets**: Use environment variables (`${DB_PASSWORD}`), never hardcode credentials.

