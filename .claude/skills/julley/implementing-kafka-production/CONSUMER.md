# Consumer Group Design & Lag Mitigation

## Consumer Configuration

Optimal consumer design balances parallelism (1:1 consumer-to-partition ratio) with data safety (manual offsets).

### Python Implementation (`confluent-kafka`)

```python
from confluent_kafka import Consumer, KafkaError, KafkaException
import sys

conf = {
    'bootstrap.servers': 'kafka-broker1:9092',
    'group.id': 'my-transaction-processor-group',
    'auto.offset.reset': 'earliest',
    
    # Data Safety: Disable auto-commit
    'enable.auto.commit': False
}

consumer = Consumer(conf)

def process_records(msg):
    # Your processing logic here
    pass

try:
    consumer.subscribe(['InputTopicName'])

    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None: continue

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                raise KafkaException(msg.error())
        
        # Process first
        process_records(msg)
        
        # Commit offsets explicitly after successful processing
        consumer.commit(asynchronous=True)

finally:
    consumer.close()
```

## Internal Queue Pattern (Lag Mitigation)

If processing is slow (e.g., external API calls), decouple consumption from processing to prevent rebalancing timeouts and allow batching.

```python
import threading
import queue
from confluent_kafka import Consumer

# Buffer for internal processing
internal_queue = queue.Queue(maxsize=1000)

def consumer_thread():
    c = Consumer(conf)
    c.subscribe(['topic'])
    while True:
        msg = c.poll(1.0)
        if msg:
             # Fast: Put in queue and commit
             # Note: For strong exactly-once, you might need to coordinate commits
             # with the processor, but for throughput:
             if not msg.error():
                 internal_queue.put(msg)
                 c.commit(asynchronous=True)

def processor_thread():
    while True:
        msg = internal_queue.get()
        # Slow processing here
        slow_api_call(msg)
        internal_queue.task_done()
```

## Anti-Patterns

### ❌ Over-Provisioning Consumers
**Problem**: Starting 20 consumers for a topic with 10 partitions.
**Impact**: 10 consumers sit idle, wasting memory and connections.
**Fix**: `Consumer Count <= Partition Count`.

### ❌ Auto-Commit on Critical Data
**Problem**: Consumer crashes after auto-commit but before processing finishes.
**Impact**: Message lost forever.
**Fix**: `enable.auto.commit=False` and commit only after processing.

### ❌ Blocking the Poll Loop
**Problem**: Doing a 30s HTTP request inside the loop.
**Impact**: Kafka thinks consumer is dead (heartbeat timeout) and triggers rebalance ("stop-the-world").
**Fix**: Use the Internal Queue pattern or async I/O.

