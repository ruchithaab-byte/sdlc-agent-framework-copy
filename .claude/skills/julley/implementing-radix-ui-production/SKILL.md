---
name: implementing-radix-ui-production
description: Implements Radix UI primitives using architectural patterns (asChild composition, component abstraction), applying best practices (mandatory prop spreading, ref forwarding, portal patterns), and avoiding anti-patterns. Use when building accessible UI components, integrating with design systems, or managing portals.
version: 1.0.1
dependencies:
  - react>=18.0.0
  - typescript>=5.0.0
  - "@radix-ui/react-primitive>=1.0.0"
  - tailwindcss>=3.0.0
---

# Implementing Radix UI Production

## Overview

Implements production-ready Radix UI components by strictly following architectural patterns for composition, accessibility, and styling. Focuses on the `asChild` pattern, component abstraction, and state-driven styling.

**See also**:
- **Templates**: [templates/TEMPLATES.md](templates/TEMPLATES.md)
- **Examples**: [templates/EXAMPLES.md](templates/EXAMPLES.md)

## Implementation Workflow

Copy this checklist to track progress:

```markdown
Implementation Progress:
- [ ] 1. Select primitive and identify `asChild` composition needs
- [ ] 2. Create/Verify custom component (`forwardRef` + `{...props}` spread is MANDATORY)
- [ ] 3. Create component abstraction (Root, Trigger, Content, Portal)
- [ ] 4. Implement styling using `data-[state]` attributes
- [ ] 5. Verify accessibility (keyboard nav, focus management)
- [ ] 6. Handle edge cases (Portal contexts, z-index layering)
```

## Core Patterns

### 1. asChild Composition Pattern (Critical)

Delegates Radix behavior to your custom components.

**Mandatory Requirements**:
1.  **Prop Spreading**: Custom components MUST spread `{...props}` to the underlying DOM node.
2.  **Ref Forwarding**: Custom components MUST use `React.forwardRef`.

**Template**:
```typescript
const CustomButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, className, ...props }, ref) => (
    <button ref={ref} className={className} {...props}>
      {children}
    </button>
  )
);
```

**Anti-Pattern**: Missing prop spreading breaks keyboard listeners and state handlers.

### 2. Component Abstraction Pattern

Encapsulate primitives to ensure consistency (Portal, Overlay, Close buttons).

**Best Practice**: Wrap primitives (Root, Trigger, Content) in a single file export.
**Reference**: See [templates/TEMPLATES.md](templates/TEMPLATES.md) for Dialog abstraction.

### 3. Data Attribute Styling Pattern

Use `data-*` attributes for interaction states (open, closed, checked) instead of external state.

**Example**:
```typescript
className="data-[state=open]:animate-in data-[state=closed]:animate-out"
```

### 4. Semantic Element Management

When overriding elements (e.g., `asChild` on a `div`), you MUST manually handle:
-   `tabIndex={0}`
-   Keyboard event handlers (`onKeyDown`)
-   ARIA roles

**Preferred**: Use semantic elements (`button`, `a`) whenever possible to avoid this burden.

## Common Patterns

### Pattern 1: Portal Container Pattern

**When**: Portal content loses theme context (CSS variables) because it renders at `document.body`.

**Solution**: Use `container` prop to mount portal within theme boundary.

```typescript
const portalRef = useRef<HTMLDivElement>(null);

<Theme>
  <div ref={portalRef}>
    <Dialog.Root>
      <Dialog.Portal container={portalRef.current}>
        <Dialog.Content />
      </Dialog.Portal>
    </Dialog.Root>
  </div>
</Theme>
```

### Pattern 2: Complex Dropdown Menu

For multi-level menus, ensure `SubContent` also uses `Portal` for correct z-index layering. See [templates/TEMPLATES.md](templates/TEMPLATES.md) for full structure.

## Anti-Patterns to Avoid

### 1. Missing Prop Spreading
**Issue**: Triggers don't open; keyboard nav fails.
**Fix**: Ensure `{...props}` is on the actual DOM element.
```typescript
// ❌ Bad
const Btn = ({children}) => <button>{children}</button>
// ✅ Good
const Btn = ({children, ...p}) => <button {...p}>{children}</button>
```

### 2. Non-Functional Element Overrides
**Issue**: Using `div` as a trigger without accessibility attributes.
**Fix**: Use `<button>` or add `role="button" tabIndex={0}`.

### 3. CSS Order Conflicts (Tailwind)
**Issue**: Radix Themes styles overridden by Tailwind base styles.
**Fix**: Explicit import order in `globals.css` or PostCSS layering.

## Workarounds

### Workaround 1: Theme Palette Abstraction
**Problem**: Radix uses physical colors (crimson); you need semantic names (primary).
**Solution**: Create a Context provider mapping semantic names to Radix tokens.

## Performance Considerations
-   **Refs**: Use `useCallback` ref merging if you need local access to the ref.
-   **Portals**: Only use `Portal` when z-index breakout is required (Dialogs, Popovers).
-   **State**: Rely on Radix internal state; avoids re-renders from external `useState`.
