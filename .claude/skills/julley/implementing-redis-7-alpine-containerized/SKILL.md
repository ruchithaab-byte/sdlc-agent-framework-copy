---
name: implementing-redis-7-alpine-containerized
description: Implements secure, high-performance Redis 7 deployments on Alpine Linux containers. Handles musl/glibc compatibility, connection pooling, security hardening, and resource optimization.
version: 1.0.0
dependencies:
  - redis>=7.0.0
  - redis-py>=5.0.0
---

# Implementing Redis 7-Alpine Containerized Deployment

## Overview
This skill implements Redis 7 in Alpine Linux containers, focusing on architectural patterns required for this environment: `musl` vs `glibc` compatibility, container network isolation, and high-performance connection strategies.

## When to Use
Use this skill when:
*   Deploying Redis 7 images (specifically `redis:7-alpine`) in Docker or Kubernetes.
*   Optimizing containerized Redis for low latency and high throughput.
*   Securing Redis instances that are running within shared container networks.
*   Troubleshooting Alpine-specific compatibility issues with client applications.

## Quick Start

### 1. Build & Environment
Alpine uses `musl libc`, which conflicts with `glibc` dependencies (common in Python/Node apps).
*   **Action**: Use a Multi-Stage Docker Build.
*   **Resource**: See [Multi-Stage Dockerfile Template](TEMPLATES.md#multi-stage-dockerfile-template).
*   **Reference**: [Alpine & musl Compatibility](REFERENCE.md#alpine--musl-libc-compatibility).

### 2. Security Hardening
Containerized Redis must never be exposed publicly.
*   **Action**: Configure network isolation and disable the `CONFIG` command.
*   **Resource**: See [Security Configuration Template](TEMPLATES.md#security-configuration-redisconf).
*   **Reference**: [Container Security](REFERENCE.md#container-security).

### 3. Connection Management
Connection overhead is significant in container networks.
*   **Action**: Implement Connection Pooling (Python/Go) or Multiplexing (Node.js).
*   **Resource**: See [Connection Pooling Setup](TEMPLATES.md#client-configuration).
*   **Reference**: [Connection Management Details](REFERENCE.md#connection-management).

## Implementation Workflow

### Step 1: Data Durability
Containers are ephemeral. Configure AOF persistence and volume mounts to preventing data loss.
*   **Pattern**: Enable `appendonly yes` with `everysec` sync.
*   **Requirement**: Mount external volume to `/data`.
*   **Reference**: [Persistence Strategy](REFERENCE.md#persistence-strategy).

### Step 2: Performance Optimization
*   **Bulk Ops**: Use **Pipelining** to amortize RTT. [Template](TEMPLATES.md#pipelining-python).
*   **Complex Logic**: Use **Lua Scripts** with `EVALSHA`. [Template](TEMPLATES.md#lua-script-pre-loading-and-evalsha-go).
*   **Structure**: Use `HASH` instead of JSON strings for atomic updates. [Template](TEMPLATES.md#hash-data-structure-usage).

### Step 3: Reliability & Scaling
*   **Stampede Prevention**: Implement "Cache-Aside with Mutex" for hot keys. [Template](TEMPLATES.md#cache-stampede-mutex-command-template).
*   **Hot Key Sharding**: Distribute heavy keys across shards. [Template](TEMPLATES.md#key-sharding-template).
*   **Memory Safety**: Enforce TTLs and use `allkeys-lfu` eviction policy.

## Common Pitfalls (Anti-Patterns)
*   ❌ **Blocking**: Using `KEYS` command in production (blocks server). Use `SCAN`.
*   ❌ **Latency**: Creating a new connection for every request. Use Pools.
*   ❌ **Security**: Exposing port 6379 to host/internet.
*   ❌ **Compatibility**: Installing `glibc` directly on Alpine (unstable).

See [REFERENCE.md#common-anti-patterns](REFERENCE.md#common-anti-patterns) for full list and mitigations.
