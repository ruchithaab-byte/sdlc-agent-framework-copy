# Workarounds

## Workaround 1: CSS Variables for Dynamic Styling

**When**: Runtime dynamic values that cannot be statically extracted (e.g., user-selected colors, theme colors fetched from API, dynamic spacing based on user preferences).

**Action**: Hybrid approach combining inline styles with Tailwind's arbitrary value syntax to maintain modifier support.

**Implementation**:
1. Define dynamic value using inline style attribute with CSS variable
2. Reference CSS variable using Tailwind's arbitrary value syntax
3. Apply Tailwind modifiers (hover, focus, responsive) as needed

**Example**:
```tsx
// Dynamic button color from user selection
const Button = ({ userColor }: { userColor: string }) => {
  return (
    <button
      style={{ '--button-color': userColor } as React.CSSProperties}
      className="px-4 py-2 rounded-lg bg-[var(--button-color)] hover:opacity-90 focus:ring-2 focus:ring-[var(--button-color)]"
    >
      Click me
    </button>
  );
};
```

**Trade-offs**:
- **Maintenance debt**: Requires inline styles alongside utility classes, slightly more verbose
- **Limitations**: CSS variables must be defined inline, cannot use theme tokens for dynamic values
- **Future considerations**: Consider CSS-in-JS solutions (styled-components, emotion) for complex dynamic styling needs

## Workaround 2: Arbitrary Values

**When**: Non-standard CSS properties not covered by Tailwind utilities, one-off design requirements, or incorporating custom CSS properties that Tailwind does not provide out-of-the-box.

**Action**: Use square bracket notation for arbitrary values, combining with Tailwind modifiers when needed.

**Implementation**:
1. Use square bracket syntax: `[property:value]`
2. Combine with Tailwind modifiers: `hover:[property:value]`
3. Use for responsive variants: `md:[property:value]`

**Example**:
```tsx
// Non-standard CSS property
<div className="[mask-type:luminance] hover:[mask-type:alpha]">
  Content
</div>

// Custom CSS variable with responsive behavior
<div className="[--scroll-offset:56px] lg:[--scroll-offset:44px]">
  Content
</div>
```

**Trade-offs**:
- **Maintenance debt**: Breaks theme constraints, values not centralized in configuration
- **Limitations**: Arbitrary values cannot be used with all Tailwind features, may not work with some plugins
- **Future considerations**: Reserve for edge cases only, consider adding to theme configuration if value becomes standard

## Workaround 3: Custom Modifiers and State Variants

**When**: Manual dark mode toggle (not OS-based), custom application states, or targeting specific data attributes for component state.

**Action**: Use `@custom-variant` directive or plugin API to create custom variants that target application-specific selectors.

**Implementation**:
1. Define custom variant using plugin API or @custom-variant directive
2. Target custom class, data attribute, or selector
3. Use custom variant in utility classes

**Example**:
```js
// tailwind.config.js
module.exports = {
  plugins: [
    function({ addVariant }) {
      // Manual dark mode toggle
      addVariant('dark', '[data-theme="dark"] &');
      
      // Custom application state
      addVariant('sidebar-open', '[data-sidebar="open"] &');
    }
  ]
}
```

```tsx
// Usage
<div className="bg-white dark:bg-neutral-primary">
  <button className="bg-brand-primary sidebar-open:bg-brand-hover">
    Toggle
  </button>
</div>
```

**Trade-offs**:
- **Maintenance debt**: Requires understanding of Tailwind plugin API, custom logic for state management
- **Limitations**: Decouples from OS preferences, requires application logic to manage state
- **Future considerations**: Consider using Tailwind's built-in dark mode configuration when possible, document custom variants clearly

