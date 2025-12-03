# Caching & Revalidation Patterns

## Comprehensive Revalidation

Combine `revalidatePath` and `updateTag`.

```typescript
// app/lib/cache-utils.ts
'use server';
import { revalidatePath, updateTag } from 'next/cache';

export async function updatePostAndRevalidate(postId: string) {
  // 1. Invalidate detail page
  revalidatePath(`/posts/${postId}`);

  // 2. Invalidate aggregate lists (tagged)
  updateTag('posts');

  // 3. Optional: Layout revalidation
  revalidatePath('/posts', 'layout');
}
```

## Tagged Fetch

Use tags for granular invalidation of aggregate data.

```typescript
// Server Component
async function PostList() {
  const posts = await fetch('https://api.example.com/posts', {
    next: { tags: ['posts'] }
  }).then(res => res.json());
  // ...
}
```

## Stale-While-Revalidate

`revalidateTag` serves stale content immediately and updates in background.

```typescript
'use server';
import { revalidateTag } from 'next/cache';

export async function refreshPosts() {
  revalidateTag('posts'); // SWR semantics
}
```

