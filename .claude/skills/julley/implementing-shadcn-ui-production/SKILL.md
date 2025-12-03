---
name: implementing-shadcn-ui-production
description: Implements shadcn/ui components for production systems. Covers atomic composition, CVA standardization, advanced theming (dark mode), and component governance. Use when building UI systems, customizing components, or setting up design tokens.
version: 1.0.0
dependencies:
  - react>=18.0.0
  - typescript>=5.0.0
  - tailwindcss>=3.0.0
  - class-variance-authority>=0.7.0
  - next-themes>=0.2.0
---

# Implementing shadcn/ui Production

## Overview

shadcn/ui represents a fundamental architectural shift from traditional component library models to an open code distribution system. Components are distributed as TypeScript/React source code that developers copy directly into their projects, transforming them from external dependencies into fully owned internal assets. This architecture provides complete transparency, eliminates vendor lock-in, enables unrestricted customization, and positions components as inherently AI-ready for analysis and improvement. The core trade-off is the transfer of maintenance responsibility from library maintainers to the development team, requiring dedicated internal maintenance protocols to manage component lifecycle, security patches, and dependency updates.

## When to Use

Use this skill when:
- Building production UI systems with custom design requirements
- Implementing design system consistency across applications
- Setting up dark mode and custom theming systems
- Managing component lifecycle and upstream synchronization
- Avoiding common integration pitfalls (SSR hydration, Tailwind conflicts, accessibility issues)
- Customizing components beyond standard library capabilities
- Establishing component governance and maintenance protocols

**Input format**: Next.js/React project, Tailwind CSS configured, understanding of component composition, access to shadcn/ui CLI
**Expected output**: Production-ready shadcn/ui implementation following proven patterns, best practices applied, workarounds implemented, anti-patterns avoided

## Prerequisites

Before using this skill, ensure:
- Next.js/React project setup with App Router (if using Next.js)
- Tailwind CSS configured with utility-first approach
- Understanding of React component composition patterns
- Access to shadcn/ui CLI (`npx shadcn@latest`)
- TypeScript configuration for type safety
- Design system requirements and custom theming needs defined

## Execution Steps

### Step 1: Atomic Composition Pattern

Component composition is the fundamental mechanism for creating complex user interfaces while promoting reusability and simplifying maintenance. shadcn/ui components, built on Radix primitives, are inherently modular, making them ideal for integration into new contexts.

**Pattern**: Use base components as atomic units for business composites
**Best Practice**: Combine primitives (Button, Card) into higher-level structures (MetricCard, Dashboard widgets)
**Anti-Pattern**: Over-nesting components, prop drilling through multiple layers

**Composite Component Template**:
See [TEMPLATES.md](TEMPLATES.md) for the `MetricCard` example.

**State Management Best Practice**: Avoid prop drilling by using React Context or external state managers (Zustand, Redux) for shared state across deep component hierarchies.

### Step 2: CVA Standardization Pattern

Any component created or significantly modified within the application must conform to design system consistency pillars: Visual, Behavioral, Accessibility, Theming, and Developer Experience. The central tool for enforcing this consistency is class-variance-authority (CVA).

**Pattern**: Use CVA for type-safe component variants
**Best Practice**: All custom components must use CVA for variant definition
**Anti-Pattern**: Hardcoded styles bypassing CVA, breaking theme-aware implementation

**CVA Variant Template**:
See [TEMPLATES.md](TEMPLATES.md) for the CVA variant structure.

**Critical**: CVA ensures components respond reliably to global theme changes (dark mode, theme switching). Bypassing CVA with hardcoded styles breaks theme awareness.

### Step 3: Advanced Theming Pattern

Effective theming is crucial for production systems, especially concerning dark mode implementation and custom brand colors. Dark mode is managed through next-themes provider with class strategy.

**Pattern**: Dark mode via next-themes with class strategy
**Best Practice**: Dual CSS variable declaration (:root for light mode, .dark for dark mode)
**Anti-Pattern**: Hardcoded colors, missing dark mode variables, breaking theme system

**Theme Token Extension Workflow**:

1.  **Define Variables**: Declare CSS variables in `app/globals.css`.
2.  **Map to Utilities**: Use `@theme inline` to map to Tailwind.
3.  **Consumption**: Use the utility classes in components.

See [TEMPLATES.md](TEMPLATES.md) for the detailed CSS template.

**Critical**: The @theme inline directive maps CSS custom properties to Tailwind utility classes, making new colors seamlessly available across all components.

## Common Patterns

### Pattern 1: Atomic Composition

Build complex business-specific components by composing shadcn/ui primitives as atomic units. This ensures core styling and accessibility logic are inherited from battle-tested primitives while assembly dictates unique features.

**When to apply**: Creating business-specific components (dashboards, metric cards, structured layouts)
**Code template**: Combine Button + Card primitives into MetricCard composite

### Pattern 2: CVA Standardization

Enforce design system consistency by mandating class-variance-authority usage for all custom or modified components. CVA centralizes variant definitions and prevents component layer decoupling from global styling variables.

**When to apply**: All custom components, any component modifications, variant definitions
**Code template**: Define variants with CVA, extend VariantProps for type safety

### Pattern 3: Advanced Theming

Implement dark mode and custom design tokens using next-themes provider with dual CSS variable declaration and @theme inline directive for Tailwind utility mapping.

**When to apply**: Theming setup, dark mode implementation, custom color/brand token introduction
**Code template**: 3-step workflow (variables → @theme → usage)

## Best Practices

- **Component Composition**: Avoid over-nesting (excessive layers impact rendering performance). Use React Context or external state managers (Zustand, Redux) for shared state to prevent prop drilling.
- **CVA Mandatory**: All custom components must use CVA for variant definitions. This ensures theme-aware implementation and maintains design system integrity.
- **Theme Variables**: Always dual-declare CSS variables (:root for light mode, .dark for dark mode). Use @theme inline directive to map variables to Tailwind utilities.
- **Maintenance Protocol**: Establish explicit Component Governance Policy categorizing components by modification level (L1: Unmodified, L3: Heavily Customized). Dedicate recurring engineering cycles for proactive maintenance and upstream synchronization.
- **Accessibility**: Mandatory Axe testing for all composite components. Verify correct ARIA attribute usage, intuitive keyboard navigation, and proper semantic HTML structure.

## Workarounds

### Workaround 1: Controlled Upstream Synchronization

**When**: Component maintenance and updates needed, security patches available, dependency updates required

**How**: Use `npx shadcn@latest diff [component]` to visualize line-by-line comparison between local and upstream versions. For batch checking, implement automated script:

```bash
# Batch diffing script
for file in components/ui/*.tsx; do 
  npx shadcn@latest diff $(basename "$file" .tsx); 
done
```

If update required, overwrite using `npx shadcn@latest add -y -o [component]`, then conduct code review to re-implement customizations on updated source.

**Trade-off**: Manual merge process requires dedicated engineering time. Maintenance debt increases with customization level.

### Workaround 2: Monorepo Adoption

**When**: Multiple applications sharing components, large organizations managing multiple codebases

**How**: Use native monorepo support (Next.js with Turborepo). Install components into shared workspace package (`packages/ui`). CLI handles path resolution automatically:

```typescript
// apps/web imports from shared package
import { Button } from "@workspace/ui/components/button";
```

**Trade-off**: Centralized maintenance creates single source of truth but requires coordinated updates across dependent applications.

### Workaround 3: Managed Internal Library

**When**: Extreme scaling scenarios, distributing highly customized components across separate repositories, sharing with external teams

**How**: Use tooling layer (Bit) to treat customized components as versionable, published assets consumed via package manager. Source code remains owned and modifiable internally.

**Trade-off**: Reintroduces library management complexity while retaining customization flexibility.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Maintenance Debt Trap

**Issue**: Neglecting upstream component updates leads to security vulnerabilities, accessibility regressions, and dependency conflicts. Components diverge from upstream, making future updates increasingly difficult.

**Detection**: Components not synced for 3+ months, security advisories for underlying dependencies (Radix), accessibility issues in updated upstream versions

**Resolution**: Implement weekly diff workflow using `npx shadcn@latest diff`. Establish Component Governance Policy with categorization (L1: Unmodified, L3: Heavily Customized). Dedicate recurring engineering cycles for L3 component maintenance.

**Prevention**: Categorize all components by modification level. Schedule proactive maintenance reviews. Monitor upstream repository for security fixes and critical patches.

### Anti-Pattern 2: SSR Hydration Errors

**Issue**: Client-side logic, hooks, or state management initiated incorrectly within Server Components causes mismatch between server-rendered HTML and client-side JavaScript during hydration.

**Detection**: Hydration mismatch errors in console, "Text content does not match" warnings, component state inconsistencies

**Resolution**: Strict adherence to Server/Client component separation. Stateful components must use 'use client' directive. Verify initial props passed from server to client are stable and consistent.

**Prevention**: Verify Server/Client component boundaries. Never use browser APIs (window, localStorage) in Server Components. Ensure props are serializable (no functions, Date objects, class instances).

### Anti-Pattern 3: Tailwind Typography Conflicts

**Issue**: Hardcoded pixel or rem values replace CSS variables, breaking theme system. Results in inconsistent heading hierarchies, layout breakage, and failure to respond to theme changes.

**Detection**: Inconsistent font scaling, layout breakage, components not responding to theme changes, hardcoded values in component styles

**Resolution**: Use Tailwind's @apply rules for reusable classes. Adjust font scales exclusively through CSS custom properties. Never replace CSS variables with hardcoded values.

**Prevention**: Always use CSS custom properties for typography. Use @apply rules for consistency. Verify components respond to theme variable changes.

### Anti-Pattern 4: Accessibility Regression

**Issue**: Missing ARIA attributes, broken keyboard navigation, improper focus traps compromise accessibility. Components built on accessible Radix primitives can be compromised through misuse.

**Detection**: Axe testing failures, keyboard navigation issues, missing accessible names for interactive elements (modals, dialogs), focus trap failures

**Resolution**: Mandatory accessibility checks (automated Axe testing) for all composite components. Verify correct ARIA attribute usage, intuitive keyboard navigation flow, proper semantic HTML structure.

**Prevention**: Integrate Axe testing into development workflow. Test all composites for accessibility. Verify focus traps have robust fallbacks for keyboard users.

## Code Templates

For reusable component patterns, CVA configurations, and theming setups, see [TEMPLATES.md](TEMPLATES.md).

## Real-World Examples

For complex implementation examples like Enterprise Data Tables and Custom Utilities, see [EXAMPLES.md](EXAMPLES.md).

## Error Handling

- **Component Installation Failures**: Verify Tailwind configuration, check component dependencies, ensure CLI version compatibility
- **Theme Variable Mapping Errors**: Validate @theme inline directive syntax, verify CSS variable names match Tailwind utility mapping
- **CVA Type Errors**: Ensure VariantProps extension, verify variant definitions match component usage, check TypeScript configuration
- **Hydration Mismatch Resolution**: Verify 'use client' directives, check prop serialization, ensure stable initial props from server

## Security and Guidelines

**CRITICAL**: Never hardcode sensitive information:
- ❌ No API keys, passwords, or tokens in component code
- ❌ No credentials in SKILL.md or templates
- ✅ Use external credential management systems
- ✅ Route sensitive operations through secure channels

**Component Ownership**: Source code is fully owned, transferring security responsibility to development team. Regular security patch monitoring required. Implement Component Governance Policy for security update tracking.

## Performance Considerations

- **Bundle Size Optimization**: Only copy required components into project. shadcn/ui architecture naturally promotes minimalism - unused components don't affect bundle size.
- **Theme Variable Performance**: CSS custom properties (CSS variables) provide efficient theming without JavaScript overhead. Theme switching is performant.
- **Component Composition Performance**: Avoid over-nesting components. Excessive nested layers negatively impact rendering performance. Use React Context or external state managers to prevent prop drilling without adding render overhead.

## Related Resources

For extensive reference materials, see:
- shadcn/ui official documentation: https://ui.shadcn.com
- Radix UI primitives: https://www.radix-ui.com
- class-variance-authority: https://cva.style
- next-themes: https://github.com/pacocoursey/next-themes

## Notes

- shadcn/ui is not distributed as NPM package - components are copied as source code
- Maintenance responsibility transfers to development team - requires dedicated protocols
- Components are AI-ready due to exposed code structure and flat-file schema
- Production suitability validated by adoption in high-scale projects (x.ai, openai.com, vercel.app)
- Monorepo support available in latest CLI versions for shared component management
