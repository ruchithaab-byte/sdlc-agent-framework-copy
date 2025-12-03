# Server Component Patterns

## Data Fetching (Server-Side)

Direct database/API access in Server Components (default).

```typescript
// app/products/page.tsx
async function ProductsPage() {
  const products = await fetch('https://api.example.com/products', {
    next: { revalidate: 3600 } // ISR: revalidate every hour
  }).then(res => res.json());

  return (
    <div>
      {products.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
```

## Component Interleaving

Pass Server Components as children to Client Components to maintain RSC isolation.

```typescript
// app/components/Modal.tsx (Client Component)
'use client';
import { useState } from 'react';

export function Modal({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  // ... implementation
  return (
    <div className="modal">
      {children} {/* Server Component passed here */}
    </div>
  );
}

// app/page.tsx (Server Component)
import { Modal } from './components/Modal';
import { CartSummary } from './components/CartSummary'; // Server Component

export default function Page() {
  return (
    <Modal>
      <CartSummary /> {/* SC passed as children to CC */}
    </Modal>
  );
}
```

## Serialization

Serialize complex types (Date, Class, Promise) before passing to Client Components.

```typescript
// app/components/ServerDate.tsx (Server Component)
export async function ServerDate() {
  const date = new Date();
  return <ClientDateDisplay date={date.toISOString()} />; // Serialize to string
}

// app/components/ClientDateDisplay.tsx (Client Component)
'use client';
export function ClientDateDisplay({ date }: { date: string }) {
  const dateObj = new Date(date); // Deserialize in client
  return <div>{dateObj.toLocaleDateString()}</div>;
}
```

## Anti-Patterns
- **Browser API access**: No `window`, `localStorage`, or event handlers in SC.
- **Direct SC import**: Do not import SC directly into CC files. Use children prop.
- **Non-serializable props**: No functions or objects with methods passed to CC.

