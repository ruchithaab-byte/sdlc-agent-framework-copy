---
name: implementing-kafka-production
description: Implements Apache Kafka production deployments using Python best practices. Covers Reliable Producer (acks=all), Consumer Groups (1:1 ratio), Schema Registry (Avro), and HA/DR configurations. Use for setting up event-driven architectures, real-time pipelines, or fixing Kafka performance/reliability issues.
version: 1.0.0
dependencies:
  - kafka-python>=2.0.0
  - confluent-kafka>=2.0.0
---

# Implementing Kafka Production

## Overview

This skill provides production-grade patterns for Apache Kafka using **Python**. It focuses on achieving "Three-Layer Durability", ensuring High Availability (HA), and avoiding common operational pitfalls.

## Production Readiness Checklist

Copy this checklist to track your implementation status:

```markdown
## Kafka Production Checklist
**Reliability**
- [ ] Producer: `acks='all'` configured
- [ ] Producer: `retries` set to high value (MAX)
- [ ] Producer: `enable.idempotence=True`
- [ ] Topic: `replication.factor >= 3`
- [ ] Broker: `min.insync.replicas >= 2`

**Architecture**
- [ ] Keys: Used for entity ordering (no random/null keys for stateful data)
- [ ] Schema: Schema Registry integrated (Avro/Protobuf)
- [ ] Consumers: Manual offset management (No auto-commit)
- [ ] Consumers: Count <= Partition Count

**Operations**
- [ ] HA: `broker.rack` configured for zone awareness
- [ ] DR: MirrorMaker 2 configured (if multi-region)
```

## Detailed Guides

| Topic | Description | Link |
|-------|-------------|------|
| **Producers** | Reliability settings, durability guarantees, async sending | [PRODUCER.md](PRODUCER.md) |
| **Consumers** | Group design, lag mitigation, internal queues | [CONSUMER.md](CONSUMER.md) |
| **Patterns** | Partitioning, Event Sourcing, CQRS, Stream Processing | [PATTERNS.md](PATTERNS.md) |
| **Schema** | Schema Registry, Avro integration, evolution rules | [SCHEMA.md](SCHEMA.md) |
| **Operations** | High Availability (HA) and Disaster Recovery (DR) | [OPERATIONS.md](OPERATIONS.md) |

## Transformation Rules

1.  **Durability**: Always align Producer (`acks=all`), Topic (`RF=3`), and Broker (`min.insync=2`).
2.  **Ordering**: Only guaranteed per partition. Use **Keys** effectively.
3.  **Performance**: Throughput (Producer batching) vs. Latency (`linger.ms`).
4.  **Lag**: Usually a consumer application issue. Use internal queues to unblock the poll loop.

## Quick Example: Production Producer

```python
from confluent_kafka import Producer

# Safe, Durable Producer Config
conf = {
    'bootstrap.servers': 'host:9092',
    'acks': 'all',
    'enable.idempotence': True,
    'compression.type': 'lz4'
}

producer = Producer(conf)
```

For full implementation details, see [PRODUCER.md](PRODUCER.md).
