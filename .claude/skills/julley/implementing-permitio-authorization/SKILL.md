---
name: implementing-permitio-authorization
description: Implements Permit.io authorization in Java Spring Boot using local PDP sidecars. Covers async tenant/user sync via Admin SDK, fail-closed permission checks, and best practices for latency and multi-tenancy.
version: 1.0.0
dependencies:
  - permit-sdk-java>=2.0.0
  - "permitio/pdp-v2:latest (Docker)"
---

# Implementing Permit.io Authorization (Java/Spring Boot)

## Overview

Implements Permit.io RBAC and ReBAC in Java Spring Boot applications using a sidecar Policy Decision Point (PDP) architecture. This setup ensures sub-millisecond authorization checks by decoupling policy enforcement (local PDP) from management (cloud).

## When to Use

Use this skill when:
- Implementing authorization in Java Spring Boot microservices
- Enforcing RBAC/ReBAC in multi-tenant applications
- Deploying Policy Decision Points (PDP) for low-latency checks
- Integrating with identity providers (syncing users/tenants)

## Prerequisites

- Permit.io account and API key
- Java 17+ with Spring Boot 3.2+
- Docker/Kubernetes for PDP sidecar deployment

## Execution Steps

### Step 1: PDP Sidecar Deployment

Deploy a dedicated PDP sidecar for each service to ensure sub-millisecond latency and fault isolation.

**docker-compose.yml**:
```yaml
permit-pdp-bff:
  image: permitio/pdp-v2:latest
  container_name: permit-pdp-bff
  environment:
    - PDP_API_KEY=${PERMIT_API_KEY}
    - PDP_DEBUG=false
  ports:
    - "7000:7000" # Expose for local service access
    - "7700:7700" # Expose for policy updates
  healthcheck:
    test: ["CMD", "wget", "--spider", "-q", "http://localhost:7000/health"]
    interval: 10s
```

**Implementation Notes**:
- **Proximity**: For multi-region setups, deploy PDPs in the same region as the service.
- **Isolation**: ❌ Do not share a single PDP across multiple services (creates bottlenecks and single points of failure).

### Step 2: Admin SDK Configuration

Configure the Admin SDK for managing tenants and users.

**PermitConfig.java**:
```java
@Configuration
public class PermitConfig {
    
    @Value("${permit.api-key}")
    private String permitApiKey;
    
    @Value("${permit.environment}")
    private String permitEnv;
    
    @Bean
    public Permit permitAdmin() {
        // Initialize for Admin operations (Sync) only
        return new Permit(
            new PermitConfig.Builder(permitApiKey)
                .withEnvironment(permitEnv)
                .build()
        );
    }
}
```

**Anti-Pattern**: ❌ Do not use this Admin SDK instance for authorization checks (`permit.check()`). It connects to the cloud API, which is slow and rate-limited.

### Step 3: Async Tenant & User Sync

Implement "dual-write" to sync entities from your Identity Provider to Permit.io. Use `@Async` to prevent blocking the main request thread.

**PermitSyncService.java**:
```java
@Service
public class PermitSyncService {
    
    private final Permit permit; // Injected Admin SDK
    
    @Async("asyncExecutor")
    public CompletableFuture<Boolean> syncUserAsync(String userId, String email, String tenantId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 1. Ensure Tenant Exists
                try {
                    permit.api.tenants.get(tenantId);
                } catch (NotFoundException e) {
                    permit.api.tenants.create(new TenantCreate(tenantId).withName(tenantId));
                }

                // 2. Sync User
                try {
                    permit.api.users.get(userId);
                } catch (NotFoundException e) {
                    permit.api.users.create(new UserCreate(userId)
                        .withEmail(email)
                        .withTenants(List.of(tenantId)));
                    log.info("Synced user {} to Permit", userId);
                }
                return true;
            } catch (Exception e) {
                log.error("Failed to sync user to Permit", e);
                return false;
            }
        });
    }
}
```

**Scaling Note**: For high-volume events, consider using a message queue or batching operations to avoid hitting Permit API rate limits (100 req/s).

### Step 4: Permission Checks (Local PDP)

Perform authorization checks using a separate SDK instance connected to the local PDP sidecar.

**PermissionService.java**:
```java
@Service
public class PermissionService {
    
    private final Permit permitPdp;
    
    public PermissionService(@Value("${permit.api-key}") String apiKey, 
                             @Value("${permit.pdp.url}") String pdpUrl) {
        // Initialize specifically for PDP checks
        this.permitPdp = new Permit(
            new PermitConfig.Builder(apiKey).withPdpAddress(pdpUrl).build()
        );
    }
    
    public boolean check(String userId, String action, String resourceType, String resourceId, String tenantId) {
        try {
            // Build context
            User user = new User.Builder(userId).withTenants(List.of(tenantId)).build();
            Resource resource = new Resource.Builder(resourceType).withKey(resourceId).withTenant(tenantId).build();
            
            // Check permission
            return permitPdp.check(user, action, resource);
            
        } catch (Exception e) {
            log.error("Auth check failed", e);
            // CRITICAL: Fail closed (Deny) on error
            return false;
        }
    }
}
```

**Edge Case**: If a user was just created, the PDP might not have synced the policy yet (eventual consistency). If `check()` fails unexpectedly for new users, implement a short retry with backoff.

### Step 5: Role Assignment

Assign roles within a specific tenant context.

```java
public void assignRole(String userId, String role, String tenantId) {
    // ❌ Never assign global roles unless absolutely necessary
    permit.api.roleAssignments.assign(
        new RoleAssignmentCreate(role, userId).withTenant(tenantId)
    );
}
```

## Security & Operational Checklist

- [ ] **Fail Closed**: Ensure all `try-catch` blocks around `permit.check()` return `false`.
- [ ] **Tenant Isolation**: Always pass `tenantId` in User and Resource builders.
- [ ] **Secret Management**: Use environment variables for `PDP_API_KEY`.
- [ ] **Health Checks**: Monitor the `/health` endpoint of the PDP sidecar.

## Related Resources

- [Permit.io Java SDK](https://github.com/permitio/permit-java)
- [PDP Docker Image](https://hub.docker.com/r/permitio/pdp-v2)
