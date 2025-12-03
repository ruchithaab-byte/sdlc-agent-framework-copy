# Deployment Configuration

## Vercel / Standalone (PPR)

Enable Partial Prerendering and standalone output.

```typescript
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    ppr: true,
  },
  output: 'standalone',
};

export default nextConfig;
```

## Self-Hosting Cache

**Requirement**: In multi-replica environments, externalize `.next/cache` to shared storage (Redis/S3) to avoid cache inconsistencies.

