---
name: shadcn_scaffolder
description: Scaffold and configure Shadcn UI components with verification
---

# Shadcn UI Scaffolder Skill

This skill provides patterns for installing and configuring Shadcn UI components in React/Next.js projects.

## When to Use This Skill

Use this skill when:
- Adding new UI components to a React/Next.js project
- Setting up Shadcn UI for the first time
- Customizing Shadcn components
- Ensuring components are properly installed

## Prerequisites

Before using Shadcn UI, ensure your project has:

1. **React 18+** or **Next.js 13+**
2. **Tailwind CSS** configured
3. **TypeScript** (recommended)

### Initial Setup (if not already configured)

```bash
# Initialize Shadcn UI in your project
npx shadcn-ui@latest init
```

During init, you'll configure:
- TypeScript (recommended: yes)
- Style (default or new-york)
- Base color
- CSS variables
- Component path (e.g., `@/components`)
- Utility path (e.g., `@/lib/utils`)

## scaffold_shadcn_component

Installs a Shadcn UI component and verifies installation.

### Installation Commands

```bash
# Install a single component
npx shadcn-ui@latest add button

# Install multiple components
npx shadcn-ui@latest add button card dialog

# Install with automatic yes to prompts
npx shadcn-ui@latest add button --yes

# Install and overwrite existing
npx shadcn-ui@latest add button --overwrite
```

### Available Components

#### Layout
- `accordion` - Collapsible content sections
- `card` - Container with header, content, footer
- `separator` - Visual divider
- `tabs` - Tabbed interface

#### Form
- `button` - Clickable button variants
- `checkbox` - Toggle checkbox
- `input` - Text input field
- `label` - Form label
- `select` - Dropdown selection
- `textarea` - Multi-line text input
- `form` - Form wrapper with react-hook-form

#### Feedback
- `alert` - Status messages
- `alert-dialog` - Confirmation dialogs
- `dialog` - Modal dialogs
- `toast` - Notification toasts
- `tooltip` - Hover tooltips

#### Navigation
- `dropdown-menu` - Dropdown menus
- `navigation-menu` - Site navigation
- `menubar` - Application menubar

#### Data Display
- `table` - Data tables
- `badge` - Status badges
- `avatar` - User avatars

### Verification Steps

After installing a component:

1. **Check file exists**:
   ```bash
   ls components/ui/button.tsx
   ```

2. **Verify imports work**:
   ```typescript
   import { Button } from "@/components/ui/button"
   ```

3. **Test in a page**:
   ```tsx
   <Button variant="default">Click me</Button>
   ```

4. **Run dev server**:
   ```bash
   npm run dev
   ```

## Component Customization

### Variant Configuration

Shadcn components use class-variance-authority (CVA):

```typescript
const buttonVariants = cva(
  "base-classes",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        destructive: "bg-destructive text-destructive-foreground",
        outline: "border border-input bg-background",
        secondary: "bg-secondary text-secondary-foreground",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)
```

### Theme Customization

Edit `tailwind.config.js` or CSS variables in `globals.css`:

```css
:root {
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  /* ... more variables */
}

.dark {
  --primary: 210 40% 98%;
  --primary-foreground: 222.2 47.4% 11.2%;
  /* ... dark mode overrides */
}
```

## Common Issues

### Component Not Found
```
Error: Cannot find module '@/components/ui/button'
```
**Solution**: Run `npx shadcn-ui@latest add button`

### Missing Dependencies
```
Error: Cannot find module '@radix-ui/react-dialog'
```
**Solution**: Run `npm install` after adding components

### Tailwind Classes Not Applied
**Solution**: Ensure `components/` is in `tailwind.config.js` content paths

## Integration with SDLC Agents

### CodeCraft Agent (Frontend)
Uses this skill when implementing UI features to quickly scaffold needed components.

### QualityGuard Agent
Verifies component installations are complete and functional.

## Related Skills

- `implementing-shadcn-ui-production` - Advanced Shadcn patterns
- `implementing-react-18-architecture` - React architecture patterns
- `implementing-tailwind-enterprise` - Tailwind configuration
- `implementing-radix-ui-production` - Radix primitives
