# Configuration & Performance

## Content Configuration (JIT)

The JIT engine generates CSS on-demand by statically scanning all template files during the build process. This makes the accurate configuration of the content array in the `tailwind.config.js` file an architectural mandate. Failure to configure this array to include all potential template paths means that Tailwind cannot detect the utility classes used in those files, resulting in an incomplete or entirely empty stylesheet.

**Pattern**: Comprehensive content array configuration for static extraction
**Anti-pattern**: Incomplete content paths leading to missing styles or bloated CSS

### Content Configuration Template

```js
// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './app/**/*.{js,jsx,ts,tsx}',
    './pages/**/*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
    './public/**/*.html',
    './templates/**/*.{html,php}',
    './*.{js,jsx,ts,tsx}'
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### Best Practices

- Include all file extensions used in the project (`.jsx`, `.tsx`, `.html`, `.vue`, `.php`)
- Cover all directories containing templates (src, app, pages, components, public, templates)
- Use glob patterns to match nested directories (`**/*`)
- Implement CI/CD validation to ensure path coverage
- Test build output to verify all utility classes are detected
- Monitor final CSS bundle size to detect configuration issues

## Performance Considerations

**Bundle Size Monitoring**: The architectural benchmark for high-performance Tailwind deployments is achieving a final, gzipped CSS file size well under 10kB. Netflix achieved 6.5kB for their "Netflix Top 10" interface. Implement CI/CD checks to monitor bundle size and prevent configuration errors.

**JIT Compilation**: Tailwind CSS v3.x uses JIT (Just-In-Time) compilation by default. The JIT engine generates CSS on-demand by statically scanning all template files during the build process. This makes content configuration critical for performance.

**Tree-Shaking**: Tailwind automatically tree-shakes unused utilities, but only for classes detected in the content array. Incomplete content configuration can lead to missing styles or, conversely, inclusion of unnecessary utilities if content paths are too broad.

**Build Performance**: Content scanning performance depends on the number and size of files in the content array. Use specific glob patterns to avoid scanning unnecessary files (e.g., `node_modules`, build outputs). Consider using `content` paths that match actual template locations.

**Runtime Performance**: Tailwind utility classes have minimal runtime overhead. Styles are generated at build-time, not runtime. Dynamic styling via CSS variables has negligible performance impact compared to CSS-in-JS solutions.

## Dependencies

This skill provides guidance for Tailwind CSS implementations. Required dependencies (as needed):

**Core Tailwind CSS**:
- `tailwindcss`: Core Tailwind CSS framework (v3.x recommended)

**Build Tools**:
- `postcss`: PostCSS processor
- `autoprefixer`: Autoprefixer plugin for cross-browser compatibility

**Framework Integration** (choose based on project):
- `@tailwindcss/react`: React integration (if using React)
- `@tailwindcss/vue`: Vue integration (if using Vue)

**Headless UI Libraries** (optional, for complex components):
- `@headlessui/react`: Headless UI for React
- `@headlessui/vue`: Headless UI for Vue
- `@radix-ui/react-*`: Radix UI primitives (alternative)

**Note**: Dependencies must be added to `package.json` based on project requirements. Tailwind CSS v3.x includes JIT mode by default and does not require separate JIT plugin.

