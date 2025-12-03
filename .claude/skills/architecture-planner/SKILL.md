---
name: architecture_planner
description: Generate comprehensive architecture plans and Architecture Decision Records (ADRs)
---

# Architecture Planner Skill

This skill provides patterns for creating system architecture plans and documenting key architectural decisions.

## When to Use This Skill

Use this skill when:
- Designing a new service or system
- Making significant architectural changes
- Documenting technology decisions
- Planning system integrations
- Creating technical specifications

## generate_architecture_plan

Creates a comprehensive architecture plan for a service or system.

### Architecture Plan Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<architecture_plan>
  <metadata>
    <project_name>Service Name</project_name>
    <version>1.0</version>
    <created_date>YYYY-MM-DD</created_date>
    <author>ArchGuard Agent</author>
  </metadata>

  <overview>
    <description>Brief description of the system</description>
    <goals>
      <goal>Primary business goal</goal>
      <goal>Technical goal</goal>
    </goals>
    <constraints>
      <constraint>Technical or business constraint</constraint>
    </constraints>
  </overview>

  <components>
    <component name="ComponentName">
      <type>service|library|database|queue</type>
      <responsibility>What this component does</responsibility>
      <technology>Technology stack</technology>
      <interfaces>
        <interface type="REST|gRPC|Event">Description</interface>
      </interfaces>
    </component>
  </components>

  <data_models>
    <entity name="EntityName">
      <fields>
        <field name="id" type="UUID" required="true"/>
        <field name="name" type="String" required="true"/>
      </fields>
      <relationships>
        <relationship type="hasMany" target="OtherEntity"/>
      </relationships>
    </entity>
  </data_models>

  <api_contracts>
    <endpoint path="/api/resource" method="POST">
      <description>Create a new resource</description>
      <request_body>JSON schema or description</request_body>
      <responses>
        <response status="201">Created successfully</response>
        <response status="400">Validation error</response>
      </responses>
    </endpoint>
  </api_contracts>

  <security>
    <authentication>OAuth2/JWT/API Key</authentication>
    <authorization>RBAC/ABAC description</authorization>
    <data_protection>Encryption requirements</data_protection>
  </security>

  <deployment>
    <environment>Kubernetes/Docker/Serverless</environment>
    <scaling>Horizontal/Vertical strategy</scaling>
    <monitoring>Observability approach</monitoring>
  </deployment>

  <dependencies>
    <dependency name="DependencyName" type="internal|external">
      <purpose>Why this dependency is needed</purpose>
      <version>Version constraint</version>
    </dependency>
  </dependencies>
</architecture_plan>
```

### Best Practices

1. **Start with business requirements** - Understand the problem before designing the solution
2. **Consider non-functional requirements** - Performance, scalability, security
3. **Document trade-offs** - Every decision has consequences
4. **Plan for evolution** - Systems change over time
5. **Include diagrams** - Visual representations aid understanding

## write_adr

Creates an Architecture Decision Record (ADR) to document a key decision.

### ADR Template

```markdown
# [Number]. [Title]

Date: YYYY-MM-DD

## Status

Proposed | Accepted | Deprecated | Superseded by [ADR-XXX]

## Context

Describe the issue motivating this decision. What is the problem?
What are the forces at play (technical, political, social)?

## Decision

Describe our response to these forces. State the decision clearly.
Use active voice: "We will..."

## Consequences

Describe the resulting context after applying the decision.
What becomes easier or harder to do because of this change?

### Positive
- Benefit 1
- Benefit 2

### Negative
- Trade-off 1
- Trade-off 2

### Neutral
- Side effect 1

## Alternatives Considered

### Alternative 1: [Name]
- Description
- Pros: ...
- Cons: ...
- Why rejected: ...

### Alternative 2: [Name]
- Description
- Pros: ...
- Cons: ...
- Why rejected: ...

## References

- Link to relevant documentation
- Link to discussion thread
```

### ADR Naming Convention

Save ADRs in `docs/adr/` with format: `NNNN-kebab-case-title.md`

Examples:
- `0001-use-postgresql-for-primary-storage.md`
- `0002-adopt-event-sourcing-pattern.md`
- `0003-select-kong-as-api-gateway.md`

### When to Write an ADR

Write an ADR when:
- Choosing between competing technologies
- Defining architectural patterns
- Making security decisions
- Changing existing patterns
- Decisions that are hard to reverse

## Integration with SDLC Agents

### ArchGuard Agent
Primary user of this skill. Creates architecture plans and ADRs based on PRDs.

### CodeCraft Agent
References architecture plans when implementing features.

### QualityGuard Agent
Validates implementations against architectural decisions.

## Related Skills

- `code_execution_suite` - For verifying implementations
- `linear-integration` - For creating architecture tasks
- `implementing-kong-gateway` - Kong-specific architecture patterns
- `implementing-kuma-production` - Service mesh patterns
