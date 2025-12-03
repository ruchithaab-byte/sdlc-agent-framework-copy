# Backend Integration (Reactor)

Ably Reactor enables asynchronous integration between Ably channels and external services.

See [SKILL.md](SKILL.md) for overview.

## Webhook Batching

**Pattern**: Outbound Webhooks for reactive processing

**Best Practice**: Batched Webhooks (prevents Chatty I/O)

**Anti-Pattern**: Unbatched webhooks causing endpoint overload

### Webhook Batching Configuration

```javascript
// Ably Dashboard Configuration (or API)
// Webhook Rule Configuration:
{
  "channelFilter": "events:*",
  "ruleType": "http",
  "requestMode": "batch",  // Critical: Use batch mode
  "batch": {
    "maxBatchSize": 100,
    "maxBatchInterval": 1000  // Max once per second
  },
  "targetUrl": "https://api.example.com/webhooks/ably"
}

// Backend endpoint handles batched payload
app.post('/webhooks/ably', (req, res) => {
  // req.body is array of events
  const events = req.body;
  events.forEach(event => {
    processEvent(event);
  });
  res.status(200).send();
});
```

**Best Practice**: Always use batched webhooks in high-throughput environments. Single-request mode can overwhelm endpoints and hit concurrency limits. Batching reduces request volume and provides resilience against traffic spikes.

## Outbound Streaming

**Pattern**: Outbound Streaming for data pipelines

```javascript
// Configured via Ably Dashboard
// Streams constant flows to external services
// Suitable for high-throughput, queueing, or broadcast scenarios
```

## REST Publishing Workarounds

Ably guarantees message ordering for REST API, but high-rate publishing via separate HTTP requests may arrive out of order due to network factors.

**Workaround**: Message batching for strict ordering requirements

**Workaround**: Rate limiting to prevent out-of-order delivery

### REST Batch Publishing

```javascript
const rest = new Ably.Rest({ key: process.env.ABLY_API_KEY });
const channel = rest.channels.get('events:stream');

// Batch multiple order-dependent messages in single request
async function publishOrderedBatch(messages) {
  // Package sequential messages into single REST request
  const batch = messages.map(msg => ({
    name: msg.name,
    data: msg.data
  }));
  
  // Single request ensures ordering within batch
  await channel.publish(batch);
}
```

### Rate Limiting

```javascript
// Application-level rate limiting
let lastPublishTime = 0;
const MIN_INTERVAL = 100; // 100ms between publishes

async function rateLimitedPublish(channel, message) {
  const now = Date.now();
  const elapsed = now - lastPublishTime;
  
  if (elapsed < MIN_INTERVAL) {
    await new Promise(resolve => setTimeout(resolve, MIN_INTERVAL - elapsed));
  }
  
  await channel.publish(message.name, message.data);
  lastPublishTime = Date.now();
}
```

**Best Practice**: For strict ordering requirements, batch order-dependent messages into single REST requests. Implement application-level rate limiting to reduce concurrency risk of requests crossing paths.

## Performance Considerations

**Webhook Processing**:
- Always enable batching for high-throughput webhook scenarios
- Configure appropriate batch size and interval based on endpoint capacity
- Monitor webhook endpoint health and implement retry logic

**Message Publishing**:
- Use Realtime SDK for high-throughput, ordered publishing
- If REST must be used, implement batching for order-dependent messages
- Apply rate limiting to prevent out-of-order delivery

