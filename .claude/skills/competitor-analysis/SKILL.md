---
name: competitor_analysis
description: Research and analyze comparable product implementations and market solutions
---

# Competitor Analysis Skill

This skill provides patterns for researching and analyzing how other products solve similar problems, helping inform architectural and design decisions.

## When to Use This Skill

Use this skill when:
- Starting a new feature or product
- Evaluating different implementation approaches
- Understanding market standards and best practices
- Making build vs. buy decisions
- Justifying architectural choices

## competitor_analysis

Research comparable implementations to inform product decisions.

### Research Framework

#### 1. Define the Problem Space

Before researching, clearly define:
- What problem are we solving?
- Who is the target user?
- What are the key requirements?
- What are the constraints?

#### 2. Identify Competitors

Categories of competitors:
- **Direct competitors** - Same market, same solution
- **Indirect competitors** - Different solution, same problem
- **Potential competitors** - Could enter the space
- **Open source alternatives** - Community solutions

#### 3. Analyze Each Competitor

For each competitor, document:

```markdown
## Competitor: [Name]

### Overview
- **Product**: Name and description
- **Target Market**: Who they serve
- **Pricing Model**: Free/Freemium/Paid/Enterprise

### Features
| Feature | Our Need | Their Solution | Gap Analysis |
|---------|----------|----------------|--------------|
| Auth    | OAuth2   | Custom + Social| Need OAuth2  |
| API     | REST     | GraphQL        | Consider both|

### Technical Architecture (if known)
- **Frontend**: Technology stack
- **Backend**: Technology stack
- **Database**: Storage solutions
- **Infrastructure**: Cloud/On-prem

### Strengths
- Strength 1
- Strength 2

### Weaknesses
- Weakness 1
- Weakness 2

### Lessons Learned
- What can we learn from their approach?
- What should we avoid?
```

### Research Sources

#### Public Information
- Product documentation
- Developer blogs
- GitHub repositories (if open source)
- API documentation
- Status pages (for infrastructure clues)
- Job postings (technology hints)

#### Technical Analysis
- Network requests (browser dev tools)
- Response headers
- Error messages
- Performance metrics

#### Community Insights
- HackerNews discussions
- Reddit threads
- Stack Overflow questions
- Twitter/X discussions
- Conference talks

### Analysis Deliverables

#### Competitive Matrix

```markdown
| Feature              | Us (Planned) | Competitor A | Competitor B | Competitor C |
|---------------------|--------------|--------------|--------------|--------------|
| SSO/SAML            | ✅ Planned   | ✅ Yes       | ❌ No        | ✅ Yes       |
| API Rate Limiting   | ✅ Planned   | ✅ Yes       | ✅ Yes       | ❌ No        |
| Webhook Support     | ✅ Planned   | ✅ Yes       | ✅ Yes       | ✅ Yes       |
| Self-Hosting        | ❌ No        | ❌ No        | ✅ Yes       | ❌ No        |
| Custom Branding     | ✅ Planned   | 💰 Enterprise| ✅ Yes       | 💰 Paid      |
```

#### Technology Comparison

```markdown
| Aspect           | Our Choice    | Competitor A   | Industry Trend |
|-----------------|---------------|----------------|----------------|
| Frontend        | React + Next  | Vue.js         | React dominant |
| Backend         | Spring Boot   | Node.js        | Mixed          |
| Database        | PostgreSQL    | MongoDB        | PostgreSQL up  |
| API Style       | REST + gRPC   | GraphQL        | REST common    |
| Auth            | OAuth2/OIDC   | Custom JWT     | OAuth2 standard|
```

### Decision Documentation

Use findings to support Architecture Decision Records (ADRs):

```markdown
## Context
We evaluated [competitors] to determine the best approach for [feature].

## Research Findings
- Competitor A uses [approach] which [pros/cons]
- Competitor B uses [approach] which [pros/cons]
- Industry trend is toward [pattern]

## Decision
Based on competitor analysis, we will [decision] because:
1. [Reason based on research]
2. [Reason based on research]

## Alternatives Considered
- [Alternative from competitor] - rejected because [reason]
```

## Integration with SDLC Agents

### ProductSpec Agent
Uses this skill during requirements analysis to understand market context.

### ArchGuard Agent
Uses competitive analysis to inform architectural decisions and ADRs.

### QualityGuard Agent
References competitive standards when evaluating quality benchmarks.

## Best Practices

1. **Focus on principles, not copy** - Learn from approaches, don't clone features
2. **Document sources** - Track where information came from
3. **Update regularly** - Markets change, refresh analysis periodically
4. **Consider context** - What works for them may not work for you
5. **Look at failures** - Learn from what didn't work too

## Related Skills

- `architecture-planner` - For documenting decisions based on research
- `linear-integration` - For creating research tasks
- `mintlify-documentation` - For researching via Mintlify docs
