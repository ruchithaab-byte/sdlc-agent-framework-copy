---
name: implementing-react-18-architecture
description: Implements React 18 scalable architecture by applying concurrent rendering patterns (useTransition, useDeferredValue, createRoot), component composition (Custom Hooks, Compound Components, Atomic Design), state management (local colocation, Context for static data, Zustand/React Query for dynamic data), performance optimization (strategic memoization, code splitting), implementing workarounds (functional state updates, component definition outside render), and avoiding anti-patterns (legacy ReactDOM.render, business logic in Atoms, Context for high-frequency updates, stale closures, inline component creation, prop drilling, premature memoization). Use when building scalable React 18 applications, implementing concurrent features, setting up component architecture, managing state, optimizing performance, or avoiding common React pitfalls.
version: 1.0.0
dependencies:
  - react>=18.3.1
  - typescript>=5.0.0
---

# Implementing React 18 Architecture

## Overview

React 18 introduces Concurrent Rendering through a sophisticated update scheduler that allows React to interrupt and resume rendering tasks, improving UX and responsiveness. This skill provides architectural patterns for building scalable React 18 applications, emphasizing component taxonomy (Atomic Design), state management strategies (local, global, server state separation), performance optimization (memoization, code splitting), and critical anti-pattern avoidance. The architecture prioritizes discipline over complexity, ensuring state granularity, proper colocation, and strategic use of concurrent hooks as a performance optimization layer.

## When to Use

Use this skill when:
- Building scalable React 18 applications requiring architectural discipline
- Implementing concurrent features (useTransition, useDeferredValue)
- Setting up component architecture following Atomic Design principles
- Managing state across local, global, and server state categories
- Optimizing performance with strategic memoization and code splitting
- Avoiding common React pitfalls (stale closures, remounting, prop drilling, Context misuse)
- Implementing component composition patterns (Custom Hooks, Compound Components)
- Setting up error boundaries, portals, and form management

**Input format**: React 18.3.1+ project, TypeScript configuration, understanding of hooks and component lifecycle, modern build system (Vite/Next.js)

**Expected output**: Production-ready React 18 implementation following proven patterns, best practices applied, workarounds implemented, anti-patterns avoided

## Prerequisites

Before using this skill, ensure:
- React 18.3.1+ project setup
- TypeScript configuration for type safety
- Understanding of React hooks and component lifecycle
- Modern build system (Vite or Next.js) for optimized bundle outputs
- Access to state management libraries (Zustand, React Query) if needed

## Implementation Workflow

Copy this checklist to track your progress:

```markdown
- [ ] Step 1: Configure Root (createRoot) and Concurrent Features
- [ ] Step 2: Establish Component Architecture (Atomic Design)
- [ ] Step 3: Implement Composition Patterns (Hooks, Compound Components)
- [ ] Step 4: Define State Management Strategy (Local, Global, Server)
- [ ] Step 5: Implement Server State Management (React Query/RTK Query)
- [ ] Step 6: Apply Performance Optimizations (Memoization, Splitting)
- [ ] Step 7: Verify Error Handling and UX Patterns
- [ ] Step 8: Review against Anti-Patterns
```

## Detailed Resources

### Code Templates
For production-ready templates including Functional Components, Context Providers, Custom Hooks, and Concurrent Features:
**👉 See [TEMPLATES.md](TEMPLATES.md)**

### Anti-Patterns & Workarounds
To avoid common pitfalls like legacy rendering, state lifting, and stale closures:
**👉 See [ANTI_PATTERNS.md](ANTI_PATTERNS.md)**

### Real-World Examples
For complex implementations like Deferred Search and Compound Tabs:
**👉 See [EXAMPLES.md](EXAMPLES.md)**

## Execution Steps & Best Practices

### Step 1: Concurrent Rendering Patterns
- **createRoot**: Always initialize with `createRoot` (see [ANTI_PATTERNS.md](ANTI_PATTERNS.md) #1).
- **useTransition**: Wrap state updates that can be deferred (non-urgent) in `startTransition`.
- **useDeferredValue**: Defer heavy rendering tasks linked to fast-changing inputs.

### Step 2: Component Architecture (Atomic Design)
- **Hierarchy**: Atoms -> Molecules -> Organisms -> Templates -> Pages.
- **Rule**: Atoms must be purely presentational (see [ANTI_PATTERNS.md](ANTI_PATTERNS.md) #2).
- **Colocation**: Keep related files close; state in the lowest common ancestor.

### Step 3: Component Composition Patterns
- **Custom Hooks**: Extract stateful logic to decouple it from the view layer (see [TEMPLATES.md](TEMPLATES.md) #3).
- **Compound Components**: Use Context locally for implicit state sharing (see [EXAMPLES.md](EXAMPLES.md) #2).
- **Avoid**: Wrapper hell (HOC nesting) - prefer hooks.

### Step 4: State Management Strategy
- **Local**: `useState`, `useReducer` (colocate!).
- **Global**: `Context` for static/rarely-changing data (Auth, Theme).
- **High-Frequency**: `Zustand`/`Jotai` for frequent updates to avoid re-renders (see [ANTI_PATTERNS.md](ANTI_PATTERNS.md) #4).

### Step 5: Server State Management
- **Rule**: Use specialized libraries (React Query, RTK Query) over `useEffect`.
- **Benefit**: Automatic caching, invalidation, and error handling.

### Step 6: Performance Optimization
- **Memoization**: Only memoize expensive computations or stable function references (see [ANTI_PATTERNS.md](ANTI_PATTERNS.md) #8).
- **Code Splitting**: Use `React.lazy` and `Suspense` for heavy components or routes.

### Step 7: Error Handling
- **Error Boundaries**: Must be Class Components (see [TEMPLATES.md](TEMPLATES.md) #9).
- **Portals**: Use for Modals/Dialogs to escape stacking contexts.

## Security and Guidelines

**CRITICAL**: Never hardcode sensitive information:
- ❌ No API keys, passwords, or tokens in code
- ❌ No credentials in SKILL.md or scripts
- ✅ Use environment variables or secure vaults
- ✅ Route sensitive operations through secure channels

**Operational Constraints**:
- TypeScript strict mode required for type safety
- All components must handle error states gracefully
- Server Actions must include validation and authorization
- Performance budgets should be monitored for large applications

## Dependencies

This skill requires the following packages (listed in frontmatter):
- `react>=18.3.1`: React 18 with concurrent rendering support
- `typescript>=5.0.0`: TypeScript for type safety

**Optional Dependencies** (for specific patterns):
- `@tanstack/react-query`: Server state management
- `zustand`: Global state management for high-frequency updates
- `react-hook-form`: High-performance form management
- `class-variance-authority`: Component variant management

## Performance Considerations

- **Memoization Strategy**: Only memoize expensive computations (complex filtering, sorting, transformations) and stable function references passed to memoized components.
- **Code Splitting**: Lazy load feature components and large dependencies. Use Suspense boundaries strategically to improve perceived performance.
- **State Colocation**: Keep state as local as possible. Only lift state when truly necessary for sharing across distant components.
- **Concurrent Hooks**: Use useTransition and useDeferredValue as performance optimization layer, not replacement for proper state management.
- **Bundle Size**: Monitor bundle size. Use dynamic imports for heavy libraries. Consider tree-shaking opportunities.

## Related Resources

For extensive reference materials, see:
- React 18 Documentation: https://react.dev
- React Query Documentation: https://tanstack.com/query
- Zustand Documentation: https://zustand-demo.pmnd.rs
- React Hook Form Documentation: https://react-hook-form.com
