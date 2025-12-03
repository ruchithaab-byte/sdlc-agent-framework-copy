---
name: implementing-linear-excellence
description: Implements Linear operational excellence by applying proven patterns (Heirloom Tomato, work hierarchy decoupling) and workflow best practices. Covers workspace configuration, team structure, and migration from legacy tools while avoiding anti-patterns like Jira-fication. References detailed templates in resources/LINEAR_PATTERNS_REFERENCE.md.
version: 1.1.0
---

# Implementing Linear Excellence

## Overview

Implements Linear operational excellence by applying proven organizational patterns and workflow best practices. Validated by implementations at Plum HQ and Descript.

## When to Use

*   **Setup**: Configuring a new Linear workspace.
*   **Migration**: Moving from Jira/Asana to Linear.
*   **Optimization**: Fixing "Jira-fication" or "Backlog Hoards" in existing setups.
*   **Restructure**: Applying the Heirloom Tomato organizational model.

## Prerequisites

*   **Admin Access**: Required for workspace settings (Teams, Cycles, Workflow).
*   **Alignment**: Agreement on "Momentum over Reporting" philosophy.

## Execution Steps

### Step 1: Configure Organization (Heirloom Tomato Pattern)
Identify core differentiators and structure teams asymmetrically.

1.  **Analyze Strategy**: Identify which teams build "strategic differentiators" vs "table stakes".
2.  **Create Teams**:
    *   **Settings > Teams > Create Team**
    *   Apply the **Heirloom Tomato Pattern** (See `resources/LINEAR_PATTERNS_REFERENCE.md` Section 1).
    *   *Guidance*: Core teams get 50%+ headcount; peripheral teams are lean.

### Step 2: Configure Work Hierarchy
Decouple scope from time.

1.  **Define Hierarchy**:
    *   **Initiatives**: Settings > Account > Preferences > Enable Initiatives. Use for quarterly goals.
    *   **Projects**: Use for finite deliverables (weeks/months).
    *   **Cycles**: Settings > [Team] > Cycles. Enable Cycles.
2.  **Configuration**:
    *   Set Cycle duration to 2-4 weeks.
    *   **CRITICAL**: Enable "Auto-rollover" in Cycle settings to maintain momentum.
    *   *Ref*: See `resources/LINEAR_PATTERNS_REFERENCE.md` Section 2 for hierarchy definitions.

### Step 3: Configure Workflow & Statuses
Avoid "Jira-fication" by simplifying statuses.

1.  **Simplify Statuses**:
    *   **Settings > [Team] > Workflow**
    *   Standardize to 4-5 states: `Backlog` -> `In Progress` -> `In Review` -> `Done` -> `Canceled`.
    *   *Action*: Remove "QA Ready", "UAT", "Deployed" from the core workflow. Use Labels or Automations if needed.
2.  **Enforce DRI**:
    *   Educate team: One assignee per issue.
    *   Use **Sub-issues** for collaboration (See `resources/LINEAR_PATTERNS_REFERENCE.md` Section 3).

### Step 4: Implement Triage Zero
Set up the inbox workflow.

1.  **Enable Triage**:
    *   **Settings > [Team] > Triage**: Turn on "Triage".
2.  **Define Protocol**:
    *   Assign a weekly "Gatekeeper".
    *   Target: Inbox Zero daily.
    *   Use `Shift+H` (Snooze) liberally.

### Step 5: Master Navigation (Keyboard First)
Linear is designed for speed.

1.  **Core Shortcuts**:
    *   `Cmd+K`: Command Palette (Do everything).
    *   `C`: Create Issue.
    *   `G` then `I`: Go to Inbox.
    *   `G` then `T`: Go to Triage.
2.  **Action**: Run a training session where mouse usage is discouraged.

### Step 6: Apply Integrations
Reduce administrative overhead.

1.  **GitHub**:
    *   **Settings > Integrations > GitHub**.
    *   Enable "Autolink" and "Draft PR support".
    *   Map "Draft PR" -> "In Progress".
2.  **Slack**:
    *   **Settings > Integrations > Slack**.
    *   Configure "Personal Notifications".
    *   Set up channel routing (avoid general channels).

### Step 7: Anti-Pattern Check
Scan the workspace for regressions.

1.  **Check for Jira-fication**: Are there >7 statuses? Are there required fields? -> **Simplify**.
2.  **Check for Backlog Hoard**: Are there >500 items in Backlog? -> **Archive** (See `resources/LINEAR_PATTERNS_REFERENCE.md` Section 4).
3.  **Check for Shadow Work**: Is velocity flat? -> **Enforce logging**.

## Verification Checklist

- [ ] **Teams**: Asymmetric sizing applied (Heirloom Tomato).
- [ ] **Cycles**: Enabled with Auto-rollover turned ON.
- [ ] **Statuses**: Simplified to max 5 states per team.
- [ ] **Triage**: Enabled and clear Gatekeeper assigned.
- [ ] **Integrations**: GitHub PRs automatically move tickets to "In Progress".
- [ ] **Backlog**: Contains only actionable work (no hoard).

## Resources
*   `resources/LINEAR_PATTERNS_REFERENCE.md`: detailed templates and anti-pattern catalog.
