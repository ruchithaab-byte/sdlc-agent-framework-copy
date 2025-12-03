# 5. RBAC Authorization Model

Date: 2025-11-28

## Status
Accepted

## Context
The authentication microservice must provide comprehensive authorization capabilities beyond simple authentication:

**Requirements from PRD:**
- Role-based access control (RBAC) with fine-grained permissions
- Support for hierarchical roles and permission inheritance
- Resource-based authorization (e.g., user can edit their own profile)
- Dynamic permission evaluation without code deployment
- Support for 50+ concurrent applications with different permission models
- Authorization decisions within 20ms for performance requirements

**Current Challenges:**
- Existing services implement authorization inconsistently
- No centralized permission management
- Difficulty in auditing who has access to what resources
- Complex permission models requiring code changes
- No support for temporary permissions or time-based access

**Design Considerations:**
- Balance between flexibility and performance
- Attribute-Based Access Control (ABAC) vs Role-Based Access Control (RBAC)
- Policy engine selection (custom vs OPA vs existing solutions)
- Permission caching strategy for performance
- Migration path from existing authorization systems

## Decision
We will implement a hybrid RBAC model with resource-based extensions using Open Policy Agent (OPA) for policy evaluation:

### 1. RBAC Core Model

**Role Hierarchy**
```
Super Admin (implicit: all permissions)
  └─ Organization Admin
      ├─ Department Admin
      │   └─ Team Lead
      │       └─ Team Member
      └─ Application Admin
          └─ Application User (default)
```

**Permission Model**
```
Permission format: <resource>:<action>
Examples:
  - users:read          # Read user data
  - users:write         # Create/update users
  - users:delete        # Delete users
  - roles:assign        # Assign roles to users
  - applications:admin  # Administer applications
  - audit_logs:read     # View audit logs
```

**Data Model**
```sql
-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_role_id UUID REFERENCES roles(id),  -- For role hierarchy
    is_system_role BOOLEAN DEFAULT FALSE,      -- Prevent deletion of system roles
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Permissions table
CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    is_system_permission BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    UNIQUE(resource, action)
);

-- Role-Permission mapping
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP NOT NULL,
    granted_by UUID REFERENCES users(id),
    PRIMARY KEY (role_id, permission_id)
);

-- User-Role mapping with optional expiration
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP NOT NULL,
    assigned_by UUID REFERENCES users(id),
    expires_at TIMESTAMP,  -- Optional time-limited access
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, role_id)
);

-- Resource-specific permissions (for fine-grained control)
CREATE TABLE resource_permissions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    resource_type VARCHAR(100) NOT NULL,  -- e.g., 'document', 'project'
    resource_id VARCHAR(255) NOT NULL,     -- ID of specific resource
    permission_id UUID REFERENCES permissions(id),
    granted_at TIMESTAMP NOT NULL,
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMP,
    UNIQUE(user_id, resource_type, resource_id, permission_id)
);

-- Indexes for performance
CREATE INDEX idx_user_roles_user ON user_roles(user_id) WHERE is_active = true;
CREATE INDEX idx_user_roles_expires ON user_roles(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_resource_permissions_user ON resource_permissions(user_id);
CREATE INDEX idx_resource_permissions_resource ON resource_permissions(resource_type, resource_id);
```

### 2. Open Policy Agent (OPA) Integration

**Why OPA:**
- Declarative policy language (Rego) enables non-developers to define policies
- High performance (microsecond latency for policy evaluation)
- Decoupled policy management from application code
- Built-in support for complex authorization scenarios
- Active community and extensive documentation

**OPA Deployment Architecture**
```
┌─────────────────┐
│ Auth Service    │
│ ┌─────────────┐ │
│ │ OPA Sidecar │ │ ← Policy evaluation (local)
│ └─────────────┘ │
└─────────────────┘
        ↑
        │ Periodic policy sync (30s interval)
        ↓
┌─────────────────┐
│ Policy Registry │ ← Central policy repository (Git/Vault)
└─────────────────┘
```

**OPA Policy Structure**
```rego
package authz

import future.keywords.if
import future.keywords.in

# Default deny - explicit allow required
default allow = false

# Super admin has all permissions
allow if {
    has_role("super_admin")
}

# Check role-based permissions
allow if {
    required_permission := input.permission
    user_permissions := get_user_permissions(input.user_id)
    required_permission in user_permissions
}

# Resource owner can perform certain actions
allow if {
    input.action in ["read", "update"]
    input.resource.owner_id == input.user_id
}

# Time-based access control
allow if {
    permission_valid_at_time(input.user_id, input.permission, time.now_ns())
}

# Helper functions
has_role(role_name) if {
    role_name in data.user_roles[input.user_id]
}

get_user_permissions(user_id) := permissions if {
    user_roles := data.user_roles[user_id]
    permissions := {p |
        role := user_roles[_]
        p := data.role_permissions[role][_]
    }
}

permission_valid_at_time(user_id, permission, current_time) if {
    grant := data.time_limited_permissions[user_id][permission]
    grant.expires_at > current_time
}
```

### 3. Authorization API

**Authorization Check Endpoint**
```
POST /api/v1/authz/check
Content-Type: application/json

Request:
{
  "user_id": "uuid",
  "permission": "users:write",
  "resource": {
    "type": "user",
    "id": "target-user-uuid",
    "owner_id": "owner-uuid"
  },
  "context": {
    "ip_address": "1.2.3.4",
    "time": "2025-11-28T10:00:00Z"
  }
}

Response (200 OK):
{
  "authorized": true,
  "reason": "User has role 'admin' with permission 'users:write'",
  "evaluated_policies": ["role_based_access", "resource_ownership"],
  "decision_time_ms": 5
}

Response (403 Forbidden):
{
  "authorized": false,
  "reason": "User lacks required permission 'users:write'",
  "evaluated_policies": ["role_based_access"],
  "decision_time_ms": 3
}
```

**Batch Authorization Check**
```
POST /api/v1/authz/batch-check
Content-Type: application/json

Request:
{
  "user_id": "uuid",
  "checks": [
    {"permission": "users:read", "resource": {"type": "user", "id": "user1"}},
    {"permission": "users:write", "resource": {"type": "user", "id": "user2"}},
    {"permission": "roles:assign", "resource": {"type": "role", "id": "role1"}}
  ]
}

Response:
{
  "results": [
    {"permission": "users:read", "authorized": true, "reason": "..."},
    {"permission": "users:write", "authorized": false, "reason": "..."},
    {"permission": "roles:assign", "authorized": true, "reason": "..."}
  ],
  "decision_time_ms": 12
}
```

### 4. Permission Caching Strategy

**Cache Layers**
```
Layer 1: Application Memory (per pod)
  - User role memberships
  - Role-permission mappings
  - TTL: 5 minutes
  - Invalidation: On role/permission change events

Layer 2: Redis Cache (shared)
  - Authorization decisions
  - Key: hash(user_id, permission, resource_type, resource_id)
  - TTL: 2 minutes
  - Invalidation: On user role changes, permission updates

Layer 3: OPA Cache (built-in)
  - Policy evaluation results
  - TTL: 30 seconds
  - Invalidation: Automatic by OPA
```

**Cache Invalidation Strategy**
```
Events that trigger cache invalidation:
  1. User role assignment/revocation
  2. Role permission changes
  3. Permission definition updates
  4. Resource ownership changes
  5. Time-limited permission expiration

Invalidation mechanism:
  - Pub/Sub pattern using Redis
  - Event published to 'authz:invalidate' channel
  - All service instances subscribe and clear relevant cache entries
  - Fallback: TTL-based expiration ensures eventual consistency
```

**Performance Optimization**
```
Authorization Decision Flow:
1. Check application memory cache (1-2ms) → CACHED RESULT
2. If miss, check Redis cache (2-5ms) → CACHED RESULT
3. If miss, query database for user roles (10-20ms)
4. Load role permissions into memory
5. Evaluate OPA policy (1-3ms)
6. Store decision in Redis cache
7. Return authorization result

Target latency: <20ms P95 (including cache misses)
Typical latency: <5ms P95 (with cache hits)
```

### 5. Permission Management API

**Role Management**
```
# Create role
POST /api/v1/roles
{
  "name": "content_editor",
  "description": "Can create and edit content",
  "parent_role_id": "team_member_role_id"
}

# Assign permissions to role
POST /api/v1/roles/{role_id}/permissions
{
  "permission_ids": ["perm1", "perm2", "perm3"]
}

# Assign role to user (with optional expiration)
POST /api/v1/users/{user_id}/roles
{
  "role_id": "content_editor_role_id",
  "expires_at": "2025-12-31T23:59:59Z"  # Optional
}
```

**Permission Discovery**
```
# Get user's effective permissions (including inherited)
GET /api/v1/users/{user_id}/permissions

Response:
{
  "user_id": "uuid",
  "roles": [
    {
      "role_id": "uuid",
      "role_name": "content_editor",
      "permissions": ["content:read", "content:write"]
    }
  ],
  "effective_permissions": [
    "content:read",
    "content:write",
    "users:read"  # Inherited from parent role
  ],
  "resource_specific_permissions": [
    {
      "resource_type": "document",
      "resource_id": "doc123",
      "permissions": ["document:delete"]
    }
  ]
}
```

### 6. Advanced Authorization Scenarios

**Time-Based Access**
```rego
# Grant temporary admin access for maintenance window
allow if {
    input.user_id == "maintenance_user"
    input.permission == "system:admin"

    # Check if within maintenance window
    current_time := time.now_ns()
    maintenance_start := time.parse_rfc3339_ns("2025-11-28T02:00:00Z")
    maintenance_end := time.parse_rfc3339_ns("2025-11-28T06:00:00Z")

    current_time >= maintenance_start
    current_time <= maintenance_end
}
```

**Context-Based Authorization**
```rego
# Allow only from office IP ranges
allow if {
    input.permission == "sensitive_data:read"
    has_role("employee")

    # Check IP address is in allowed ranges
    input.context.ip_address in data.allowed_ip_ranges
}

# Require MFA for sensitive operations
allow if {
    input.permission == "users:delete"
    has_role("admin")

    # Verify recent MFA authentication
    input.context.mfa_verified_at > time.now_ns() - (5 * 60 * 1000000000)  # 5 minutes
}
```

**Delegation and Impersonation**
```rego
# Allow admins to impersonate users for support
allow if {
    input.action == "impersonate"
    has_role("support_admin")

    # Log impersonation event
    log_audit_event("impersonation", input)
}

# Temporary permission delegation
allow if {
    delegated_permission := data.delegated_permissions[input.user_id][input.permission]
    delegated_permission.delegator_id != null
    delegated_permission.expires_at > time.now_ns()

    # Verify delegator had permission to delegate
    delegator_can_delegate(delegated_permission.delegator_id, input.permission)
}
```

## Consequences

### Positive Consequences
- **Flexibility**: OPA Rego policies enable complex authorization logic without code changes
- **Performance**: Multi-layer caching achieves <5ms P95 authorization latency
- **Auditability**: All authorization decisions logged with reasoning
- **Scalability**: Stateless OPA sidecars scale horizontally with service
- **Maintainability**: Centralized policy management in Git repository
- **Security**: Default-deny policy prevents unauthorized access
- **Time-Limited Access**: Built-in support for temporary permissions reduces security risk

### Negative Consequences
- **Learning Curve**: Rego language requires training for policy authors
- **Complexity**: OPA adds another component to manage and monitor
- **Cache Consistency**: Multi-layer caching introduces eventual consistency challenges
- **Policy Testing**: Requires tooling and processes for policy testing
- **Migration Effort**: Existing authorization systems must be migrated to new model

### Risk Mitigation
- **Policy Errors**: Comprehensive policy testing framework with unit tests
- **Performance Degradation**: Aggressive caching and monitoring of authorization latency
- **Cache Invalidation Failures**: TTL-based expiration ensures eventual correctness
- **OPA Unavailability**: Fail-secure approach - deny access if OPA unavailable
- **Policy Conflicts**: Policy versioning and staged rollout process

### Trade-offs Considered

1. **RBAC vs ABAC (Attribute-Based Access Control)**
   - Chose RBAC with OPA extensions for best of both worlds
   - RBAC: Simpler model for common cases, easier to understand
   - ABAC (via OPA): Flexibility for complex scenarios
   - Trade-off: Slightly more complex than pure RBAC

2. **OPA vs Custom Policy Engine**
   - Chose OPA for proven performance and ecosystem
   - Trade-off: Vendor dependency, but open-source mitigates risk

3. **Eager vs Lazy Permission Loading**
   - Chose lazy loading with caching for better performance
   - Trade-off: First request slower, subsequent requests fast

4. **Hierarchical Roles vs Flat Roles**
   - Chose hierarchical for permission inheritance
   - Trade-off: More complex queries, but better permission management

### Future Considerations
- **Fine-Grained Permissions**: Row-level and column-level database access control
- **Dynamic Policies**: Machine learning-based anomaly detection for authorization
- **Federation**: Cross-organization authorization with trusted identity providers
- **Blockchain Audit**: Immutable audit trail using blockchain technology
- **GraphQL Integration**: Integrate authorization with GraphQL query filtering
- **Zero Trust Architecture**: Continuous verification and least-privilege access

## Monitoring and Compliance

**Key Metrics**
- Authorization decision latency (P50, P95, P99)
- Cache hit ratio (target: >95%)
- Policy evaluation errors
- Permission changes per day
- Role assignment changes per day

**Audit Requirements**
- Log all authorization decisions (allowed and denied)
- Track permission grants and revocations
- Monitor for privilege escalation attempts
- Alert on anomalous access patterns
- Retain audit logs for 7 years (compliance)

**Compliance Considerations**
- GDPR: User right to know what data they can access
- SOC 2: Separation of duties, least privilege principle
- PCI DSS: Role-based access control for payment data
- HIPAA: Access controls for protected health information

## References
- NIST RBAC Model (ANSI INCITS 359-2004)
- Open Policy Agent Documentation
- OWASP Access Control Cheat Sheet
- Google Zanzibar: Consistent, Global Authorization System
- AWS IAM Best Practices
