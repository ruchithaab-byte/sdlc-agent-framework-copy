# Code Templates

## Composite Component Template

```typescript
// components/business-component.tsx
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function BusinessComponent() {
  return (
    <Card>
      <CardContent>
        <Button>Action</Button>
      </CardContent>
    </Card>
  );
}
```

## CVA Variant Template

```typescript
import { cva, type VariantProps } from "class-variance-authority";

const componentVariants = cva("base", {
  variants: {
    size: { sm: "h-8", md: "h-10", lg: "h-12" },
    variant: { primary: "bg-primary", destructive: "bg-destructive" },
  },
  defaultVariants: { size: "md", variant: "primary" },
});

interface Props extends VariantProps<typeof componentVariants> {
  children: React.ReactNode;
}
```

## Theme Token Extension Template

```css
/* Step 1: Define variables */
:root { --custom: 200 80% 50%; }
.dark { --custom: 200 80% 60%; }

/* Step 2: Map to utilities */
@theme inline {
  --color-custom: oklch(var(--custom));
}

/* Step 3: Use in components */
/* className="bg-custom" */
```

## Server-Side Pagination Template

```typescript
// components/pagination-controls.tsx (Client Component)
"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";

export function PaginationControls({ currentPage, lastPage }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const handlePageChange = (page: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", page.toString());
    router.push(`?${params.toString()}`);
  };
  
  return (
    <div className="flex space-x-2">
      <Button disabled={currentPage === 1} onClick={() => handlePageChange(currentPage - 1)}>
        Previous
      </Button>
      <Button disabled={currentPage === lastPage} onClick={() => handlePageChange(currentPage + 1)}>
        Next
      </Button>
    </div>
  );
}
```

## Form Validation Template

```typescript
// Using Zod + react-hook-form + shadcn/ui
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";

const schema = z.object({
  username: z.string().min(2, "Username must be at least 2 characters"),
  email: z.string().email("Valid email required"),
});

export function SignUpForm() {
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { username: "", email: "" },
  });
  
  const onSubmit = (data: z.infer<typeof schema>) => {
    console.log(data);
  };
  
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField control={form.control} name="username" render={({ field }) => (
          <FormItem>
            <FormLabel>Username</FormLabel>
            <FormControl><Input {...field} /></FormControl>
            <FormMessage />
          </FormItem>
        )} />
      </form>
    </Form>
  );
}
```

