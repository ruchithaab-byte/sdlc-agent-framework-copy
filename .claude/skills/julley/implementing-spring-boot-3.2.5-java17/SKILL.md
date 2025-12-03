---
name: implementing-spring-boot-3.2.5-java17
description: Implements Spring Boot 3.2.5 with Java 17 using MVC-S-R architecture, Virtual Threads, and Native Image patterns. Handles migration from 2.x and Jakarta EE namespace changes. Use when building new apps, migrating legacy apps, or optimizing for high concurrency/cloud cost.
version: 1.0.0
dependencies:
  - org.springframework.boot:spring-boot-starter-web>=3.2.5
  - org.springframework.boot:spring-boot-starter-data-jpa>=3.2.5
  - io.micrometer:micrometer-tracing-bridge-otel>=1.2.0
  - io.opentelemetry:opentelemetry-exporter-zipkin>=1.32.0
---

# Implementing Spring Boot 3.2.5 with Java 17

## Overview
Implements production-ready Spring Boot 3.2.5 applications on Java 17. Focuses on migration (javax->jakarta), high-concurrency (Virtual Threads), and cloud optimization (Native Image).

## Execution Steps

### Step 1: Migration & Setup
1.  **Verify Java 17+**: Run `java -version`.
2.  **Jakarta Migration**: Replace all `javax.*` imports with `jakarta.*`.
    - See [reference/troubleshooting.md](reference/troubleshooting.md) for details.
3.  **Property Migration**: Use `spring-boot-properties-migrator` to identify changed config keys.

### Step 2: Implement Layered Architecture (MVC-S-R)
Follow the strict separation of concerns:
- **Controller**: Web interface only. See [templates/RestControllerTemplate.java](templates/RestControllerTemplate.java).
- **Service**: Business logic & Transactions. See [templates/ServiceTemplate.java](templates/ServiceTemplate.java).
- **Repository**: Data access. See [templates/RepositoryTemplate.java](templates/RepositoryTemplate.java).
- **Domain**: DTOs (Records) vs Entities (POJOs).
  - DTOs: [templates/RecordDTOTemplate.java](templates/RecordDTOTemplate.java)
  - Entities: [templates/EntityTemplate.java](templates/EntityTemplate.java)
- For architectural rules, see [reference/patterns.md](reference/patterns.md).

### Step 3: Configure Best Practices
1.  **Virtual Threads**: Enable for I/O bound apps.
    - Set `spring.threads.virtual.enabled=true`
2.  **Observability**: Configure Micrometer Tracing & Zipkin.
    - See [templates/application.properties](templates/application.properties).
3.  **Exception Handling**: Use global handler with RFC 7807.
    - Template: [templates/GlobalExceptionHandler.java](templates/GlobalExceptionHandler.java).

## Code Templates
Use these templates as starting points:
- **Controller**: [templates/RestControllerTemplate.java](templates/RestControllerTemplate.java)
- **Service**: [templates/ServiceTemplate.java](templates/ServiceTemplate.java)
- **Repository**: [templates/RepositoryTemplate.java](templates/RepositoryTemplate.java)
- **DTOs**: [templates/RecordDTOTemplate.java](templates/RecordDTOTemplate.java)
- **Entity**: [templates/EntityTemplate.java](templates/EntityTemplate.java)
- **Config**: [templates/application.properties](templates/application.properties)

## Troubleshooting
For issues with migration, property changes, or tracing setup, see [reference/troubleshooting.md](reference/troubleshooting.md).

## Related Resources
- [Spring Boot 3.2 Release Notes](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.2-Release-Notes)
- [Project Loom (Virtual Threads)](https://openjdk.org/jeps/444)
- [GraalVM Native Image](https://www.graalvm.org/latest/reference-manual/native-image/)
