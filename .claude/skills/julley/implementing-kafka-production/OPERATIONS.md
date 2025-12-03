# Operations: HA & DR

## High Availability (HA)

HA ensures the cluster survives single-broker or rack failures. This is primarily server-side configuration.

### Broker Configuration (`server.properties`)

```properties
# Rack Awareness: Distribute replicas across zones/racks
broker.rack=us-east-1a

# Replication Basics
default.replication.factor=3     # Survive 2 failures
min.insync.replicas=2            # Enforce durability
unclean.leader.election.enable=false  # Prevent data loss over availability
```

### Monitoring Checklist
-   [ ] **Under-replicated partitions**: Should be 0.
-   [ ] **ISR Shrinkage**: Alert if ISR count < Replication Factor.
-   [ ] **Controller Count**: Should be exactly 1 active controller.

## Disaster Recovery (DR)

DR protects against region-wide outages using Active-Passive replication.

### MirrorMaker 2 (MM2) Configuration

MM2 comes with Kafka and is configured via `mm2.properties`.

```properties
clusters = primary, dr
primary.bootstrap.servers = broker-primary:9092
dr.bootstrap.servers = broker-dr:9092

# Enable replication
primary->dr.enabled = true
primary->dr.topics = .*
# Important: Replicate consumer group offsets for failover
primary->dr.sync.group.offsets.enabled = true
primary->dr.sync.group.offsets.interval.seconds = 5
```

## Anti-Patterns

### ❌ Insufficient Replication
**Risk**: `replication.factor=2` allows only 1 failure.
**Fix**: Use 3+ for production.

### ❌ Synchronous Geo-Replication
**Risk**: Latency kills performance.
**Fix**: Use async replication (MM2) for DR.

### ❌ Ignoring Client Failover
**Risk**: Replicating data but not consumer offsets. When failover happens, consumers reprocess years of data.
**Fix**: Sync offsets via MM2 and practice the failover switch (pointing clients to DR URL).

