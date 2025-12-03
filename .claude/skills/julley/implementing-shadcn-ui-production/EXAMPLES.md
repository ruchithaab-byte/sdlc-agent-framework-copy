# Real-World Examples

## Example 1: Enterprise Data Table with Server-Side Pagination

**Context**: High-volume data tables requiring server-side pagination for performance. Client-side pagination inefficient for thousands of records.

**Implementation**: Separate data fetching (Server Component) from interactivity (Client Component). Server Component fetches data based on URL searchParams. Client Component (PaginationControls) modifies URL query string to trigger server re-fetch.

```typescript
// app/products/page.tsx (Server Component)
export default async function ProductsPage({ searchParams }: { searchParams: { page?: string } }) {
  const page = parseInt(searchParams.page || "1");
  const products = await fetchProducts(page);
  
  return (
    <div>
      <DataTable data={products} />
      <PaginationControls currentPage={page} lastPage={products.totalPages} />
    </div>
  );
}

// components/pagination-controls.tsx (Client Component - 15 lines)
"use client";
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
      <Button disabled={currentPage === 1} onClick={() => handlePageChange(currentPage - 1)}>Previous</Button>
      <Button disabled={currentPage === lastPage} onClick={() => handlePageChange(currentPage + 1)}>Next</Button>
    </div>
  );
}
```

**Key Points**: URL query string management triggers server-side re-render. Server/Client component separation ensures efficient data fetching.

## Example 2: Custom Utility Distribution

**Context**: Cross-browser scrollbar hiding utility needed consistently across application. Complex CSS rules require centralized management.

**Implementation**: Define custom utility in registry JSON using @utility directive. CLI distributes CSS, making class available like standard Tailwind utility.

```json
// registry/utility/scrollbar-hidden.json
{
  "$schema": "https://ui.shadcn.com/schema/registry-item.json",
  "name": "scrollbar-hidden",
  "type": "registry:utility",
  "css": {
    "@utility scrollbar-hidden": {
      "&::-webkit-scrollbar": { "display": "none" },
      "-ms-overflow-style": "none",
      "scrollbar-width": "none"
    }
  }
}
```

**Usage**: `<ScrollArea className="scrollbar-hidden">...</ScrollArea>`

**Key Points**: @utility directive enables centralized CSS management. Complex styling concerns integrated into utility-first design system.

