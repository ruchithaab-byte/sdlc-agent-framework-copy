# Redis 7-Alpine Implementation Reference

## Core Concepts & Environment

### Alpine & musl libc Compatibility
The `redis:7-alpine` image uses `musl libc` instead of `glibc` to achieve its small footprint (~5MB). This creates compatibility issues for applications or client libraries compiled against `glibc` (e.g., standard Python wheels, Node.js binaries).

**The Multi-Stage Build Pattern**:
To resolve this without bloating the image:
1.  **Builder Stage**: Use a full `glibc` image (like `python:3.11-slim`) to compile dependencies.
2.  **Runtime Stage**: Copy only the necessary artifacts and shared libraries to the Alpine image.

**Anti-Pattern**: Do not try to install `glibc` directly on Alpine or include build tools in the final image.

### Container Security
Redis is insecure by default. In containerized environments:

1.  **Network Isolation**: Never expose Redis ports (`6379`) to the host or public internet. Use internal Docker networks or Kubernetes ClusterIP services. Only trusted application containers should reach Redis.
2.  **CONFIG Command**: The `CONFIG` command allows runtime configuration changes, including directory paths. Attackers can use this to write malicious RDB files (e.g., SSH keys) to the host filesystem. Disable or rename it in `redis.conf`.

### Connection Management
Container networking adds latency (RTT). Opening a new TCP connection for every command is a major performance bottleneck.

1.  **Connection Pooling**: Initialize a pool at startup and reuse connections. Size the pool based on `(concurrent_requests * avg_duration_ms) / 1000 * safety_factor`.
2.  **Multiplexing**: For event-driven runtimes (Node.js), use a single shared connection that multiplexes commands.

**Impact**: Connection reuse can increase throughput from ~4 ops/sec (with connect overhead) to thousands.

### Persistence Strategy
Containers are ephemeral. Data in memory is lost on restart.

*   **AOF (Append Only File)**: Logs every write operation. Higher durability. Use `appendfsync everysec` for the best balance of safety and speed.
*   **Volume Mounts**: You **MUST** mount a persistent volume (Docker Volume or K8s PVC) to `/data` to preserve AOF/RDB files across container restarts.

## High-Performance Patterns

### Pipelining
Sends multiple commands without waiting for replies, reading all replies at the end. This amortizes the RTT cost over many commands.
*   **Use for**: Bulk inserts, batch processing.
*   **Constraint**: Cannot use if a command depends on the result of a previous one in the same batch.

### Lua Scripting (EVALSHA)
Executes logic server-side atomically.
*   **Optimization**: Use `EVALSHA` instead of `EVAL`. `EVAL` sends the full script text every time (bandwidth waste). `EVALSHA` uses the SHA1 digest of the pre-loaded script.

### Data Structure Efficiency
*   **Hash vs JSON String**: Storing JSON as a string requires a full read-modify-write cycle for small updates. Using `HASH` allows atomic modification of individual fields (`HSET key field value`) without transferring the whole object.

## Reliability & Mitigation

### Cache Stampede Prevention
When a hot key expires, multiple clients might race to regenerate it, slamming the database.
**Solution**: Use a "Cache-Aside with Mutex" pattern.
1.  Check cache.
2.  If miss, try to acquire atomic lock (`SET NX EX`).
3.  If lock acquired: query DB, update cache, release lock.
4.  If lock busy: wait/retry.

### Hot Keys & Sharding
A single hot key can overwhelm one Redis shard (even in Cluster mode).
**Workaround**: Application-side Key Sharding.
*   Append a suffix to the key (`key:shard:1`, `key:shard:2`).
*   Distribute reads/writes across shards.
*   **Trade-off**: Complexity in aggregation.

### Memory Management
*   **TTL**: Always set Time-To-Live. Without it, memory grows indefinitely until eviction.
*   **Eviction Policies**:
    *   `allkeys-lfu`: Best for hot-key protection. Evicts least frequently used.
    *   `volatile-lru`: Best when using Redis as a pure cache for some keys while keeping others persistent.
    *   `noeviction`: Dangerous. Redis returns errors on write when full.

## Troubleshooting & Anti-Patterns

### Common Anti-Patterns
| Anti-Pattern | Impact | Solution |
|--------------|--------|----------|
| **KEYS Command** | Blocks server (O(N)), potential downtime. | Use `SCAN` for incremental iteration. |
| **No TTL** | Memory exhaustion, OOM kills. | Enforce TTL on all cache keys. |
| **Public Exposure** | Data breach, system compromise. | Internal networks only. |
| **JSON Strings** | High bandwidth, race conditions on update. | Use `HASH` or RedisJSON. |
| **Connect-per-op** | High latency (RTT overhead). | Use Connection Pools. |

### Error Handling
*   **Connection Pool Exhaustion**: Manifests as timeout errors. Solution: Increase pool size or check for leaked connections (not returned to pool).
*   **musl Compatibility**: Manifests as `Symbol not found` or `ImportError`. Solution: Use multi-stage builds (see Templates).
*   **Memory Fragmentation**: `mem_fragmentation_ratio > 1.5`. Solution: Run `MEMORY PURGE` (impacts performance temporarily).

### Performance Baseline
Measure intrinsic latency to set expectations:
`redis-cli --latency`
This accounts for container/kernel overhead. Do not expect performance better than this baseline.

