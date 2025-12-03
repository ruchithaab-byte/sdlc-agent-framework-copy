# Anti-Patterns

Critical anti-patterns to avoid when implementing Ably realtime messaging.

See [SKILL.md](SKILL.md) for overview.

## 1. Channel Proliferation

**Problem**: Creating excessively granular channels (e.g., per-user, per-session) results in constant metadata management overhead and triggers error 90021 (Max Channel Creation Rate Exceeded).

**Solution**: Structure channels around logical groups or high-fan-out events.

**Example**:
```javascript
// ❌ Anti-Pattern: Excessive granularity
'chat:user_123:session_456:message_789'

// ✅ Good: Logical grouping
'chat:room_general'
'notifications:user_123'
```

## 2. Retry Storm

**Problem**: Clients retry failed requests too frequently without sufficient delay, overwhelming connection endpoints and triggering errors 42910, 42922 (Rate limit exceeded).

**Solution**: Implement exponential backoff and rely on SDK's built-in reconnection attempts.

## 3. Improper Instantiation

**Problem**: Repeatedly creating and destroying Ably SDK objects leads to high connection overhead and triggers error 80021 (Max New Connections Rate Exceeded).

**Solution**: Treat SDK instance as Singleton throughout application lifecycle.

```javascript
// ❌ Anti-Pattern: Multiple instances
const ably1 = new Ably.Realtime({ authUrl: '/api/ably-token' });
const ably2 = new Ably.Realtime({ authUrl: '/api/ably-token' });

// ✅ Good: Singleton pattern
const ably = new Ably.Realtime({ authUrl: '/api/ably-token' });
// Reuse 'ably' throughout application
```

## 4. Chatty I/O / Unbatched REST

**Problem**: Continually sending many small network requests via HTTP REST results in low throughput, variable latency, and risk of message reordering.

**Solution**: Use Realtime SDK for ordered, high-throughput publishing. If REST must be used, implement batching.

## 5. Basic Auth on Client-Side

**Problem**: Exposing persistent API keys on client-side provides indefinite, full configured access rights, rendering system vulnerable to exploitation.

**Solution**: Mandatory: Use token authentication for all client-side applications.

```javascript
// ❌ Anti-Pattern: API key on client
const ably = new Ably.Realtime({ key: 'api-key-here' });

// ✅ Good: Token authentication
const ably = new Ably.Realtime({ authUrl: '/api/ably-token' });
```

## 6. Ignored State Loss

**Problem**: Failing to implement History API recovery when channel reattachment has `resumed: false` leads to permanent data loss (messages published during suspension are not queued).

**Solution**: Always check resume flag and recover history immediately.

```javascript
channel.on('attached', async (stateChange) => {
  if (stateChange.resumed === false) {
    // ❌ Anti-Pattern: Ignore state loss
    // ✅ Good: Recover history
    const history = await channel.history({ limit: 100 });
    history.items.reverse().forEach(message => {
      processMessage(message);
    });
  }
});
```

## 7. Monolithic Persistence

**Problem**: Using Ably's message persistence or LiveObjects storage as the sole data store for data with vastly different usage patterns.

**Solution**: Treat LiveObjects as distributed, synchronized cache/state store. Durable, complex, or infrequently accessed data should reside in external data store.

## 8. Ignored Outbound Backpressure

**Problem**: Failing to account for subscriber connection capacity limitations. When outbound message rate exceeds connection capacity, Ably forcibly detaches channels (error 80020).

**Solution**: Reduce message volume per client or implement fan-in aggregation service.

