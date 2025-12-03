---
name: implementing-ably-realtime
description: Implements Ably realtime messaging with Pub/Sub patterns, token authentication, presence management, and LiveObjects. Use when building chat, notifications, collaborative apps, or realtime features requiring state synchronization.
version: 1.0.0
dependencies:
  - ably>=2.0.0
---

# Implementing Ably Realtime

Ably provides globally distributed Pub/Sub with exactly-once delivery, guaranteed ordering, and automatic multi-region failover.

## Quick Start

**Basic Pub/Sub**:

```javascript
import Ably from 'ably';

const ably = new Ably.Realtime({ authUrl: '/api/ably-token' });

const channel = ably.channels.get('room:general');

channel.subscribe((message) => {
  console.log('Received:', message.data);
});

channel.publish('message', { text: 'Hello' });
```

## Core Patterns

**Authentication**:
- Client-side: Token auth mandatory (see [authentication.md](authentication.md))
- Server-side: Basic auth with API keys

**Connection Resilience**:
- Automatic reconnection with 2-minute state retention
- History API recovery for suspended state (see [connection-resilience.md](connection-resilience.md))

**Channel Design**:
- Structure around logical groups, not per-user
- Avoid channel proliferation (error 90021)
- Details: [channels.md](channels.md)

**LiveObjects & CRDTs**:
- Push operations (deltas), not full state
- Echo-based consistency
- See [liveobjects.md](liveobjects.md)

**Presence Management**:
- Realtime subscriptions for live awareness
- REST API for occupancy snapshots
- See [presence.md](presence.md)

**Backend Integration**:
- Batched webhooks (critical for high-throughput)
- Outbound streaming for data pipelines
- See [reactor.md](reactor.md)

## Critical Anti-Patterns

See [anti-patterns.md](anti-patterns.md) for detailed guidance on:

- Channel Proliferation (error 90021)
- Retry Storms (errors 42910, 42922)
- Basic Auth on Client-Side (security vulnerability)
- Ignored State Loss (data loss)

## Critical Errors

- **90021**: Channel proliferation—consolidate channels
- **42910/42922**: Rate limiting—implement exponential backoff
- **80008**: Connection suspended >2min—use History API

**Full error reference**: See [error-codes.md](error-codes.md)

## When to Use

Use this skill when:

- Implementing realtime features (chat, notifications, live updates)
- Building collaborative applications
- Handling presence and state synchronization
- Integrating with backend systems via Ably Reactor

## Prerequisites

- Ably account with API keys
- Backend for token generation (client-side auth)
- Client-side framework (React, Vue, vanilla JS) or backend requirements

## Examples

**Basic patterns**: See code above

**Advanced scenarios**: See [examples.md](examples.md) for:

- Resilient chat implementation
- Backend webhook integration

## Security and Guidelines

**CRITICAL**: Never hardcode sensitive information:
- ❌ No API keys in client-side code
- ❌ No API keys in SKILL.md or example code
- ❌ No credentials in version control
- ✅ Use environment variables for all API keys
- ✅ Use token authentication for all client-side applications
- ✅ Generate tokens on backend with appropriate capabilities and TTL
- ✅ Route sensitive operations through secure backend channels

**Operational Constraints**:
- Token authentication is mandatory for client-side (browsers, mobile devices)
- Basic authentication (API keys) is suitable for trusted server-side only
- Tokens should have appropriate TTL (typically 1 hour) and be renewed before expiration
- Monitor token generation service availability (dependency for client connectivity)
- Use Search-Only API keys for read-only operations when available

## Dependencies

This skill requires the following packages (listed in frontmatter):
- `ably>=2.0.0`: Core Ably JavaScript/TypeScript client for realtime and REST operations

**Note**: For API-based deployments, all dependencies must be pre-installed in the execution environment. The skill cannot install packages at runtime.

**Additional Framework-Specific Libraries** (as needed):
- `@ably/liveobjects`: For LiveObjects functionality (if using LiveObjects feature)
- Framework-specific Ably integrations may be available for React, Vue, etc.

## Related Resources

- Ably Documentation: https://ably.com/documentation
- Ably API Reference: https://ably.com/documentation/rest-api
- Ably Reactor Documentation: https://ably.com/documentation/general/reactor
- Ably Error Codes: https://ably.com/documentation/general/errors

## Notes

- Ably provides exactly-once delivery semantics with 99.999999% (eight nines) message survivability guarantee
- Strong message ordering is guaranteed for persistently connected subscribers using Realtime client libraries
- Connection state is retained for maximum 2 minutes during disconnection. Beyond this, state is lost (suspended) and requires History API recovery
- Channels are ephemeral and virtual - no pre-provisioning required. They exist only when referenced in publisher or subscriber operations
- LiveObjects uses Push Operations (delta updates) pattern, not Push State (full object), for bandwidth efficiency
- Presence requires ClientId and appropriate presence capability in authentication token
- Webhook batching is critical for high-throughput scenarios to prevent endpoint overload and concurrency limit issues
