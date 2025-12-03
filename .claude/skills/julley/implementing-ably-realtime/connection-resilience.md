# Connection Resilience

Client-side resilience is paramount in realtime applications where unreliable network conditions are common. Ably SDKs handle connection lifecycle automatically.

See [SKILL.md](SKILL.md) for overview.

## Automatic Reconnection

**Pattern**: Automatic reconnection with state retention (2-minute window)

**Best Practice**: Exponential backoff for custom retry logic

**Anti-Pattern**: Retry Storm (errors 42910, 42922)

**Workaround**: History API recovery for suspended state (resumed: false)

## Connection State Management

```javascript
const ably = new Ably.Realtime({ authUrl: '/api/ably-token' });
const channel = ably.channels.get('chat:room1');

// Monitor connection state
ably.connection.on((stateChange) => {
  if (stateChange.current === 'suspended') {
    // Connection lost for >2 minutes - state is lost
    console.warn('Connection suspended - state lost');
  }
});

// Handle channel attachment with resume flag
channel.on('attached', (stateChange) => {
  if (stateChange.resumed === false) {
    // State continuity lost - recover missing messages
    recoverChannelHistory(channel);
  }
});

// History API recovery workaround
async function recoverChannelHistory(channel) {
  const history = await channel.history({ limit: 100 });
  history.items.forEach(message => {
    // Process missed messages
    handleMessage(message);
  });
}
```

**Best Practice**: Ably retains connection state for 2 minutes. If disconnected longer, implement History API recovery immediately upon reattachment with `resumed: false`. Use exponential backoff for any custom retry logic to prevent retry storms.

## History API Recovery

When channel reattachment has `resumed: false` (indicating state continuity loss), immediately retrieve missing message backlog using History API.

```javascript
channel.on('attached', async (stateChange) => {
  if (stateChange.resumed === false) {
    const history = await channel.history({ limit: 100 });
    history.items.reverse().forEach(message => {
      processMessage(message);
    });
  }
});
```

This recovers messages published during extended disconnection beyond the 2-minute retention window.

## Exponential Backoff

Use exponential backoff with jitter for any custom retry logic (token acquisition, bootstrapping). Prevents retry storms and respects rate limits.

**Best Practice**: Monitor connection state to detect suspended state and trigger recovery workflows. Subscribe to connection and channel state change events.

