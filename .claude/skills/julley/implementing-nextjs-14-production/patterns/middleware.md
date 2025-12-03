# Middleware Patterns

## Authentication

Lightweight checks before route matching.

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  const currentUser = request.cookies.get('currentUser')?.value;

  if (currentUser && request.nextUrl.pathname.startsWith('/login')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  if (!currentUser && !request.nextUrl.pathname.startsWith('/login')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|.*\\.png$).*)'],
};
```

## Path Rewriting

Dynamic rewriting for feature flags.

```typescript
// middleware.ts
if (request.nextUrl.pathname === '/new-feature' && isBetaUser) {
  return NextResponse.rewrite(new URL('/feature-v2', request.url));
}
```

## Anti-Patterns
- **Heavy Computation**: No complex logic or database calls in middleware.

