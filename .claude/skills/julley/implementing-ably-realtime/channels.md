# Channels

Channels are the primary building blocks for Ably's Pub/Sub architecture. They are virtual and ephemeral—no pre-provisioning required.

See [SKILL.md](SKILL.md) for overview.

## Core Pub/Sub Pattern

**Pattern**: Global Pub/Sub with ephemeral channels

Channels are virtual—no pre-provisioning needed. Structure around logical groups, not per-user granularity (avoids error 90021).

```javascript
import Ably from 'ably';

// Singleton SDK instance (reuse throughout application lifecycle)
const ably = new Ably.Realtime({ authUrl: '/api/ably-token' });

// Channel is ephemeral - exists only when referenced
const channel = ably.channels.get('room:general');

// Subscribe to messages
channel.subscribe((message) => {
  console.log('Received:', message.data);
});

// Publish message
channel.publish('message', { text: 'Hello', user: 'alice' });
```

## Channel Design Strategy

**Pattern**: Logical grouping over granular channels

**Best Practice**: Structure channels around high-fan-out events

**Anti-Pattern**: Channel Proliferation leading to error 90021 (Max Channel Creation Rate Exceeded)

```javascript
// ✅ Good: Logical grouping
const channels = {
  notifications: ably.channels.get('notifications:user_123'),
  chat: ably.channels.get('chat:room_general'),
  liveData: ably.channels.get('live:sports_football')
};

// ❌ Anti-Pattern: Excessive granularity
// Don't create channels like: 'chat:user_123:session_456:message_789'
```

**Best Practice**: Channels should reflect sustainable communication patterns. Use channel parameters or message metadata for fine-grained routing within a channel rather than creating new channels.

## Channel Scoping

Structure channels around logical groups for scalability. Monitor channel creation rate to avoid error 90021.

**Best Practice**: Use channel parameters or message metadata for fine-grained routing rather than creating excessive channels.

