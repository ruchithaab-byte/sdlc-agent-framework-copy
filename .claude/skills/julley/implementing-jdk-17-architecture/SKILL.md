---
name: implementing-jdk-17-architecture
description: Implements JDK 17 architectural standards by applying patterns (Records for immutable DTOs, Sealed Classes for controlled hierarchies, Pattern Matching for exhaustive switching), following best practices (try-with-resources for resource management, functional Stream API with pure functions, disciplined exception handling), implementing workarounds (Records vs JPA entities using data projection pattern with TupleTransformer, incremental migration from JDK 8/11), and avoiding anti-patterns (Records as JPA entities, side effects in Stream operations, exception swallowing, imperative loops). Use when migrating to JDK 17, implementing modern Java applications, building data-oriented programs, enforcing immutability and type safety, or developing microservices requiring modern Java features.
version: 1.0.0
dependencies:
  - java>=17
---

# Implementing JDK 17 Architecture

## Overview

This skill guides the transition to Data-Oriented Programming in Java. Unlike traditional object-oriented patterns that often mix mutable state with complex behavior, JDK 17 architecture encourages the separation of immutable data (Records) from domain logic (Sealed Interfaces, Pattern Matching). This approach reduces the bug surface area through strong compile-time guarantees, enforces thread safety by default, and dramatically improves maintainability for modern distributed systems and microservices.

## When to Use

Use this skill when:
- Migrating from JDK 8 or JDK 11 to JDK 17
- Implementing new Java applications with modern patterns
- Building data-oriented applications requiring immutability
- Enforcing type safety through sealed hierarchies
- Developing microservice architectures requiring modern Java features
- Reducing boilerplate code in data-holding classes
- Implementing exhaustive type switching with compiler guarantees

**Input format**: Java codebase, business requirements, database schema (if using JPA)
**Expected output**: Production-ready JDK 17 implementation following enterprise patterns, best practices applied, workarounds documented, anti-patterns avoided

## Prerequisites

Before using this skill, ensure:
- JDK 17+ installed and configured (`java -version` must show 17 or later)
- Maven (compiler.source/target set to 17+) or Gradle (toolchain set to 17)
- Understanding of Java fundamentals (classes, interfaces, inheritance)
- Database access configured (if using JPA with Records for projections)

## Core Patterns

### Immutable Data Structures - Records (JEP 395)

Records provide streamlined, immutable data-holding classes, eliminating boilerplate for DTOs, configuration classes, and domain events.

**Pattern**: Use Records for all immutable value classes:
- Data Transfer Objects (DTOs): API request/response contracts
- Configuration Classes: Application settings that remain constant
- Domain Events: Immutable events in event-driven architectures

**Template**: See `templates/record-dto.template`

**Best Practice**: 
- Use compact constructor for parameter validation and initialization logic
- All components are implicitly final, ensuring immutability
- Records automatically generate canonical constructor, accessors, equals(), hashCode(), and toString()

**Anti-Pattern**: ❌ Using Records as JPA entities (Records are immutable, JPA requires mutable entities with no-arg constructor and setters). ❌ Adding instance fields beyond components (Records must represent state purely through defined components). ❌ Attempting to extend other classes (Records are implicitly final).

**Workaround**: For JPA integration, use Records strictly as DTOs and implement data projection pattern using TupleTransformer. See "Records vs JPA Entities Workaround" below.

### Controlled Hierarchies - Sealed Classes (JEP 409)

Sealed Classes provide precise mechanism for controlling inheritance, defining finite type hierarchies that enable exhaustive pattern matching.

**Pattern**: Use sealed interfaces/classes to define closed sets of types representing domain concepts:
- Result types: Success/Failure variants
- Command types: Finite set of operations
- State machines: All possible states explicitly defined

**Template**: See `templates/sealed-hierarchy.template`

**Best Practice**: 
- Use Records as permitted subclasses (Records are implicitly final, perfect for sealed hierarchies)
- All permitted subclasses must be in same module or package as sealed type
- Subclasses must explicitly choose: `final`, `sealed`, or `non-sealed`

**Anti-Pattern**: ❌ Opening sealed hierarchy unnecessarily with `non-sealed` (defeats purpose of controlled inheritance). ❌ Placing permitted subclasses in different packages without proper module configuration. ❌ Attempting to extend sealed class from external package without permission.

**Architectural Benefit**: Sealed classes provide opposite guarantee of open classes - users know all possible subtypes, enabling exhaustive pattern matching with compiler enforcement.

### Exhaustive Type Switching - Pattern Matching (JEP 406)

Pattern Matching for switch enables expressive consumption of sealed hierarchies with compiler-enforced exhaustiveness.

**Pattern**: Use switch expressions with type patterns for exhaustive handling of sealed types:
- Type patterns automatically bind matched values
- Pattern guards (`&&`) refine matches with boolean conditions
- Explicit `case null` centralizes null handling

**Template**: See `templates/pattern-matching-switch.template`

**Best Practice**: 
- When switching on sealed types, compiler enforces exhaustiveness (no default needed if all cases covered)
- Use pattern guards for fine-grained control: `case Triangle t && (t.getSides() == 3)`
- Handle null explicitly within switch: `case null -> "Input is null"`

**Anti-Pattern**: ❌ Missing cases when switching on sealed types (compiler error, but must be addressed). ❌ Using default case unnecessarily when all sealed subtypes are handled. ❌ Not leveraging pattern guards for complex conditions.

**Compiler Enforcement**: Switch expressions on sealed types guarantee exhaustiveness at compile time, eliminating runtime errors from incomplete domain logic.

### Modern Resource Management

try-with-resources (TWR) is mandatory standard for all AutoCloseable resource management, eliminating error-prone manual cleanup.

**Pattern**: Use TWR for all resources implementing AutoCloseable:
- File streams, database connections, sockets
- Multiple resources closed in reverse order of declaration
- Automatic closure even if exception occurs

**Template**: See `templates/try-with-resources.template`

**Best Practice**: 
- Declare all AutoCloseable resources in TWR parentheses
- Resources are automatically closed upon exiting block (normal or exception)
- No explicit finally block required for resource cleanup
- Catch specific exceptions first, then general (specific to general order)

**Anti-Pattern**: ❌ Manual finally blocks for resource cleanup (error-prone, verbose). ❌ Not using TWR for AutoCloseable resources (potential resource leaks). ❌ Catching general exceptions before specific ones (unreachable code or logical flaws).

**Critical**: TWR provides foundational layer for future Foreign Function & Memory API (JEP 412) integration requiring safe native resource management.

### Disciplined Exception Handling

Enterprise applications require strict exception handling practices to ensure resilience and prevent resource leaks.

**Pattern**: Specific to general catch order with proper exception handling:
- Java evaluates catch blocks sequentially
- Most specific (subclass) exceptions must be caught before general (superclass)
- All caught exceptions must be handled properly (never swallow)

**Best Practice**: 
- Always catch exceptions from most specific to least specific type
- Never swallow exceptions (silent catching hides errors, complicates debugging)
- Implement proper recovery logic or robust logging for all caught exceptions
- Use specific exception types to provide meaningful error context

**Anti-Pattern**: ❌ Swallowing exceptions silently (hides errors, masks system failures). ❌ Catching general Exception before specific types (unreachable code, compilation errors). ❌ Empty catch blocks without logging or recovery (operational anti-pattern).

**Operational Impact**: Proper exception handling is non-negotiable for high-volume microservice environments where resource leaks and hidden failures cause cascading system degradation.

### Functional Stream Processing

Stream API provides modern, functional, declarative data processing. Misusing streams with imperative styles or side effects undermines their benefits.

**Pattern**: Declarative Stream API usage with pure functions:
- Use map, filter, collect over boilerplate loops
- Behavioral parameters must be pure functions (no side effects)
- Leverage lazy evaluation and method references

**Template**: See `templates/stream-aggregation.template`

**Best Practice**: 
- Use declarative style: define what to achieve, not how
- Ensure behavioral parameters are pure functions (no external state modification)
- Prefer method references (`Class::method`) over verbose lambdas
- Understand lazy evaluation: computation only happens upon terminal operation
- Use parallel streams judiciously (test performance benefit first)

**Anti-Pattern**: ❌ Side effects in stream operations (modifying external state within map/filter - execution order/frequency unpredictable). ❌ Imperative loops for transformations (manual iteration instead of Stream API). ❌ Blocking stream operations with slow I/O (prevents optimization, causes bottlenecks).

**Stream Optimization**: Stream implementations use lazy evaluation and may elide operations or execute concurrently. Reliance on side effects leads to non-deterministic behavior.

### Records vs JPA Entities Workaround

Records cannot be used as JPA entities due to immutability and structural incompatibility. Data projection pattern provides architectural workaround.

**Pattern**: Separate mutable JPA entities from immutable Record DTOs using projection:
- Entities remain traditional mutable classes with no-arg constructor and setters
- Records used for DTOs and data projection from queries
- Use TupleTransformer or constructor expressions for query-to-Record mapping

**Template**: See `templates/jpa-projection.template`

**Best Practice**: 
- Use Records strictly as DTOs, never as entities
- Leverage JPA/Hibernate TupleTransformer for efficient projections
- Select only required columns in queries, map directly to Records
- Bypass full entity lifecycle overhead for read-only operations

**Anti-Pattern**: ❌ Attempting to use Records as JPA entities (Records are immutable, JPA requires mutable state). ❌ Manually adding no-arg constructor and mutable fields to Records (defeats purpose). ❌ Relying on framework-specific reflection hacks to bypass final field constraints (brittle, non-standard).

**Architectural Separation**: This workaround respects contractual requirements of both JPA (mutable entities) and Records (immutable data), maintaining clear separation of concerns.

## Code Templates

Reference templates in `templates/` directory for implementation patterns:

- **record-dto.template**: Record definition with compact constructor for validation
- **sealed-hierarchy.template**: Sealed interface with Record implementations
- **pattern-matching-switch.template**: Exhaustive switch expression on sealed types
- **try-with-resources.template**: Multiple resource management with proper exception handling
- **stream-aggregation.template**: Declarative grouping and aggregation operations
- **jpa-projection.template**: JPA query projecting to Record using TupleTransformer

## Real-World Examples

### Example 1: API Response Modeling with Sealed Types

Minimal example demonstrating sealed interface for API results with exhaustive pattern matching:

```java
// Sealed interface defining finite result set
public sealed interface ApiResult<T> permits Success, Failure {}

// Record implementations
public record Success<T>(T data) implements ApiResult<T> {}
public record Failure<T>(String error) implements ApiResult<T> {}

// Exhaustive handling with pattern matching
public String processResult(ApiResult<String> result) {
    return switch (result) {
        case Success<String> s -> "Success: " + s.data();
        case Failure<String> f -> "Error: " + f.error();
        // Compiler enforces exhaustiveness - no default needed
    };
}
```

**Key Points**: Sealed interface ensures all result types are known at compile time. Pattern matching switch guarantees all cases are handled. Records provide immutable, concise implementations.

### Example 2: Data Projection Pattern for JPA

Minimal example showing separation between mutable JPA entity and immutable Record DTO:

```java
// Mutable JPA entity
@Entity
public class Customer {
    @Id private Long id;
    private String name;
    private String email;
    // Getters, setters, no-arg constructor
}

// Immutable Record DTO
public record CustomerDTO(Long id, String name, String email) {}

// Query projecting to Record
List<CustomerDTO> customers = em.createQuery(
    "SELECT c.id, c.name, c.email FROM Customer c", Object[].class
)
.setTupleTransformer((tuple, aliases) -> 
    new CustomerDTO((Long) tuple[0], (String) tuple[1], (String) tuple[2])
)
.getResultList();
```

**Key Points**: Entity remains mutable for JPA requirements. Record DTO provides immutable contract. Projection bypasses entity lifecycle for read-only operations. Clear separation of persistence model from application model.

## Error Handling

Guidelines for handling common errors:

- **Compilation Errors**: Sealed class violations (subclass not in permitted list) - ensure all permitted subclasses are listed and in correct package
- **Runtime Errors**: Record validation failures in compact constructor - ensure validation logic throws appropriate exceptions with clear messages
- **Pattern Matching**: Missing cases on sealed types - compiler enforces exhaustiveness, but ensure all permitted subtypes are handled
- **JPA Projection**: TupleTransformer type casting errors - ensure query column order matches Record component order and types

**Verification**: Run `mvn clean compile` or `gradle compileJava` to catch sealed hierarchy violations (missing permits) or non-exhaustive switch expressions immediately.

**Fallback Strategy**: If Records cannot be used for specific use case (e.g., complex JPA entity requirements), fall back to traditional mutable classes but maintain immutability principles where possible.

## Security and Guidelines

**CRITICAL**: Never hardcode sensitive information:
- ❌ No API keys, passwords, or tokens in code
- ❌ No credentials in SKILL.md or templates
- ✅ Use external credential management systems
- ✅ Route sensitive operations through secure channels

**Operational Constraints**:
- Records are immutable by design - cannot be modified after creation
- Sealed classes enforce compile-time type safety - runtime reflection may have limitations
- Pattern matching requires JDK 17+ - ensure target environment supports it

## Dependencies

This skill requires:
- `java>=17`: JDK 17 or later for Records, Sealed Classes, and Pattern Matching features

**Note**: For API-based deployments, JDK 17+ must be pre-installed in the execution environment. The skill cannot install JDK at runtime.

## Performance Considerations

- **Records**: Minimal memory overhead compared to traditional classes, automatic equals/hashCode optimization
- **Sealed Classes**: No runtime performance impact, compile-time type checking only
- **Pattern Matching**: Compiler optimizations for switch expressions, no reflection overhead
- **Stream API**: Lazy evaluation reduces memory usage, parallel streams for CPU-intensive operations
- **JPA Projections**: Significant performance improvement over full entity loading for read-only operations

## Related Resources

For extensive reference materials, see:
- JDK 17 JEP documentation: JEP 395 (Records), JEP 409 (Sealed Classes), JEP 406 (Pattern Matching)
- Java Language Specification for Records and Sealed Classes
- JPA/Hibernate documentation for TupleTransformer and projection patterns

## Notes

- **Migration Path**: For JDK 8/11 migrations, complete incremental upgrade: first to latest 2.x, remove deprecated APIs, then upgrade to 3.x/17
- **Preview Features**: Pattern Matching for switch (JEP 406) was preview in JDK 17, finalized in later versions - ensure target JDK version supports required features
- **Framework Compatibility**: Verify framework versions support JDK 17 features (e.g., Spring Boot 3.x requires JDK 17+)
- **Limitations**: Records cannot extend classes, cannot have instance fields beyond components, cannot be used as JPA entities
- **Future Enhancements**: Pattern Matching continues to evolve (record patterns, array patterns in later JDK versions)
