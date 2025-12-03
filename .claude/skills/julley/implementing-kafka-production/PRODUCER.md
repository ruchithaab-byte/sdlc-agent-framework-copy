# Producer Reliability

## Reliable Producer Configuration

To achieve the "Three-Layer Durability" guarantee, configure the Python producer (`confluent-kafka` or `kafka-python`) as follows.

### Python Implementation (`confluent-kafka`)

```python
from confluent_kafka import Producer
import socket

conf = {
    'bootstrap.servers': 'kafka-broker1:9092,kafka-broker2:9092',
    'client.id': socket.gethostname(),
    
    # Durability Configuration (Mandatory for critical data)
    'acks': 'all',                  # Wait for all ISR
    'enable.idempotence': True,     # Prevents duplicates, ensures ordering
    'max.in.flight.requests.per.connection': 5,
    'retries': 2147483647,          # Integer.MAX_VALUE equivalent
    
    # Performance Configuration
    'compression.type': 'lz4',
    'linger.ms': 10,                # Wait up to 10ms for batching
    'batch.size': 32768,            # 32KB batches
}

producer = Producer(conf)

def acked(err, msg):
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message produced to: {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

# Asynchronous send
producer.produce('my-topic', key='key', value='value', callback=acked)
producer.poll(0)
producer.flush()
```

### Three-Layer Durability Alignment

1.  **Producer**: `acks='all'` ensures leader waits for all In-Sync Replicas.
2.  **Topic**: `replication.factor >= 3` provides redundancy.
3.  **Broker**: `min.insync.replicas >= 2` enforces minimum ISR requirement.

## Anti-Patterns to Avoid

### ❌ Using `acks=0` or `acks=1`
**Risk**: Data loss. `acks=0` sends and forgets. `acks=1` waits only for leader, losing data if leader crashes before replication.
**Fix**: Always use `acks='all'` for critical paths.

### ❌ Not Configuring Retries
**Risk**: Transient network blips cause dropped messages.
**Fix**: Set `retries` to strict max (or very high) and enable idempotence to handle duplicates safe.

### ❌ Misaligned Durability
**Risk**: Producer waits for "all", but "all" is just 1 replica if `min.insync.replicas` is default (1).
**Fix**: Ensure Broker/Topic config matches Producer expectations.

