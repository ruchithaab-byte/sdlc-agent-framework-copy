# Real-World Examples

## Example 1: Production Dialog Component

```typescript
// components/dialog.tsx
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Cross1Icon } from "@radix-ui/react-icons";
import { cn } from "@/lib/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;

export const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="data-[state=open]:animate-overlayShow fixed inset-0 bg-black/50 z-50" />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "data-[state=open]:animate-contentShow fixed top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] bg-white p-6 rounded-lg shadow-xl z-50",
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute top-4 right-4" aria-label="Close">
        <Cross1Icon />
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
));
```

## Example 2: Custom Button as Tooltip Trigger

```typescript
// components/custom-button.tsx
import * as React from "react";
import { cn } from "@/lib/utils";

interface CustomButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "icon";
  size?: "small" | "medium" | "large";
}

const CustomButton = React.forwardRef<HTMLButtonElement, CustomButtonProps>(
  ({ children, className, variant = "default", size = "medium", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "rounded font-medium transition-colors",
        variant === "icon" && "p-2",
        size === "small" && "text-sm px-3 py-1.5",
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
);

// Usage with Tooltip
import * as Tooltip from "@radix-ui/react-tooltip";

<Tooltip.Root>
  <Tooltip.Trigger asChild>
    <CustomButton variant="icon" size="small">i</CustomButton>
  </Tooltip.Trigger>
  <Tooltip.Content>This uses asChild with prop spreading</Tooltip.Content>
</Tooltip.Root>
```

