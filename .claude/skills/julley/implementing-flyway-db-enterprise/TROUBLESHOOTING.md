# Troubleshooting & Workarounds

## Common Errors

### Checksum Validation Failure
*Symptoms*: Startup fails with "Migration checksum mismatch".
*Cause*: A V-script was modified after execution.
*Fix*: Revert the script change and apply the change in a new version. (Emergency only: Repair schema history).

### Missing Migration
*Symptoms*: "Detected applied migration not resolved locally".
*Cause*: A script present in the DB is missing from the classpath.
*Fix*: Restore the file or use `spring.flyway.ignore-migration-patterns=*:missing` (transient environments only).

### Database Connection Refused
*Check*: JDBC URL, credentials, network, and that the correct DB module (e.g., `flyway-postgresql`) is on the classpath.

## Workarounds

### W1: Baseline Existing Database
For adopting Flyway on a database with existing data/schema:
- Set `spring.flyway.baseline-on-migrate=true`.
- Flyway will create the history table and mark the current state as baseline.

### W2: Handling Manual Scripts
If a script was run manually and Flyway tries to run it again:
- Run `flyway migrate -skipExecutingMigrations` (CLI) to record it as applied without executing SQL.

### W3: Validation Suppression
For development/CI with fluctuating branches:
- `spring.flyway.ignore-migration-patterns=*:missing` to ignore missing scripts.
- **Warning**: Do not use in production.

