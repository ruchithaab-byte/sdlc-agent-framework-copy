# Linear Patterns Reference

This reference contains detailed configuration templates, anti-pattern definitions, and workaround strategies for the `implementing-linear-excellence` skill.

## 1. Organizational Patterns

### Heirloom Tomato Pattern
**Purpose**: Avoid symmetrical team sizing that creates fragmentation. Prioritize strategic differentiators.

**Configuration Template**:
```markdown
Core Team: [Name] - [Strategic differentiator]
- Headcount: [50%+ of total]
- Scope: [Wide, multiple surface areas]
- Key Trait: Owners of the "Crown Jewels"

Peripheral Team: [Name] - [Support function]
- Headcount: [Lean, minimal staffing]
- Scope: [Focused, non-differentiating]
- Key Trait: Efficiency-focused
```

## 2. Work Hierarchy Patterns

**Purpose**: Decouple scope (what we do) from time (when we do it).

**Hierarchy Definitions**:
| Level | Scope/Time | Duration | Purpose |
|-------|------------|----------|---------|
| **Initiative** | Scope | Quarters/Years | Strategic goals, executive visibility. |
| **Project** | Scope | Weeks/Months | Finite work with clear outcome. Can span multiple cycles. |
| **Cycle** | Time | 2-4 Weeks | Pacing & capacity. Auto-rollover enabled. NOT a release. |
| **Issue** | Scope | Days | Atomic unit. Single assignee. |

**Project Template**:
```markdown
Project: [Feature/Outcome]
- Owner: [Specific Lead]
- Target Date: [Approximate]
- Associated Initiative: [Strategic Goal]
- Status: Planned / In Progress / Paused / Completed / Canceled
```

## 3. Workflow & Assignment Patterns

### Single Assignee (DRI) Pattern
**Principle**: One assignee per issue ensures accountability.

**Workarounds for Collaboration**:
1.  **Sub-Issues Pattern**:
    *   Parent Issue: [Feature Name] (Assigned to: Lead)
    *   Sub-Issue 1: [Design] (Assigned to: Designer)
    *   Sub-Issue 2: [Frontend] (Assigned to: Dev)
2.  **Lead + Subscribers Pattern**:
    *   Assignee: Current active driver.
    *   Subscribers: All contributors.
    *   *Action*: Reassign as the "ball" passes to the next person.

### Triage Zero Pattern
**Protocol**:
*   **Gatekeeper**: Rotational role (weekly).
*   **Snooze**: Use `Shift+H` for items not immediately actionable but valuable.
*   **Decline**: Reject with comment.
*   **Accept**: Move to Cycle (active) or Backlog (later).

## 4. Anti-Pattern Catalog

### Jira-fication
*   **Signs**: Complex status workflows (QA Ready, UAT In Progress), granular permissions, required fields.
*   **Fix**: Simplify statuses to `Backlog` -> `In Progress` -> `In Review` -> `Done`. Trust over control.

### Backlog Hoard
*   **Signs**: 1000+ tickets in backlog, "we might need this", degraded search.
*   **Fix**: Archive everything older than 3 months. If it's important, it will come back.

### Shadow Work
*   **Signs**: "Busy" team but low velocity stats. Work happening in DMs/Slack.
*   **Fix**: "If it's not in Linear, it doesn't exist." Use "Create Issue from Slack".

### "Done" Misunderstanding
*   **Signs**: Tickets stuck in "In Progress" waiting for deployment.
*   **Fix**: "Done" = PR Merged/Engineer's work complete. Use "Released" automation or status for deployment tracking.

## 5. Workaround Library

| Limitation | Workaround |
|------------|------------|
| **Multiple Assignees** | Use **Sub-issues** or **Lead + Subscribers**. |
| **Reporting Gaps** | Use **Screenful** integration or **Airbyte** export to data warehouse. |
| **Cooldowns** | Create a manual cycle named "Cooldown" or use a specific Label. |
| **Dependencies** | Use "Blocking" / "Blocked By" relations (visual red icon). |

## 6. Integration Configurations

### GitHub
*   **Autolinking**: Ensure branch names contain `[ENG-123]`.
*   **Draft PRs**: Map Draft PR opening to "In Progress".
*   **Magic Words**: Use "Fixes ENG-123" in PR descriptions.

### Slack
*   **Create from Message**: Use the "Create Issue" action for bug reports.
*   **Notifications**: Route to specific `#team-feed` channels, not general channels.

