---
name: implementing-unleash-featureops
description: Implements Unleash v9.2.0 feature flag management by applying proven architectural patterns (SPOE single point evaluation, abstraction layer decoupling, multi-strategy inclusive OR logic, Edge daisy chaining for multi-region), following best practices (complete context building, constraint-based targeting over custom strategies, userId stickiness for A/B testing, telemetry-enabled governance), implementing workarounds (Edge daisy chaining for latency mitigation, constraint-based targeting as alternative to custom strategies), and avoiding anti-patterns (flag sprawl, long-lived flags becoming config, fragmented evaluation, custom strategy overload, incomplete context, missing telemetry). Use when implementing feature flags, setting up A/B testing infrastructure, configuring gradual rollouts, deploying multi-region feature flag infrastructure, or managing feature flag lifecycle and governance.
version: 1.0.0
dependencies:
  - unleash-client>=6.0.0
  - io.getunleash:unleash-client-java>=9.0.0
  - postgresql>=14.0
  - node>=22.0.0
---

# Implementing Unleash FeatureOps

## Overview

Implements Unleash v9.2.0 as the FeatureOps control plane for continuous, low-risk deployment. Unleash transforms software delivery from monolithic releases to feature flag-driven deployments, enabling high release velocity (100+ daily deployments) while maintaining production stability. The platform supports 15+ official SDKs (Node.js, Java, Python, Go) for polyglot environments.

**Critical Prerequisites**: Unleash v7+ requires PostgreSQL v14+ and Node.js v22+ due to ESM migration. Server upgrades must include infrastructure modernization (database and runtime updates) before application deployment.

## When to Use

Use this skill when:
- Implementing feature flags in applications (web, mobile, backend services)
- Setting up A/B testing and experimentation infrastructure
- Configuring gradual rollouts and kill switches for production safety
- Deploying multi-region feature flag infrastructure with Edge
- Managing feature flag lifecycle and governance (cleanup, analytics)
- Implementing trunk-based development with feature flags
- Building self-hosted feature flag infrastructure for compliance

**Input format**: Application codebase, Unleash server URL, API token, deployment environment requirements
**Expected output**: Production-ready feature flag implementation following SPOE pattern, abstraction layer, best practices applied, anti-patterns avoided

## Prerequisites

Before using this skill, ensure:
- Unleash server v9.2.0+ (or v7+ compatible) with PostgreSQL v14+ and Node.js v22+
- API token for client authentication (client-side or server-side)
- Understanding of feature flag lifecycle (Define, Develop, Production, Cleanup, Archived)
- Application runtime compatible with target SDK (Node.js, Java, Python, Go)
- Access to Unleash Admin UI for flag configuration and governance

## Execution Steps

### Step 1: SDK Initialization

Initialize Unleash SDK early in application lifecycle with required parameters for telemetry and local evaluation.

**Node.js SDK Initialization Template**:
```typescript
import { initialize } from 'unleash-client';

const unleash = initialize({
  url: process.env.UNLEASH_SERVER_URL + '/api/',
  appName: 'my-service', // Required for telemetry
  instanceId: process.env.POD_NAME || `instance-${Date.now()}`, // Unique per instance
  refreshInterval: 15000, // Poll frequency (15 seconds)
  customHeaders: {
    Authorization: process.env.UNLEASH_API_TOKEN // Never hardcode
  }
});

unleash.on('ready', () => {
  console.log('Unleash client synchronized');
});
```

**Java SDK Initialization Template**:
```java
import io.getunleash.Unleash;
import io.getunleash.DefaultUnleash;
import io.getunleash.UnleashConfig;

UnleashConfig config = UnleashConfig.builder()
  .appName("my-service")
  .instanceId(System.getenv("POD_NAME"))
  .unleashAPI(System.getenv("UNLEASH_SERVER_URL") + "/api/")
  .customHttpHeader("Authorization", System.getenv("UNLEASH_API_TOKEN"))
  .synchronousFetchOnInitialisation(true) // Optional: block until ready
  .build();

Unleash unleash = new DefaultUnleash(config);
```

**Best Practice**: Initialize before processing requests, use unique instanceId per running instance
**Anti-Pattern**: Missing appName/instanceId breaks telemetry and governance metrics

### Step 2: Single Point of Evaluation (SPOE) Pattern

Evaluate feature flag state once at request entry point, then pass result through system. Ensures consistency and simplifies cleanup.

**SPOE Pattern Template**:
```typescript
// Request entry point (middleware/handler)
function handleRequest(req, res) {
  // Build complete context with all required fields
  const context = {
    userId: req.user?.id,
    sessionId: req.sessionId,
    remoteAddress: req.ip,
    environment: process.env.NODE_ENV,
    tenantId: req.user?.organizationId, // Custom property for constraints
    email: req.user?.email
  };

  // Evaluate ONCE at entry point
  const isNewFeatureEnabled = unleash.isEnabled('feature-new-engine', context);
  const variant = unleash.getVariant('feature-new-engine', context);

  // Pass result through system (don't re-evaluate)
  processRequest(req, res, { isNewFeatureEnabled, variant });
}

function processRequest(req, res, featureState) {
  if (featureState.isNewFeatureEnabled) {
    // Use new feature
  } else {
    // Use old feature
  }
}
```

**Best Practice**: Build complete context at entry point with all fields required by strategies
**Anti-Pattern**: Multiple flag evaluations within single request causes inconsistency

### Step 3: Abstraction Layer Pattern

Centralize feature flag logic in dedicated service/facade to decouple application from Unleash SDK.

**Abstraction Layer Template**:
```typescript
// FeatureService abstraction
class FeatureService {
  constructor(private unleash: Unleash) {}

  isNewEngineEnabled(context: UnleashContext): boolean {
    return this.unleash.isEnabled('feature-new-engine', context);
  }

  getRecommendationVariant(context: UnleashContext): Variant {
    return this.unleash.getVariant('feature-recommendations', context);
  }
}

// Application code uses abstraction (not direct SDK)
const featureService = new FeatureService(unleash);
const enabled = featureService.isNewEngineEnabled(userContext);
```

**Java Abstraction Template**:
```java
public class FeatureToggleFacade {
  private final Unleash unleash;

  public FeatureToggleFacade(Unleash unleash) {
    this.unleash = unleash;
  }

  public boolean canAccessPremium(UnleashContext context) {
    return unleash.isEnabled("feature.premium_access", context);
  }
}
```

**Best Practice**: Decouple application logic from SDK, enables easy mocking for tests
**Anti-Pattern**: Direct SDK calls scattered throughout codebase fragments control flow

### Step 4: Multi-Strategy Evaluation Pattern

Apply multiple activation strategies to single toggle using inclusive OR logic (any strategy true = enabled).

**Multi-Strategy Template**:
```typescript
// In Unleash Admin UI: Configure toggle with multiple strategies
// Strategy 1: Gradual Rollout (75% of users)
// Strategy 2: User IDs (whitelist: internal team emails)
// Result: Internal team always enabled + 75% of general population

const context = {
  userId: user.id,
  email: user.email, // Required for User IDs strategy
  // ... other fields
};

// Evaluation uses inclusive OR: internal team OR 75% rollout
const enabled = unleash.isEnabled('feature-new-ui', context);
```

**Best Practice**: Use standard strategies (Gradual Rollout, User IDs) with constraints
**Anti-Pattern**: Custom strategy overload creates complexity debt across polyglot SDKs

### Step 5: Context-Based Targeting with Constraints

Use constraint-based targeting instead of custom strategies for complex segmentation.

**Constraint-Based Targeting Template**:
```typescript
// In Unleash Admin UI: Standard Gradual Rollout + Constraints
// Constraint: email STR_ENDS_WITH @company.com
// Constraint: tenantId EQUALS premium-tenant

const context = {
  userId: user.id,
  email: user.email, // For email constraint
  tenantId: user.organizationId, // For tenantId constraint
  remoteAddress: req.ip
};

// Evaluation: 50% rollout + email constraint + tenantId constraint
const enabled = unleash.isEnabled('feature-premium', context);
```

**Best Practice**: Use constraints for targeting (email domains, tenant IDs, regions)
**Workaround**: Constraints centralize complexity in Admin UI, avoid custom SDK code

### Step 6: Edge Deployment and Daisy Chaining

Deploy Unleash Edge regionally for multi-region applications, chain Edge instances for latency mitigation.

**Edge Daisy Chaining Pattern**:
```
Regional Edge → Regional Edge → Central Server
(US-East)      (EU-West)      (Primary)
```

**Edge Configuration Template**:
```yaml
# Edge instance configuration
edge:
  upstreamUrl: "https://unleash-server.example.com/api/"
  # Edge can also consume from another Edge (daisy chain)
  # upstreamUrl: "https://edge-us-east.example.com/api/"
  port: 3063
  enableOfflineMode: true # Offline resilience
```

**Best Practice**: Deploy Edge regionally, chain to central server for synchronization
**Workaround**: Daisy chaining mitigates global latency in multi-region deployments

### Step 7: A/B Testing and Stickiness

Configure stickiness using persistent identifiers (userId) for consistent variant assignment across sessions.

**A/B Testing with Stickiness Template**:
```typescript
// In Unleash Admin UI: Configure gradual rollout with stickiness
// Stickiness: userId (preferred over sessionId for consistency)

const context = {
  userId: user.id, // Persistent identifier for stickiness
  sessionId: req.sessionId, // Fallback if userId unavailable
  // ... other fields
};

const variant = unleash.getVariant('feature-ab-test', context);
// User always sees same variant across sessions/devices

// Capture impression for analytics
trackImpression('feature-ab-test', variant.name, user.id);
```

**Best Practice**: Use userId for stickiness (not sessionId) for multi-device consistency
**Best Practice**: Integrate with external analytics (capture impressions, adjust traffic dynamically)

### Step 8: Telemetry and Governance

Enable telemetry for governance metrics (flag lifecycle, cleanup ratio, usage tracking).

**Telemetry Configuration**:
- SDK automatically registers on startup (appName, instanceId required)
- SDK reports usage metrics (flag evaluations, variant impressions)
- Admin UI displays lifecycle analytics (flags created vs archived)

**Best Practice**: Always provide appName and instanceId for telemetry
**Best Practice**: Monitor cleanup ratio (target: 100% archived vs created)
**Anti-Pattern**: Disabling telemetry loses governance metrics and cleanup visibility

## Common Patterns

### Pattern 1: Single Point of Evaluation (SPOE)

**Description**: Evaluate feature flag once at request entry point, pass result through system.

**When to Use**: All feature flag implementations requiring consistency.

**Template**: See Step 2 above.

**Benefits**: Guarantees consistent user experience, simplifies code cleanup, localizes control logic.

### Pattern 2: Abstraction Layer

**Description**: Centralized feature service/facade decouples application from Unleash SDK.

**When to Use**: Multi-flag applications requiring maintainability and testability.

**Template**: See Step 3 above.

**Benefits**: Easy mocking for tests, faster cleanup (flags in one place), architectural clarity.

### Pattern 3: Multi-Strategy Evaluation

**Description**: Apply multiple strategies to single toggle using inclusive OR logic.

**When to Use**: Controlled rollouts requiring internal team whitelisting plus gradual rollout.

**Template**: See Step 4 above.

**Benefits**: Internal team always enabled regardless of rollout percentage, flexible targeting.

### Pattern 4: Edge Daisy Chaining

**Description**: Hierarchical caching layers (Edge → Edge → Server) for multi-region deployments.

**When to Use**: Global applications with high latency to central server.

**Template**: See Step 6 above.

**Benefits**: Reduced latency, offline resilience, synchronized configuration across regions.

### Pattern 5: Constraint-Based Targeting

**Description**: Use standard strategies (Gradual Rollout) augmented with constraints instead of custom strategies.

**When to Use**: Complex targeting requirements (email domains, tenant IDs, regions).

**Template**: See Step 5 above.

**Benefits**: Centralized complexity in Admin UI, no custom SDK code, easier maintenance.

## Best Practices

1. **SDK Initialization**: Initialize early in application lifecycle, use unique instanceId per running instance, provide complete context.

2. **Context Completeness**: Include all fields required by activation strategies (userId, sessionId, remoteAddress, custom properties). Incomplete context causes strategy evaluation failures.

3. **Strategy Selection**: Prefer standard strategies (Gradual Rollout, User IDs) with constraints over custom strategies to avoid complexity debt across polyglot SDKs.

4. **Stickiness Configuration**: Use userId (persistent identifier) over sessionId for A/B testing consistency across devices and sessions.

5. **Telemetry Enablement**: Always provide appName and instanceId during initialization. Telemetry enables governance metrics (lifecycle analytics, cleanup ratio).

6. **Flag Lifecycle Management**: Maintain 1:1 cleanup ratio (flags archived vs flags created). Treat cleanup as definition of done for feature delivery.

7. **Testing Strategy**: Mock feature service abstraction for unit tests. Test both enabled and disabled code paths.

## Workarounds

### Workaround 1: Daisy Chaining for Latency

**When**: Multi-region deployments with high latency to central Unleash server.

**How**: Deploy Edge instances regionally, configure Edge to consume from another Edge (daisy chain) or central server. Regional SDKs connect to local Edge for low latency.

**Trade-off**: Additional infrastructure complexity (Edge deployment, monitoring, synchronization).

**Implementation**: Configure Edge upstreamUrl to point to another Edge instance or central server.

### Workaround 2: Constraint-Based Targeting

**When**: Complex targeting requirements that would otherwise require custom strategy implementation.

**How**: Use standard Gradual Rollout strategy with constraints (email STR_ENDS_WITH, tenantId EQUALS, remoteAddress IN_LIST). Constraints defined in Admin UI, no custom SDK code.

**Trade-off**: Constraint logic centralized in server, requires Admin UI access for changes.

**Implementation**: Configure constraints in Unleash Admin UI on standard strategies.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Flag Sprawl

**Issue**: Accumulating technical debt from creating flags faster than archiving them.

**Detection**: Cleanup ratio < 100% (flags archived vs flags created). Lifecycle analytics show increasing flag inventory.

**Resolution**: Enforce flag ownership, establish automated expiration notifications, treat cleanup as definition of done for feature delivery. Use Project Overview filters to identify flags in 'Clean-up' stage.

**Impact**: Clutters codebase, increases cognitive load, obscures business logic.

### Anti-Pattern 2: Long-Lived Flags

**Issue**: Temporary release flags remain active indefinitely, becoming permanent configuration.

**Detection**: Flags active > 6 months without cleanup plan. Flags used for static behavior control.

**Resolution**: Migrate static values to dedicated configuration store (Kubernetes ConfigMaps, HashiCorp Vault, environment variables). Unleash is for dynamic control (rollouts, kill switches, experimentation), not static config.

**Impact**: Obscures business logic, complicates code review, violates separation of concerns.

### Anti-Pattern 3: Fragmented Evaluation

**Issue**: Same feature flag checked multiple times in dispersed code locations within single request.

**Detection**: Same flag name appears in multiple files, flag evaluated in different functions during same request.

**Resolution**: Apply SPOE pattern. Evaluate flag once at request entry point, pass result through system as parameter or context object.

**Impact**: Inconsistent user experience, complex debugging, violates Single Responsibility Principle.

### Anti-Pattern 4: Custom Strategy Overload

**Issue**: Developing custom activation strategies creates complexity debt requiring replication across all client SDKs (Node.js, Java, Python, Go).

**Detection**: Custom strategies defined in Unleash server, custom strategy code in multiple SDKs.

**Resolution**: Use standard strategies (Gradual Rollout, User IDs) augmented with constraints. Constraints centralize complexity in Admin UI, eliminate distributed custom code.

**Impact**: Exponential maintenance burden, testing complexity, version synchronization issues.

### Anti-Pattern 5: Incomplete Context

**Issue**: Activation strategies fail to evaluate correctly due to missing context fields.

**Detection**: Flags not evaluating as expected, strategies returning false when should be true.

**Resolution**: Build complete context at application entry point. Include all fields required by strategies: userId, sessionId, remoteAddress, custom properties (email, tenantId, etc.).

**Impact**: Incorrect feature targeting, failed rollouts, unpredictable behavior.

### Anti-Pattern 6: Missing Telemetry

**Issue**: No governance metrics available (lifecycle analytics, cleanup ratio, usage tracking).

**Detection**: appName or instanceId missing from SDK initialization, no telemetry data in Admin UI.

**Resolution**: Always provide unique appName and instanceId during SDK initialization. Enable telemetry for governance visibility.

**Impact**: No visibility into flag lifecycle, cannot measure cleanup ratio, governance blind spots.

## Code Templates

### Node.js SDK Initialization
```typescript
import { initialize } from 'unleash-client';

const unleash = initialize({
  url: process.env.UNLEASH_SERVER_URL + '/api/',
  appName: 'my-service',
  instanceId: process.env.POD_NAME || `instance-${Date.now()}`,
  refreshInterval: 15000,
  customHeaders: {
    Authorization: process.env.UNLEASH_API_TOKEN
  }
});

unleash.on('ready', () => console.log('Unleash ready'));
```

### Java SDK Initialization
```java
UnleashConfig config = UnleashConfig.builder()
  .appName("my-service")
  .instanceId(System.getenv("POD_NAME"))
  .unleashAPI(System.getenv("UNLEASH_SERVER_URL") + "/api/")
  .customHttpHeader("Authorization", System.getenv("UNLEASH_API_TOKEN"))
  .build();

Unleash unleash = new DefaultUnleash(config);
```

### SPOE Pattern
```typescript
function handleRequest(req, res) {
  const context = {
    userId: req.user?.id,
    sessionId: req.sessionId,
    remoteAddress: req.ip,
    tenantId: req.user?.organizationId
  };
  const isEnabled = unleash.isEnabled('feature-flag', context);
  processRequest(req, res, isEnabled);
}
```

### Abstraction Layer
```typescript
class FeatureService {
  constructor(private unleash: Unleash) {}
  isEnabled(flag: string, context: UnleashContext): boolean {
    return this.unleash.isEnabled(flag, context);
  }
}
```

### Multi-Strategy with Constraints
```typescript
const context = {
  userId: user.id,
  email: user.email,
  tenantId: user.organizationId
};
const enabled = unleash.isEnabled('feature-flag', context);
// Evaluates: Gradual Rollout OR User IDs OR Constraints
```

### A/B Testing with Stickiness
```typescript
const variant = unleash.getVariant('feature-ab-test', {
  userId: user.id, // Stickiness key
  sessionId: req.sessionId
});
trackImpression('feature-ab-test', variant.name, user.id);
```

## Examples

### Example 1: E-commerce Feature Rollout

**Scenario**: Rollout new recommendation engine to 50% of users plus internal QA team.

**Implementation**:
```typescript
// SDK initialization (application startup)
const unleash = initialize({
  url: process.env.UNLEASH_SERVER_URL + '/api/',
  appName: 'ecommerce-api',
  instanceId: process.env.POD_NAME,
  customHeaders: { Authorization: process.env.UNLEASH_API_TOKEN }
});

// Request handler (SPOE pattern)
async function getRecommendations(req, res) {
  const context = {
    userId: req.user.id,
    email: req.user.email, // For User IDs strategy
    sessionId: req.sessionId
  };

  // Evaluate once
  const isNewEngineEnabled = unleash.isEnabled('feature-new-recommendations', context);
  const variant = unleash.getVariant('feature-new-recommendations', context);

  // Use result
  const recommendations = isNewEngineEnabled
    ? await newRecommendationEngine.get(variant.name)
    : await oldRecommendationEngine.get();

  res.json(recommendations);
}
```

**Unleash Admin UI Configuration**:
- Strategy 1: Gradual Rollout (50% of users)
- Strategy 2: User IDs (whitelist: qa-team@company.com, product@company.com)

### Example 2: Multi-Region Edge Deployment

**Scenario**: Global application with Edge instances in US-East and EU-West regions.

**Edge Configuration** (US-East):
```yaml
edge:
  upstreamUrl: "https://unleash-primary.example.com/api/"
  port: 3063
  enableOfflineMode: true
```

**Application Configuration** (US-East region):
```typescript
const unleash = initialize({
  url: 'https://edge-us-east.example.com/api/', // Local Edge
  appName: 'global-service',
  instanceId: process.env.POD_NAME,
  customHeaders: { Authorization: process.env.UNLEASH_API_TOKEN }
});
```

**Result**: US-East applications connect to local Edge (low latency), Edge syncs with central server, daisy chaining possible for additional Edge layers.

## Error Handling

**Common Errors**:
- **Connection Failure**: SDK cannot reach Unleash server
  - **Resolution**: Implement retry logic, use fallback values (default to disabled), check network connectivity
  - **Fallback**: Return disabled state, log error for monitoring

- **Invalid API Token**: Authentication fails
  - **Resolution**: Verify token in environment variables, check token permissions in Admin UI
  - **Fallback**: Return disabled state, alert operations team

- **Missing Context Fields**: Strategies fail due to incomplete context
  - **Resolution**: Validate context completeness at entry point, log missing fields
  - **Fallback**: Use default context values, log warning

- **Server Unavailable**: Unleash server down or unreachable
  - **Resolution**: SDK uses cached configuration (last known state), retry with exponential backoff
  - **Fallback**: Continue with cached flags, alert when server returns

**Fallback Strategy**: Default to disabled state on errors to prevent feature exposure during failures.

## Security and Guidelines

**CRITICAL**: Never hardcode sensitive information:
- ❌ No API tokens in code, SKILL.md, or configuration files
- ❌ No server URLs hardcoded
- ✅ Use environment variables for all sensitive configuration
- ✅ Use server-side token generation for client SDKs (never expose tokens to browser)
- ✅ Self-host Unleash for compliance (FedRAMP, SOC2, ISO27001) - retains complete data control

**Operational Constraints**:
- Client SDKs require API token for authentication
- Server SDKs can use server-side tokens or service accounts
- Edge instances require upstream server authentication
- Telemetry data includes appName and instanceId (ensure no PII in identifiers)

## Performance Considerations

- **Local Evaluation**: Flag checks use in-memory repository (no network round-trip), sub-millisecond latency
- **Periodic Server Sync**: SDK polls server for configuration updates (default: 15 seconds), configurable refreshInterval
- **Edge Caching**: Edge instances cache configuration, reduce latency for regional SDKs
- **Telemetry Overhead**: Minimal impact (usage metrics reported asynchronously, batched)
- **Database Performance**: PostgreSQL v14+ required for server performance and structural integrity

## Related Resources

- Unleash Documentation: https://docs.getunleash.io/
- Unleash Server Requirements: https://docs.getunleash.io/reference/requirements
- SDK Documentation: https://docs.getunleash.io/reference/sdks
- Edge Deployment: https://docs.getunleash.io/reference/unleash-edge
- Feature Flag Lifecycle: https://docs.getunleash.io/reference/feature-lifecycle

