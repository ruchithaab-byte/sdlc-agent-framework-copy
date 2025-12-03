---
name: code-execution
description: Code execution verification and safe database migrations for SDLC workflows
---

# Code Execution Skill Suite

This skill provides patterns for verifying code changes and safely executing database migrations.

## When to Use This Skill

Use this skill when:
- You need to verify that code changes work correctly
- You need to run tests after making changes
- You need to execute database migrations safely
- You need to analyze task requirements and break them down

## code_execution_verify_change

Verifies that code changes work correctly by running the project's test suite.

### Usage

After making code changes, run the appropriate test command:

```bash
# For Node.js/TypeScript projects
npm run test

# For Python projects
pytest

# For Java/Spring Boot projects
./mvnw test

# For Go projects
go test ./...
```

### Best Practices

1. **Run tests after every significant change** - Don't wait until the end
2. **Read test output carefully** - Pay attention to which tests failed and why
3. **Fix failing tests before moving on** - Don't accumulate test debt
4. **Check for new warnings** - Warnings often indicate issues

### Example Workflow

```
1. Make code change
2. Run: npm run test (or appropriate test command)
3. If tests fail:
   - Read the error message
   - Identify the failing assertion
   - Fix the issue
   - Repeat from step 2
4. If tests pass:
   - Proceed to next change
```

## code_execution_flyway_safe

Safely executes Flyway database migrations with proper validation.

### Pre-Migration Checklist

Before running migrations:
1. **Backup the database** (for production)
2. **Validate migration scripts** - Run `flyway validate`
3. **Check for pending migrations** - Run `flyway info`
4. **Review migration scripts** - Ensure they're reversible if possible

### Migration Commands

```bash
# Validate migration scripts
flyway validate

# Show migration status
flyway info

# Run migrations (Maven wrapper)
./mvnw flyway:migrate

# Run migrations (Gradle wrapper)
./gradlew flywayMigrate

# Run migrations (Flyway CLI)
flyway migrate
```

### Best Practices

1. **Never modify applied migrations** - Create new migrations to fix issues
2. **Use versioned migrations** - Format: `V001__description.sql`
3. **Include rollback scripts** - For critical migrations
4. **Test on development first** - Never run untested migrations in production
5. **Use transactions** - Wrap DDL in transactions when supported

### Anti-Patterns to Avoid

- Modifying migration files after they've been applied
- Running migrations without validation
- Skipping migrations in sequence
- Using raw SQL for schema changes outside of migrations

## code_execution_task_breakdown

Analyzes requirements and breaks them into actionable development tasks.

### Workflow

1. **Understand the requirement** - Read and analyze the full requirement
2. **Identify components** - What parts of the system are affected?
3. **Define acceptance criteria** - How will we know when it's done?
4. **Create subtasks** - Break into small, testable units
5. **Estimate effort** - Consider complexity and dependencies

### Task Structure

Each task should have:
- **Title**: Short, action-oriented description
- **Description**: Detailed explanation of what needs to be done
- **Acceptance Criteria**: Specific conditions for completion
- **Dependencies**: Other tasks that must complete first
- **Estimated Effort**: Time or story points

### Example Breakdown

For requirement: "Add user authentication with OAuth2"

```markdown
## Tasks

1. **Set up OAuth2 dependencies**
   - Add Spring Security OAuth2 client
   - Configure application.yml with OAuth2 settings
   - Acceptance: Dependencies resolve, app starts

2. **Implement OAuth2 login flow**
   - Create security configuration
   - Set up OAuth2 redirect endpoints
   - Acceptance: Can initiate OAuth2 flow

3. **Handle OAuth2 callback**
   - Process authorization code
   - Create/update user session
   - Acceptance: Successful login creates session

4. **Add user session management**
   - Implement session storage
   - Add logout functionality
   - Acceptance: Sessions persist, logout clears session

5. **Write integration tests**
   - Test login flow
   - Test session management
   - Acceptance: All tests pass
```

## Integration with SDLC Agents

### CodeCraft Agent
Uses `code_execution_verify_change` after generating code to ensure changes work.

### QualityGuard Agent
Uses all three functions to:
- Break down review tasks
- Verify code changes pass tests
- Validate database migrations

### InfraOps Agent
Uses `code_execution_flyway_safe` for database migrations during deployments.

## Related Skills

- `architecture-planner` - For high-level design decisions
- `linear-integration` - For creating tasks in Linear
- `implementing-flyway-db-enterprise` - Detailed Flyway patterns
