# Architectural Patterns

## Partitioning Strategy

### Key-Based Partitioning
**Goal**: Guarantee ordering for specific entities (e.g., all events for `User:123` must be ordered).

```python
key = user_id  # Immutable ID
producer.produce(topic, key=key, value=data)
```

**Hotspotting Mitigation**:
If `User:VIP` generates 1000x events:
1.  **Composite Key**: `key = f"{user_id}:{minute_bucket}"` (spreads load, loses total ordering).
2.  **Random Sharding**: If ordering isn't strictly required for that high-volume entity.

## Event Sourcing & CQRS

### Event Sourcing (Python)
Capture state changes as immutable events.

```python
# Write Segment (Command Handler)
event = OrderCreatedEvent(id=order_id, amount=100)
producer.produce('order-events', key=order_id, value=serialize(event))

# Read Segment (Event Handler)
while True:
    msg = consumer.poll(1.0)
    event = deserialize(msg.value())
    # Update Materialized View (e.g., Redis, Postgres, Elasticsearch)
    update_read_db(event)
```

### CQRS (Command Query Responsibility Segregation)
-   **Write Side**: Kafka Topic (Source of Truth).
-   **Read Side**: SQL/NoSQL Database (optimized for queries).
-   **Glue**: A Consumer application (or Kafka Streams/KSQL) that populates the Read Side.

## Stream Processing (Python)

While Kafka Streams is Java-exclusive, Python uses `faust` or standard consumer-producer loops for stateful processing.

**Pattern**: Consumer -> Transform -> Producer

```python
# Simple Python Stream Processor
consumer.subscribe(['input-topic'])

while True:
    msg = consumer.poll(1.0)
    if msg and not msg.error():
        # Transform
        words = msg.value().decode('utf-8').split()
        count = len(words)
        
        # Produce result
        producer.produce('word-counts', key=msg.key(), value=str(count))
```

## Anti-Patterns

### ❌ Mutable Keys
**Problem**: Using `email` as a key, then user changes email. New messages go to a different partition.
**Fix**: Use immutable UUIDs.

### ❌ Global Ordering Requirement
**Problem**: Expecting Topic-wide order.
**Reality**: Kafka only guarantees Partition-wide order.
**Fix**: Design system to only need causal ordering per entity (Key).

