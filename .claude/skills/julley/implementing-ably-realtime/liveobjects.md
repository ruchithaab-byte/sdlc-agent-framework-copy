# LiveObjects & CRDT Pattern

LiveObjects provides high-level pattern for managing shared data with automatic conflict resolution using CRDTs.

See [SKILL.md](SKILL.md) for overview.

## Pattern Overview

**Pattern**: Push Operations (delta updates) over Push State

**Best Practice**: Echo-based consistency (wait for authoritative echo)

**Anti-Pattern**: Monolithic Persistence (using LiveObjects as sole data store)

## LiveObjects Setup

```javascript
import { Realtime } from 'ably';
import { LiveObject } from '@ably/liveobjects';

const ably = new Realtime({ authUrl: '/api/ably-token' });
const liveObject = new LiveObject('shared:document_123', ably);

// Subscribe to operations (delta updates, not full state)
liveObject.subscribe((operation) => {
  // Apply operation to local object
  liveObject.applyOperation(operation);
});

// Publish operation (not full state)
liveObject.publishOperation({
  type: 'update',
  path: 'title',
  value: 'New Title'
});

// Wait for authoritative echo before applying locally
// LiveObjects handles this automatically
```

## Best Practices

**Delta Updates**: LiveObjects broadcasts only operations (deltas), not full state. This is bandwidth-efficient.

**Echo-based Consistency**: Operations are echoed back from Ably's authoritative state before local application, ensuring consistency.

**Distributed Cache Pattern**: Treat LiveObjects as distributed cache/state store, not primary data store. Durable, complex, or infrequently accessed data should reside in external data store.

**Best Practice**: LiveObjects uses Push Operations (delta updates) pattern, not Push State (full object), for bandwidth efficiency.

