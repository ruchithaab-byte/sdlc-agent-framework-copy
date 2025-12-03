---
name: linear-integration
description: Create and manage Linear epics, issues, sprints, and project tracking
---

# Linear Integration Skill

This skill provides patterns for integrating with Linear for project and issue management within the SDLC workflow.

## When to Use This Skill

Use this skill when:
- Creating epics from PRDs
- Breaking down features into issues
- Planning sprints
- Tracking issue status
- Linking code changes to issues

## Prerequisites

Before using Linear integration:

1. **Set LINEAR_API_KEY** environment variable
2. **Set LINEAR_TEAM_ID** environment variable
3. **Verify API access** with the Linear MCP server

## linear_create_epic

Creates an epic (parent issue or project) in Linear to track a feature.

### When to Create an Epic

Create an epic when:
- Starting a new feature from a PRD
- Grouping related issues together
- Tracking a multi-sprint initiative

### Epic Structure

```markdown
## Epic: [Feature Name]

**Description**: Brief description of the feature and its value

**Goals**:
- Goal 1
- Goal 2

**Success Metrics**:
- Metric 1
- Metric 2

**Dependencies**:
- Dependency 1
- Dependency 2

**Estimated Duration**: X sprints

**Team**: Team name
```

### Best Practices

1. **Use clear titles** - "User Authentication with OAuth2" not "Auth stuff"
2. **Include acceptance criteria** - Define what "done" means
3. **Link to PRD** - Reference the source requirements
4. **Set priority** - P1/P2/P3 based on business value
5. **Add labels** - Categorize for filtering

## linear_create_issue

Creates an issue (task) under an epic or standalone.

### Issue Types

- **Feature** - New functionality
- **Bug** - Defect fix
- **Improvement** - Enhancement to existing
- **Chore** - Maintenance, refactoring
- **Spike** - Research/investigation

### Issue Template

```markdown
## Issue: [Action-oriented Title]

**Type**: Feature | Bug | Improvement | Chore | Spike

**Description**: 
What needs to be done and why.

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Technical Notes**:
- Implementation hint 1
- Implementation hint 2

**Parent Epic**: #EPIC-ID

**Estimate**: 1-8 story points
```

### Estimation Guidelines

| Points | Effort | Example |
|--------|--------|---------|
| 1 | Few hours | Fix typo, update config |
| 2 | Half day | Simple bug fix |
| 3 | 1 day | Small feature |
| 5 | 2-3 days | Medium feature |
| 8 | 1 week | Large feature |
| 13+ | Split it | Too big, break down |

## linear_sprint_planning

Plans and configures a sprint with dates and capacity.

### Sprint Structure

```markdown
## Sprint: [Sprint Name]

**Duration**: [Start Date] - [End Date] (2 weeks typical)

**Goals**:
1. Primary goal
2. Secondary goal

**Capacity**:
- Team size: X developers
- Available days: Y
- Total story points: Z

**Committed Issues**:
- Issue 1 (3 pts)
- Issue 2 (5 pts)
- Issue 3 (2 pts)

**Total Committed**: 10 pts
```

### Sprint Planning Workflow

1. **Review backlog** - Prioritize issues
2. **Estimate unestimated** - Size new issues
3. **Calculate capacity** - Account for meetings, PTO
4. **Commit issues** - Pull in based on capacity
5. **Identify dependencies** - Flag blockers
6. **Set sprint goal** - Define success

## linear_update_status

Updates issue status through the workflow.

### Common Status Transitions

| From | To | When |
|------|----|------|
| Backlog | Todo | Issue is prioritized for sprint |
| Todo | In Progress | Developer starts work |
| In Progress | In Review | Code submitted for review |
| In Review | Done | Code merged and deployed |
| Any | Blocked | External dependency blocking |
| Any | Canceled | No longer needed |

### Status Update Best Practices

1. **Update promptly** - Status should reflect current reality
2. **Add comments** - Explain why status changed
3. **Link PRs** - Connect code to issues
4. **Move blockers** - Don't let issues stall

## Workflow Integration

### PRD to Epic Flow

```
ProductSpec Agent                Linear
      |                            |
      |-- Creates PRD ------------>|
      |                            |
      |-- linear_create_epic ----->|-- Epic created
      |                            |
SprintMaster Agent                 |
      |                            |
      |-- linear_create_issue ---->|-- Issues created
      |                            |
      |-- linear_sprint_planning ->|-- Sprint configured
      |                            |
CodeCraft Agent                    |
      |                            |
      |-- linear_update_status --->|-- Status: In Progress
      |                            |
      |-- [implements code] -------|
      |                            |
      |-- linear_update_status --->|-- Status: Done
```

### Linking Code to Issues

Include issue ID in commit messages:
```bash
git commit -m "Implement OAuth2 login flow [LIN-123]"
```

Include issue ID in PR titles:
```
[LIN-123] feat: Add OAuth2 login flow
```

## Environment Variables

```bash
# Required
LINEAR_API_KEY=lin_api_xxx
LINEAR_TEAM_ID=TEAM-xxx

# Optional
LINEAR_PROJECT_ID=project_xxx
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check LINEAR_API_KEY |
| 404 Not Found | Invalid team/issue ID | Verify IDs exist |
| 422 Validation | Missing required fields | Check request body |
| 429 Rate Limited | Too many requests | Implement backoff |

## Integration with SDLC Agents

### ProductSpec Agent
Creates epics when generating PRDs.

### SprintMaster Agent
Primary user - creates issues and plans sprints.

### CodeCraft Agent
Updates status as code is implemented.

### QualityGuard Agent
Updates status when review is complete.

## Related Skills

- `architecture-planner` - For documenting decisions in ADRs
- `code_execution_suite` - For verifying implementations
- `implementing-linear-excellence` - Advanced Linear patterns
