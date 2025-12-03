# Schema Management

Centralized schema management prevents "Schema Drift" and runtime deserialization errors.

## Schema Registry Integration (Python)

Using `confluent-kafka` with Avro.

### Producer with Avro

```python
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

schema_registry_conf = {'url': 'http://schema-registry:8081'}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

avro_serializer = AvroSerializer(schema_registry_client,
                                 schema_str,
                                 to_dict_function)

producer_conf = {
    'bootstrap.servers': 'broker:9092',
    'key.serializer': StringSerializer('utf_8'),
    'value.serializer': avro_serializer
}

producer = SerializingProducer(producer_conf)
```

### Consumer with Avro

```python
from confluent_kafka.schema_registry.avro import AvroDeserializer

avro_deserializer = AvroDeserializer(schema_registry_client,
                                     schema_str,
                                     from_dict_function)

consumer_conf = {
    'bootstrap.servers': 'broker:9092',
    'group.id': 'my-group',
    'key.deserializer': StringDeserializer('utf_8'),
    'value.deserializer': avro_deserializer
}
```

## Compatibility Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **BACKWARD** | New consumers can read old data. | **Default/Best**. Upgrade consumers first, then producers. |
| **FORWARD** | Old consumers can read new data. | Upgrade producers first. |
| **FULL** | Both ways supported. | Hardest to maintain, highest safety. |

## Anti-Patterns

### ❌ Ignoring Schema Evolution
**Risk**: Producer changes field type (int -> string), Consumer crashes on read.
**Fix**: Use Schema Registry to enforce compatibility checks at produce time.

### ❌ Ad-Hoc JSON
**Risk**: No contract. Fields disappear or change randomly.
**Fix**: Use strict schemas (Avro/Protobuf) for inter-team topics.

