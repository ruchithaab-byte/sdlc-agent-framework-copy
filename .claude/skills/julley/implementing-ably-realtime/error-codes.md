# Error Codes

Comprehensive error handling reference for Ably realtime messaging.

See [SKILL.md](SKILL.md) for overview.

## 401xx - Authentication & Security

- **40170** (Error from client token callback): Indicates failure or latency in application's external token issuance service. Verify token server availability and response time.

## 429xx - Rate Limits / Throttling

- **42910, 42922** (Rate limit exceeded; request rejected): Application publisher or subscriber has exceeded defined account rate limits. Implement exponential backoff and reduce request frequency.

## 800xx - Connection Resilience

- **80008** (Unable to recover connection): Client remained disconnected longer than 2-minute retention window (Suspended State). Requires History API intervention to recover missed messages.

- **80020** (Continuity loss due to maximum subscribe message rate exceeded): Outbound message rate exceeded connection capacity. Reduce message volume per client or implement fan-in aggregation.

- **80021** (Max New Connections Rate Exceeded): Too many new connections created. Reuse SDK instance (Singleton pattern) instead of creating multiple instances.

## 900xx - Channel Management

- **90021** (Max Channel Creation Rate Exceeded): Symptom of Channel Proliferation anti-pattern. Review channel scoping strategy and consolidate granular channels.

- **90003** (Unable to recover channel - messages expired): Messages expired during extended disconnection. Implement History API recovery with appropriate limit before messages expire.

## 720xx - Reactor / Ingress Failure

- **72003** (Ingress cannot connect to database): External database connectivity failure related to LiveSync or Reactor configuration. Check database credentials, connection requirements, and network accessibility.

