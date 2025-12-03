# Presence Management

Presence allows applications to track which clients or devices are present on a channel in realtime.

See [SKILL.md](SKILL.md) for overview.

## Realtime Presence

**Pattern**: Realtime presence subscriptions for live awareness

**Workaround**: REST API for historical occupancy snapshots

## Presence Management Template

```javascript
const channel = ably.channels.get('chat:room1');

// Enter presence set (requires ClientId and presence capability)
channel.presence.enter({ name: 'Alice', status: 'available' });

// Subscribe to presence events
channel.presence.subscribe((presenceMessage) => {
  if (presenceMessage.action === 'enter') {
    console.log(`${presenceMessage.data.name} joined`);
  } else if (presenceMessage.action === 'leave') {
    console.log(`${presenceMessage.data.name} left`);
  }
});

// Update presence
channel.presence.update({ status: 'away' });

// Leave presence set
channel.presence.leave();
```

## REST API for Occupancy

**Workaround**: REST API for historical occupancy snapshots

```javascript
// Server-side: Get occupancy snapshot without persistent connection
const rest = new Ably.Rest({ key: process.env.ABLY_API_KEY });
const presence = await rest.channels.get('chat:room1').presence.get();
console.log(`Current occupants: ${presence.length}`);
```

**Best Practice**: Use realtime presence for live awareness. Use REST API for one-time occupancy checks or historical snapshots without maintaining persistent connections.

## Requirements

Presence requires ClientId and appropriate presence capability in authentication token.

