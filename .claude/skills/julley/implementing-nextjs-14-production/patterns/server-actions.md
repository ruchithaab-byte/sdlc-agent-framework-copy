# Server Action Patterns

## Basic Action with Validation

Use Zod for input validation and implement auth checks.

```typescript
// app/actions.ts
'use server';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const createPostSchema = z.object({
  title: z.string().min(1).max(100),
  content: z.string().min(1),
});

export async function createPost(formData: FormData) {
  // 1. Validation
  const rawData = {
    title: formData.get('title'),
    content: formData.get('content'),
  };
  
  const validated = createPostSchema.safeParse(rawData);
  if (!validated.success) {
    return { error: 'Validation failed', details: validated.error.errors };
  }

  // 2. Auth Check
  const user = await getCurrentUser();
  if (!user) return { error: 'Unauthorized' };

  // 3. Mutation
  await createPostInDatabase(validated.data);

  // 4. Revalidation
  revalidatePath('/posts');
  return { success: true };
}
```

## Action with useActionState

Handle form state and errors gracefully.

```typescript
// app/actions.ts
'use server';
import { revalidatePath } from 'next/cache';

export async function createPost(
  prevState: { message: string },
  formData: FormData
) {
  const title = formData.get('title') as string;
  
  if (!title) return { message: 'Title required' };

  try {
    await savePost({ title });
    revalidatePath('/posts');
    return { message: 'Success' };
  } catch (e) {
    return { message: 'Failed to create post' };
  }
}

// Client Component usage
// const [state, formAction, pending] = useActionState(createPost, initialState);
// <form action={formAction}>...</form>
```

## Anti-Patterns
- **Actions for Reads**: Use Server Components for reading data.
- **Missing Validation**: Never trust client input.
- **Exceptions for Expected Errors**: Return error objects instead of throwing.

