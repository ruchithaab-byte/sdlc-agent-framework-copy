# Architectural Patterns

## Component-First Abstraction

The definitive best practice for managing large-scale Tailwind projects is integrating the framework tightly with a component-based system (React, Vue, etc.) or template languages. This approach ensures reusability by creating template partials or framework components that encapsulate the utility class combinations.

**Pattern**: Framework component abstraction for utility composition
**Anti-pattern**: Class soup and copy-paste culture without abstraction

### Component Structure Template

```tsx
// Button.tsx - Atomic/Primitive Component
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
}

export const Button = ({ variant = 'primary', size = 'md', children, onClick }: ButtonProps) => {
  const baseClasses = 'font-medium rounded-lg focus:ring-2 focus:outline-none transition-colors';
  const variantClasses = {
    primary: 'bg-brand-primary hover:bg-brand-hover text-brand-on',
    secondary: 'bg-neutral-secondary hover:bg-neutral-hover text-neutral-on',
    danger: 'bg-feedback-error hover:bg-feedback-error-hover text-feedback-error-on'
  };
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};
```

### Component Hierarchy

- **Atomic/Primitive Components**: Low-coupling elements like buttons, inputs, and icons
- **Composite Components**: Higher-level abstractions that combine primitives, such as Cards, Forms, or Navigation bars
- **Layout Components**: Dedicated wrappers that standardize foundational layout rules

### Abstraction Method Comparison

| Method | Primary Use Case | Architectural Strength | Architectural Weakness |
|--------|------------------|------------------------|----------------------|
| Framework Component (React/Vue) | Complex, interactive, or multi-variant UI elements | Provides the Single Source of Truth; maximum control | Requires a JavaScript framework runtime |
| Custom CSS Class with @apply | Simple, highly repeated styles; migration | Reduces immediate HTML verbosity | Reduces flexibility; introduces indirection |
| Headless UI Component | Complex, accessible, stateful components | Separates behavior from styling | Dependency on specific libraries |

## Semantic Design Tokens

To counter the anti-pattern of using literal colors, the primary best practice involves establishing a customized, semantic design token strategy within the Tailwind configuration. The goal is to decouple the token's name from its visual color value.

**Pattern**: Semantic color naming with complete theme customization
**Anti-pattern**: Literal colors (blue-500, gray-700) without semantic meaning

### Semantic Naming Convention

The recommended naming convention for alias colors follows a hierarchy: `[role]-[prominence]-[interaction]`

- **Role**: Describes the token's purpose (e.g., brand, neutral, error, success)
- **Prominence**: Specifies usage level (e.g., primary, secondary, subtle)
- **Interaction**: Denotes state (e.g., hover, active, disabled)

### Theme Configuration Template

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#3B82F6',
          hover: '#2563EB',
          active: '#1D4ED8',
          on: '#FFFFFF'
        },
        neutral: {
          primary: '#1F2937',
          secondary: '#4B5563',
          subtle: '#9CA3AF',
          hover: '#374151',
          on: '#FFFFFF'
        },
        feedback: {
          error: '#EF4444',
          'error-hover': '#DC2626',
          'error-on': '#FFFFFF',
          success: '#10B981',
          'success-hover': '#059669',
          'success-on': '#FFFFFF',
          warning: '#F59E0B',
          'warning-hover': '#D97706',
          'warning-on': '#FFFFFF'
        }
      }
    }
  }
}
```

### Semantic vs Literal Color Usage

| Concept | Literal Tailwind Class (Anti-Pattern) | Semantic Tailwind Class (Best Practice) | Justification |
|---------|--------------------------------------|------------------------------------------|---------------|
| Primary Button | `bg-blue-500 hover:bg-blue-600` | `bg-brand-primary hover:bg-brand-hover` | Decouples design from aesthetic |
| Standard Text | `text-gray-700` | `text-neutral-primary` | Defines hierarchical importance |
| Error Message | `bg-red-500 text-white` | `bg-feedback-error text-feedback-error-on` | Ensures consistent feedback |

## Layout Component Standardization

**Description**: Standardize layout rules in dedicated components that encapsulate foundational structural patterns. This allows developers to focus on content without reinventing basic structural rules repeatedly.

### Layout Component Template

```tsx
// Container.tsx - Layout Component
interface ContainerProps {
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  padding?: boolean;
}

export const Container = ({ children, maxWidth = 'xl', padding = true }: ContainerProps) => {
  const maxWidthClasses = {
    sm: 'max-w-screen-sm',
    md: 'max-w-screen-md',
    lg: 'max-w-screen-lg',
    xl: 'max-w-screen-xl',
    '2xl': 'max-w-screen-2xl',
    full: 'max-w-full'
  };

  return (
    <div className={`mx-auto ${maxWidthClasses[maxWidth]} ${padding ? 'px-4 sm:px-6 lg:px-8' : ''}`}>
      {children}
    </div>
  );
};
```

## Headless UI Integration

For highly complex, stateful components that require sophisticated interaction logic, keyboard navigation, and robust accessibility (e.g., dropdowns, command palettes, modals), the best practice is the architectural delegation of responsibilities. Tailwind is used purely as the styling engine, while a "headless" library handles the behavioral and accessibility logic.

### Headless UI Integration Template

```tsx
// Dropdown.tsx - Using Headless UI with Tailwind
import { Menu } from '@headlessui/react';

export const Dropdown = () => {
  return (
    <Menu as="div" className="relative">
      <Menu.Button className="px-4 py-2 bg-brand-primary text-brand-on rounded-lg">
        Options
      </Menu.Button>
      <Menu.Items className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
        <div className="py-1">
          <Menu.Item>
            {({ active }) => (
              <a
                href="#"
                className={`${
                  active ? 'bg-neutral-hover text-neutral-primary' : 'text-neutral-secondary'
                } block px-4 py-2 text-sm`}
              >
                Account settings
              </a>
            )}
          </Menu.Item>
        </div>
      </Menu.Items>
    </Menu>
  );
};
```

### Custom Variants for Headless UI

```js
// tailwind.config.js
module.exports = {
  plugins: [
    function({ addVariant }) {
      addVariant('ui-open', '&[data-headlessui-state="open"]');
      addVariant('ui-active', '&[data-headlessui-state="active"]');
      addVariant('ui-focus', '&[data-headlessui-state="focus"]');
    }
  ]
}
```

