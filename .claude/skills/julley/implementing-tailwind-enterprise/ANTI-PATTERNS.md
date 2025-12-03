# Anti-Patterns to Avoid

## Anti-Pattern 1: @apply Misuse

**Issue**: Using @apply directive to shorten verbose utility class lists for aesthetic reasons breaks the fundamental utility-first philosophy. This practice reintroduces context switching, reduces flexibility in style modifications, and creates a steeper learning curve for new team members who must understand an entirely new set of opaque, custom classes on top of the native Tailwind utilities.

**Example**:
```css
/* Anti-pattern: Using @apply for component abstraction */
.btn-primary {
  @apply px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-medium;
}
```

```html
<!-- Usage requires context switching to CSS file -->
<button class="btn-primary">Click me</button>
```

**Resolution**: Use framework components (React/Vue) for abstraction instead of @apply. Abstract utility combinations at the component level using props and variants, not at the CSS level.

## Anti-Pattern 2: Class Soup

**Issue**: Long strings of utility classes applied directly to elements without abstraction (termed "Class Soup") lead to inconsistent implementation and maintenance paralysis. When complex combinations of utility classes are duplicated across multiple files, new developers often copy existing class strings with subtle, unintentional variations. Global design changes require searching for and manually modifying thousands of separate instances.

**Example**:
```tsx
// Anti-pattern: Long utility strings without abstraction
<div className="flex items-center justify-between px-6 py-4 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
  <h2 className="text-xl font-semibold text-gray-900">Title</h2>
  <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md font-medium">Action</button>
</div>

// Repeated across multiple files with variations
<div className="flex items-center justify-between px-4 py-3 bg-white border border-gray-300 rounded-lg shadow hover:shadow-lg">
  {/* Slight variations cause inconsistency */}
</div>
```

**Resolution**: Abstract utility combinations into framework components with props and variants. Create Card, Button, and other reusable components that encapsulate utility strings.

## Anti-Pattern 3: Ignoring Theme Customization

**Issue**: Using the extensive, out-of-the-box Tailwind color palette (e.g., blue-500, gray-700) without proper theme customization creates semantic debt. If branding or core design system changes—for instance, the primary brand color shifting from blue to teal—a major, often brittle, refactoring effort is required to find and replace every literal instance.

**Example**:
```tsx
// Anti-pattern: Literal colors without semantic meaning
<button className="bg-blue-500 hover:bg-blue-600 text-white">
  Primary Action
</button>
<div className="text-gray-700">Standard text</div>
<div className="bg-red-500 text-white">Error message</div>
```

**Resolution**: Complete semantic token replacement in theme configuration. Define semantic color names (brand-primary, neutral-primary, feedback-error) and replace all literal color usage.

## Anti-Pattern 4: Dynamic Class Generation

**Issue**: Attempting to derive class names from dynamic, runtime values within client-side code (e.g., `class="bg-${color}"`) cannot work because Tailwind CSS generates utility classes entirely statically at build-time. The JIT compiler cannot detect dynamically constructed class names, resulting in styles not being generated or applied.

**Example**:
```tsx
// Anti-pattern: Dynamic class generation
const Button = ({ color }: { color: string }) => {
  return <button className={`bg-${color}-500`}>Click</button>; // Won't work!
};

// Template literals in class names
const variant = 'primary';
<div className={`btn-${variant}`}>Content</div>; // Won't work if btn-primary not detected!
```

**Resolution**: Use CSS variables + arbitrary values for truly dynamic styling, or use inline styles for runtime values. Never construct class names dynamically with template literals.

## Anti-Pattern 5: Incomplete Content Configuration

**Issue**: Missing template paths in the content array means Tailwind cannot detect utility classes used in those files, resulting in missing styles or an incomplete stylesheet. Conversely, if content paths are too broad or include unnecessary files, the build process may be slower, though this is less critical than missing paths.

**Example**:
```js
// Anti-pattern: Incomplete content configuration
module.exports = {
  content: [
    './src/**/*.jsx' // Missing .tsx, .html, and other directories!
  ]
}
```

**Resolution**: Comprehensive content array covering all template file types and directories. Implement CI/CD validation to ensure path coverage. Test build output to verify all utilities are detected.

## Anti-Pattern 6: Magic Numbers

**Issue**: Using arbitrary or "magic numbers"—unique values lacking explanation or naming, such as `mt-[13px]`—for spacing or other constraints that should be governed by the standardized spacing scale constitutes ignoring existing theme settings. If a value must be used repeatedly, it must be defined in the theme configuration, not hardcoded as an arbitrary value.

**Example**:
```tsx
// Anti-pattern: Magic numbers for spacing
<div className="mt-[13px] mb-[7px] px-[23px]">
  Content with inconsistent, unexplained spacing
</div>
```

**Resolution**: Define repeated values in theme configuration. Use Tailwind's spacing scale (0, 1, 2, 4, 8, 12, 16, etc.) or extend theme with custom spacing values.

## Summary Table

| Anti-Pattern | Issue | Resolution |
|-------------|-------|------------|
| @apply Misuse | Reintroduces context switching, reduces flexibility | Use framework components for abstraction |
| Class Soup | Inconsistent implementation, maintenance paralysis | Abstract utility combinations into components |
| Ignoring Theme Customization | Semantic debt, brittle rebranding | Complete semantic token replacement |
| Dynamic Class Generation | Classes not detected by JIT compiler | Use CSS variables + arbitrary values |
| Incomplete Content Configuration | Missing styles, bloated CSS | Comprehensive content array, CI/CD validation |
| Magic Numbers | Inconsistent spacing, breaks design system | Define in theme configuration |

