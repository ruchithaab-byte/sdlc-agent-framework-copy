---
name: implementing-flowable-7-spring-boot-3
description: Implements Flowable 7.0.1 with Spring Boot 3.2.5 and Java 17. Provides patterns for delegate expressions, external workers, saga orchestration, and async continuation. Includes best practices for Jakarta EE compliance, transaction management, and variable handling. Use when implementing BPMN/CMMN/DMN processes, orchestrating microservices, managing long-running workflows, or coordinating distributed transactions.
version: 1.0.0
dependencies:
  - org.flowable:flowable-spring-boot-starter>=7.0.1
  - org.springframework.boot:spring-boot>=3.2.5
  - java>=17
---

# Implementing Flowable 7.0.1 with Spring Boot 3.2.5

## Overview

Implements Flowable 7.0.1 Open Source integration with Spring Boot 3.2.5 and Java 17. Flowable 7.0.1 requires Java 17 baseline and Jakarta EE 9/10 compliance. The engine operates as an embedded microservice, exposing Flowable services as native Spring beans.

## Implementation Workflow

Copy this checklist and track your progress:

```markdown
Flowable Implementation Progress:
- [ ] Step 1: Configure dependencies (Maven/Gradle)
- [ ] Step 2: Configure data source (application.properties)
- [ ] Step 3: Implement delegate expressions for service tasks
- [ ] Step 4: Configure external workers (for long-running tasks)
- [ ] Step 5: Set up transaction boundaries at service layer
- [ ] Step 6: Apply transient variable doctrine
- [ ] Step 7: Add async continuations to break long paths
- [ ] Step 8: Test Jakarta EE compliance (no javax.* packages)
- [ ] Step 9: Verify Spring DI in all delegates
- [ ] Step 10: Performance test with production load
```

## Prerequisites

- Spring Boot 3.2.5 project structure
- Java 17 runtime environment
- Database connection configured (PostgreSQL, MySQL, Oracle)
- All dependencies are Jakarta EE-compliant (no javax.* packages)

## Execution Steps

### Step 1: Dependency Configuration

Spring Boot 3.2.5 integration requires Flowable starter and production database driver.

**Maven Configuration**: Read `templates/maven-dependency.template` and copy the dependency block to your pom.xml.

**Best Practice**: ✅ Use persistent, enterprise-grade database. ✅ Include database-specific driver.

### Step 2: Data Source Configuration

Externalize database configuration using Spring Boot Externalized Configuration.

**Configuration Template**: Read `templates/application-properties.template` for the configuration block.

**Best Practice**: ✅ Use environment variables for passwords (`${DB_PASSWORD}`).

### Step 3: Delegate Expression Pattern (MANDATORY)

Implement Service Tasks using Delegate Expression pattern for Spring dependency injection.

**Template**: See `templates/delegate-expression.template` for implementation details.

**Implementation**:

1. Create Java class implementing `JavaDelegate`
2. Annotate with `@Component("beanName")`
3. Use `@Autowired` for dependency injection
4. Reference in BPMN: `flowable:delegateExpression="${beanName}"`

### Step 4: External Worker Pattern (RECOMMENDED)

Decouple long-running tasks from engine using External Worker pattern.

**Template**: See `templates/external-worker.template` for worker implementation.

**Best Practice**: ✅ Mandatory for tasks >100ms. ✅ Decouples engine from business logic execution.

### Step 5: Transaction Management

Manage transactions at service layer, not within delegates.

**Pattern**: Wrap Flowable API calls with `@Transactional` annotation at service layer.

```java
@Service
public class ProcessService {
    @Autowired
    private RuntimeService runtimeService;
    
    @Transactional
    public String startProcess(String processKey, Map<String, Object> variables) {
        return runtimeService.startProcessInstanceByKey(processKey, variables).getId();
    }
}
```

### Step 6: Variable Management

Apply Transient Variable Doctrine to prevent database bloat.

**Template**: See `templates/transient-variable.template` for usage patterns.

**Rule**:

- **Transient**: Temporary data (API responses, calculations) -> `setTransientVariable()`
- **Persistent**: Audit-critical business data (IDs, status) -> `setVariable()`

### Step 7: Async Continuation

Break synchronous paths frequently to minimize transaction windows.

**Template**: See `templates/async-continuation.template` for BPMN XML.

**Pattern**: Add `flowable:async="true"` to Service Tasks to delegate execution to Async Executor in new transaction.

## Validation Steps

After implementation, verify:

1. **Jakarta EE Compliance Check**:

   ```bash
   mvn dependency:tree | grep javax
   # Should return no results
   ```

2. **Spring DI Verification**:
   - All delegates annotated with `@Component` or `@Service`
   - All BPMN uses `flowable:delegateExpression` (not `flowable:class`)
   - No `NullPointerException` in delegate execution

3. **Transaction Boundary Check**:
   - All Flowable API calls wrapped in `@Transactional` at service layer
   - No manual transaction management in delegates

## Patterns and Resources

**Core Patterns**:

- **Delegate Expression**: `templates/delegate-expression.template`
- **External Worker**: `templates/external-worker.template`
- **Saga Orchestration**: `templates/saga-orchestration.template`
- **Async Continuation**: `templates/async-continuation.template`

**Detailed Guides**:

- **Anti-Patterns**: See [ANTI-PATTERNS.md](ANTI-PATTERNS.md) for blocking transactions and common mistakes.
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for error handling.
- **Security**: See [SECURITY.md](SECURITY.md) for credential management.
- **Examples**: See [EXAMPLES.md](EXAMPLES.md) for real-world scenarios.

## Workarounds

**Data Persistence**: Use Spring Data JPA (see `templates/spring-data-jpa-workaround.template`)
**Event Integration**: Use Flowable Event Registry (see `templates/event-registry-workaround.template`)
