---
name: implementing-nextjs-14-production
description: Implements Next.js 14 App Router production patterns (Server Components, Server Actions, Caching, Routing). Use when building Next.js apps, setting up architecture, or deploying to production.
version: 1.0.0
dependencies:
  - next>=14.0.0
  - react>=18.0.0
  - zod>=3.0.0
---

# Implementing Next.js 14 Production

Follow this workflow to implement production-ready Next.js 14 features using App Router.

## Implementation Workflow

Copy this checklist and track your progress:

```markdown
Feature Implementation Progress:
- [ ] Step 1: Component Architecture (Server vs Client)
- [ ] Step 2: Data Mutations (Server Actions)
- [ ] Step 3: Caching Strategy
- [ ] Step 4: Routing & Layouts
- [ ] Step 5: Verification
```

### Step 1: Component Architecture
Determine component type and data fetching strategy.
- **Default**: Use Server Components for data fetching.
- **Interactive**: Use Client Components only for interactivity (`use client`).
- **Composition**: Interleave Client Components with Server Component children.
- **Reference**: [patterns/server-components.md](patterns/server-components.md)

### Step 2: Data Mutations
Implement `use server` actions for form submissions and mutations.
- **Validation**: MUST use Zod for input validation.
- **Auth**: MUST verify user session/permissions.
- **Reference**: [patterns/server-actions.md](patterns/server-actions.md)

### Step 3: Caching Strategy
Define revalidation triggers to ensure data consistency.
- **Mutations**: Use `revalidatePath` and `updateTag`.
- **Fetch**: Add `next: { tags: [...] }` to fetch calls.
- **Reference**: [patterns/caching.md](patterns/caching.md)

### Step 4: Routing & Layouts
Configure advanced routing if needed.
- **Parallel**: Use slots (`@slot`) for independent loading.
- **Intercepting**: Use `(.)` for modals.
- **Reference**: [patterns/routing.md](patterns/routing.md)

### Step 5: Verification
Verify against anti-patterns:
- [ ] No `window`/`localStorage` in Server Components?
- [ ] No direct Server Component imports in Client Component modules?
- [ ] All props passing to Client Components are serializable?
- [ ] Server Actions validting all inputs?
- [ ] `use client` directive present on interactive components?

## Quick Reference: Anti-Patterns

1.  **Direct SC Import into CC**: Violates isolation. Use children prop.
2.  **Non-Serializable Props**: Functions/Dates cause hydration errors. Serialize first.
3.  **Server Actions for Reads**: Inefficient. Use SC with fetch.
4.  **Missing Validation**: Security risk. Always validate inputs.
5.  **Local Cache in Multi-Replica**: Inconsistent data. Use Redis/S3.

## Additional Patterns

- **Middleware**: Auth and rewrites -> [patterns/middleware.md](patterns/middleware.md)
- **Deployment**: PPR and config -> [patterns/deployment.md](patterns/deployment.md)
