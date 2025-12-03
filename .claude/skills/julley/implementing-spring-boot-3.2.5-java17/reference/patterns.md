# Architectural Patterns & Best Practices

## Patterns

### 1. Layered Architecture (MVC-S-R)
**Principle**: Strict separation of concerns across Controller (presentation), Service (business), Repository (data access) layers.
**Implementation**:
- Controller handles HTTP concerns only
- Service encapsulates business logic and transactions
- Repository manages data persistence
- Clear boundaries prevent coupling

### 2. Dependency Injection (Constructor Injection)
**Principle**: Components receive dependencies through constructor parameters rather than instantiating them directly.
**Implementation**:
- Constructor parameters for all dependencies
- Final fields for immutability
- Explicit dependency contracts

### 3. Transaction Boundary (Service Layer)
**Principle**: Transaction boundaries defined at Service layer to coordinate multiple Repository operations.
**Implementation**:
- `@Transactional(readOnly = true)` as default
- `@Transactional` override for write operations
- Service methods coordinate Repository calls

### 4. Observability (Micrometer Tracing)
**Principle**: Distributed tracing for correlating requests across microservices.
**Implementation**:
- Micrometer Observation API, OpenTelemetry bridge, Zipkin exporter
- Correlation IDs in MDC

### 5. Virtual Threads (Project Loom)
**Principle**: Lightweight threads for high-concurrency I/O-bound operations.
**Implementation**: `spring.threads.virtual.enabled=true`

### 6. AOT Compilation (GraalVM Native Image)
**Principle**: Ahead-of-time compilation for cloud-native deployments.
**Implementation**: GraalVM Native Image compilation for reduced startup time and memory.

## Best Practices

1.  **Java 17 Records for DTOs**: Use Records for immutable DTOs in API contracts.
2.  **Sealed Classes**: Use for domain hierarchies (e.g., Service results).
3.  **Constructor Injection**: Always use for Spring components.
4.  **Service Layer Transactions**: Define boundaries at Service, not Repository/Controller.
5.  **Externalized Config**: Never hardcode. Use `application.properties` or env vars.
6.  **Java Config**: Prefer `@Configuration` over XML.
7.  **Targeted Scanning**: Avoid broad `@ComponentScan`.

## Anti-Patterns to Avoid

1.  **God Object (SRP Violation)**: Single class handling all responsibilities.
    - *Remediation*: Decompose into focused classes.
2.  **Hardcoding Values**: Embedding config in code.
    - *Remediation*: Externalize to properties.
3.  **Excessive Coupling**: Business logic in Controller or Validation in Repository.
    - *Remediation*: Enforce layered boundaries.
4.  **Overengineering**: Unnecessary complexity.
5.  **Transactional Overload**: Transactions on read-only or non-db operations.
6.  **Business Logic in Controllers**: Controllers should only delegate.

