---
name: implementing-algolia-search
description: Implements Algolia search using radical denormalization, frontend direct search, secured API keys for multi-tenancy, and custom ranking. Handles selective indexing, batching, infinite scroll, debouncing, record splitting with Distinct, atomic re-indexing, and paginationLimitedTo. Avoids normalized structures, backend proxying, and index-per-tenant patterns.
version: 1.0.0
dependencies:
  - algoliasearch>=4.0.0
  - react-instantsearch-hooks-web>=6.0.0
---

# Implementing Algolia Search

Implements Algolia search functionality using search-first architecture patterns. Covers data modeling, indexing strategies, search architecture, security patterns, relevance engineering, and frontend implementation.

## When to Use

- Implementing search functionality in applications
- Migrating from database-based search to Algolia
- Optimizing existing Algolia implementations
- Handling multi-tenant search requirements
- Implementing federated search across multiple data types
- Setting up SSR/SEO-compatible search

## Prerequisites

- Algolia account with API keys (Search-Only and Admin keys)
- Understanding of data structure to be indexed
- Frontend framework (React, Vue, vanilla JS) or backend requirements
- Access to application backend for Secured API Key generation (if multi-tenant)

## Step 1: Data Modeling - Radical Denormalization

Flatten normalized database structures into single, self-contained records.

**Flattened Record Structure**:

```javascript
{
  objectID: "product_123",
  name: "iPhone 15 Pro",
  price: 999,
  category: "Electronics",
  category_id: "cat_001",
  brand: "Apple",
  brand_id: "brand_001",
  description: "Latest iPhone model...",
  tags: ["smartphone", "apple", "pro"],
  in_stock: true,
  popularity_score: 8500
}
```

Only include attributes needed for search matching, display, sorting, or filtering.

**Record Splitting for Long Content**:

For documents exceeding record size limits (10KB-100KB):

- Split document into paragraph/section chunks
- Index each chunk as separate record
- Use `distinct: true` with `attributeForDistinct: "document_id"` to return one result per document

## Step 2: Indexing Operations - Batching

Group indexing operations into batches (1,000-100,000 records, max 10MB per batch).

**Batch Indexing**:

```javascript
import algoliasearch from 'algoliasearch';

const client = algoliasearch(APP_ID, ADMIN_API_KEY);
const index = client.initIndex('products');

async function batchIndex(records) {
  const BATCH_SIZE = 1000;
  for (let i = 0; i < records.length; i += BATCH_SIZE) {
    const batch = records.slice(i, i + BATCH_SIZE);
    await index.saveObjects(batch);
  }
}
```

**Partial Updates**:

```javascript
await index.partialUpdateObjects([{
  objectID: "product_123",
  price: 899
}]);
```

**Atomic Re-indexing**:

For structural changes requiring full re-index:

1. Index data into temporary index (`products_temp`)
2. Use `moveIndex('products_temp', 'products')` to atomically replace production index

## Step 3: Search Architecture - Frontend Direct Search

Query Algolia directly from the client using Search-Only API keys.

**Frontend Search Initialization**:

```javascript
import algoliasearch from 'algoliasearch';

const searchClient = algoliasearch(APP_ID, SEARCH_ONLY_API_KEY);
const index = searchClient.initIndex('products');
```

Search-Only keys are safe for frontend exposure. They cannot modify indices or access admin settings.

**Backend search required for**:

- SSR/SEO generation
- System-to-system queries
- Complex security logic exceeding Secured API Key payload limits

## Step 4: Multi-Tenancy - Secured API Keys

Generate HMAC-signed virtual keys on backend that enforce tenant isolation without separate indices.

**Secured API Key Generation (Backend)**:

```javascript
import algoliasearch from 'algoliasearch';

const client = algoliasearch(APP_ID, ADMIN_API_KEY);

function generateSecuredKey(tenantId) {
  return client.generateSecuredApiKey(SEARCH_ONLY_KEY, {
    filters: `tenant_id:${tenantId}`,
    validUntil: Math.floor(Date.now() / 1000) + 3600,
    restrictIndices: ['products']
  });
}

app.get('/api/search-key', (req, res) => {
  const tenantId = req.user.tenantId;
  const securedKey = generateSecuredKey(tenantId);
  res.json({ apiKey: securedKey });
});
```

Use single index with filter-based isolation. Algolia validates signature and forcibly applies embedded filters.

## Step 5: Relevance Engineering - Custom Ranking

Use custom ranking attributes (popularity, sales rank, date) for business control.

**Custom Ranking Configuration**:

```javascript
await index.setSettings({
  customRanking: ['desc(popularity_score)', 'desc(sales_rank)'],
  searchableAttributes: [
    'name',
    'description',
    'tags'
  ],
  attributesForFaceting: ['category', 'brand', 'price']
});
```

**Synonyms**:

```javascript
await index.saveSynonym({
  objectID: 'pants-synonym',
  type: 'synonym',
  synonyms: ['pants', 'trousers', 'slacks']
});
```

**Derived Attributes for Noise Reduction**:

For "noise" in long descriptions:

- Extract key terms into `short_description` or `keywords` attribute
- Prioritize derived attribute in `searchableAttributes` list

## Step 6: Frontend Implementation - Infinite Scroll

Implement infinite scroll to avoid deep pagination limitations.

**Infinite Scroll (React)**:

```javascript
import { useInfiniteHits } from 'react-instantsearch-hooks-web';

function ProductList() {
  const { hits, showMore, isLastPage } = useInfiniteHits();
  
  return (
    <>
      {hits.map(hit => <ProductCard key={hit.objectID} product={hit} />)}
      {!isLastPage && <button onClick={showMore}>Load More</button>}
    </>
  );
}
```

**Search for Facet Values**:

For high-cardinality facets (10,000+ values):

```javascript
import { RefinementList } from 'react-instantsearch-hooks-web';

<RefinementList
  attribute="author"
  searchable={true}
/>
```

**Deep Pagination Workaround**:

```javascript
await index.setSettings({
  paginationLimitedTo: 5000
});
```

## Step 7: SSR Implementation - Next.js

Synchronize server-side search state with client.

**SSR Search (Next.js)**:

```javascript
import { InstantSearchSSRProvider, getServerState } from 'react-instantsearch-hooks-web';
import { searchClient } from '@/lib/algolia';

export default async function SearchPage({ searchParams }) {
  const serverState = await getServerState(
    <Search searchParams={searchParams} />
  );

  return (
    <InstantSearchSSRProvider {...serverState}>
      <Search searchParams={searchParams} />
    </InstantSearchSSRProvider>
  );
}
```

**URL-based Routing**:

```javascript
import { useRouter } from 'next/router';

<InstantSearch
  routing={{
    stateMapping: {
      stateToRoute(uiState) {
        return { q: uiState.query };
      },
      routeToState(routeState) {
        return { query: routeState.q };
      }
    }
  }}
/>
```

Initialize client with `initialUiState` from server to prevent duplicate requests.

## Step 8: Rules and Analytics

Use Rules strategically for merchandising exceptions.

**Rule Creation**:

```javascript
await index.saveRule({
  objectID: 'black-friday-rule',
  condition: {
    pattern: 'laptop',
    anchoring: 'contains'
  },
  consequence: {
    promote: [
      { objectID: 'laptop_premium', position: 1 }
    ],
    params: {
      query: 'laptop'
    }
  }
});
```

**Insights API**:

```javascript
import { insights } from 'search-insights';

insights('clickedObjectIDsAfterSearch', {
  eventName: 'Product Clicked',
  index: 'products',
  queryID: searchResponse.queryID,
  objectIDs: [hit.objectID],
  positions: [hit.__position]
});
```

**A/B Testing**:

1. Create replica index with proposed configuration
2. Configure A/B test in dashboard (traffic split)
3. Engine tracks performance difference using Insights data

## Step 9: Cost Optimization - Debouncing

Implement debouncing and caching to reduce search operations.

**Debouncing**:

```javascript
import { useSearchBox } from 'react-instantsearch-hooks-web';
import { useMemo } from 'react';
import { debounce } from 'lodash';

function SearchBox() {
  const { query, refine } = useSearchBox();
  
  const debouncedRefine = useMemo(
    () => debounce((value) => refine(value), 300),
    [refine]
  );
  
  return (
    <input
      onChange={(e) => debouncedRefine(e.target.value)}
      defaultValue={query}
    />
  );
}
```

**Filter-Only Attributes**:

```javascript
await index.setSettings({
  attributesForFaceting: [
    'filterOnly(is_public)',
    'category',
    'brand'
  ]
});
```

**Prevent Empty Queries**:

```javascript
<InstantSearch
  searchClient={{
    ...searchClient,
    search(requests) {
      if (requests[0].params.query === '') {
        return Promise.resolve({ results: [] });
      }
      return searchClient.search(requests);
    }
  }}
/>
```

## Key Patterns

**Data Flattening**: Include all related entity attributes directly in record. Map database PK to `objectID`. Duplicate data across records if needed.

**Attribute Selection**: Include only attributes needed for search matching, display, sorting, or filtering.

**Security**: Use Search-Only keys for public frontend search, Secured API Keys for multi-tenant scenarios, Admin keys only on backend.

**Relevance**: Prioritize custom ranking for business logic, Rules only for strategic exceptions, synonyms for natural language.

## Anti-Patterns to Avoid

- Normalized database structures (flatten data at indexing time)
- Indexing entire database rows including unnecessary metadata
- High-frequency single-record updates (use batching)
- Backend proxying when Search-Only keys suffice
- Index-per-tenant (use Secured API Keys with single index)
- Over-reliance on Rules (fix relevance globally, not per-query)
- Deep pagination beyond 1,000 hits without `paginationLimitedTo`
- Not using Distinct for chunked records

## Examples

### E-commerce Product Search

```javascript
// Flattened product record
const product = {
  objectID: "prod_123",
  name: "iPhone 15 Pro",
  price: 999,
  category: "Electronics",
  brand: "Apple",
  popularity_score: 8500,
  in_stock: true
};

// Index configuration
await index.setSettings({
  customRanking: ['desc(popularity_score)'],
  searchableAttributes: ['name', 'category', 'brand']
});

// Frontend search with infinite scroll
import { InstantSearch, InfiniteHits } from 'react-instantsearch-hooks-web';

<InstantSearch searchClient={searchClient} indexName="products">
  <SearchBox />
  <InfiniteHits hitComponent={ProductCard} />
</InstantSearch>
```

### Multi-Tenant SaaS Search

```javascript
// Backend: Generate Secured API Key
app.get('/api/search-key', authenticate, (req, res) => {
  const securedKey = client.generateSecuredApiKey(SEARCH_ONLY_KEY, {
    filters: `tenant_id:${req.user.tenantId}`,
    validUntil: Math.floor(Date.now() / 1000) + 3600
  });
  res.json({ apiKey: securedKey });
});

// Frontend: Use Secured Key
const { apiKey } = await fetch('/api/search-key').then(r => r.json());
const searchClient = algoliasearch(APP_ID, apiKey);

// Records include tenant_id
const record = {
  objectID: "doc_123",
  tenant_id: "company_A",
  title: "Document Title",
  content: "Document content..."
};
```

## Error Handling

**Indexing Failures**: Implement retry logic with exponential backoff, log failed records, use `waitTask` to ensure indexing completion.

**Query Errors**: Handle rate limiting (429 errors) with retry logic, validate API keys before requests, provide fallback UI.

**API Key Validation**: Verify key permissions match operation, check key expiration for Secured API Keys, validate key format.

**Rate Limiting**: Implement request queuing, use debouncing, monitor usage in dashboard.

## Security Guidelines

Never expose sensitive information:

- ❌ No Admin API keys in frontend code
- ❌ No API keys in version control
- ✅ Use environment variables for all API keys
- ✅ Use Search-Only keys for frontend
- ✅ Generate Secured API Keys on backend for multi-tenancy

Search-Only keys are safe for frontend exposure. Admin keys must remain on backend only. Secured API Keys should have expiration (`validUntil`).

## Performance Considerations

**Batch Size**: 1,000-100,000 records depending on record size (max 10MB per batch). Monitor indexing latency to find optimal batch size.

**Index Size**: Use `filterOnly` for attributes used only for filtering, exclude unnecessary attributes, monitor index size in dashboard.

**Query Debouncing**: 300ms delay after user stops typing. Adjust based on user experience requirements.

**Caching**: Leverage built-in InstantSearch caching, implement application-level caching for frequently accessed results, use CDN caching for static search result pages (SSR).

## Notes

Algolia uses a "tie-breaking" ranking algorithm: Typo → Geo → Words → Filters → Proximity → Attribute → Exact → Custom. The first 7 criteria are highly optimized defaults. Focus custom ranking efforts on the Custom step.

Record size limits vary by plan: typically 10KB-100KB. Federated search (multi-index) is supported via parallel queries. A/B testing requires replica indices and dashboard configuration. Insights API enables personalization based on historical click/conversion data.
