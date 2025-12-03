# Routing Patterns

## Parallel Routes

Independent layouts with separate loading states.

```typescript
// app/dashboard/layout.tsx
export default function DashboardLayout(props: {
  children: React.ReactNode;
  analytics: React.ReactNode; // @analytics slot
  team: React.ReactNode;      // @team slot
}) {
  return (
    <div className="grid">
      <main>{props.children}</main>
      <aside>
        {props.analytics}
        {props.team}
      </aside>
    </div>
  );
}
```

## Intercepting Routes

Modals with shareable URLs.

```typescript
// app/photos/@modal/(.)photos/[id]/page.tsx
export default function PhotoModal({ params }: { params: { id: string } }) {
  return (
    <Modal>
      <PhotoDetail id={params.id} />
    </Modal>
  );
}
```

## Route Handlers

For public APIs or complex HTTP contracts.

```typescript
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const data = await fetchNative();
  return NextResponse.json(data);
}
```

