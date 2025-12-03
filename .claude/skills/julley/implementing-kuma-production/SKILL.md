---
name: implementing-kuma-production
description: Implements Kuma (Kong Mesh) service mesh production deployments by applying patterns (Global/Zone CP separation, multi-zone topology, delegated gateway, hybrid fleet management), following best practices (mTLS with CA rotation, control plane sizing, reachable-services, policy layering), implementing workarounds (Argo CD certificate drift, CNI for GKE Autopilot, Cilium compatibility), and avoiding anti-patterns (policy fragmentation, quorum loss, configuration drift, in-memory storage). Use when implementing service mesh, zero trust architecture, multi-cluster connectivity, hybrid Kubernetes/VM deployments, or API gateway integration.
version: 1.0.0
dependencies: []
---

# Implementing Kuma Production

## Overview

Implements Kuma (Kong Mesh) service mesh production deployments using universal control plane architecture that manages services across Kubernetes, VMs, and bare metal. Kuma provides centralized policy enforcement, zero trust security via mTLS, multi-zone connectivity, and unified observability. This skill provides procedural knowledge for control plane architecture, multi-zone topologies, zero trust security, policy governance, and operational workarounds while avoiding critical production anti-patterns.

## When to Use

Use this skill when:
- Implementing service mesh for microservices communication
- Building zero trust architecture with identity-based security
- Deploying multi-cluster or multi-zone service connectivity
- Integrating hybrid Kubernetes and VM workloads under unified governance
- Integrating API gateways (Kong) with service mesh
- Implementing centralized network policy and traffic management
- Setting up cross-zone service discovery and failover

**Input format**: Kubernetes cluster access, VM environment details, multi-zone requirements, security policies, API gateway integration needs

**Expected output**: Production-ready Kuma configuration following proven patterns, best practices applied, workarounds implemented, anti-patterns avoided

## Prerequisites

Before using this skill, ensure:
- Kubernetes cluster access (or VM/bare metal environment)
- Understanding of service mesh concepts (data plane, control plane, sidecar proxy)
- Network connectivity between control plane and data planes
- Administrative permissions for control plane deployment
- Understanding of mTLS and certificate management
- PostgreSQL access (for Universal/Hybrid mode persistent storage)

## Workflow Checklist

Copy this checklist to track your progress:

```markdown
Kuma Production Deployment Progress:
- [ ] Step 1: Design Control Plane Architecture (Global/Zone separation)
- [ ] Step 2: Establish Multi-Zone Topology (if applicable)
- [ ] Step 3: Implement Zero Trust Security (mTLS & Traffic Permissions)
- [ ] Step 4: Size Control Plane Resources
- [ ] Step 5: Define Policy Layering Strategy
- [ ] Step 6: Configure Data Plane Sizing & Sidecars
- [ ] Step 7: Verify Deployment Health & Connectivity
```

## Execution Steps

### Step 1: Control Plane Architecture Pattern

Establish Global/Zone control plane separation for scalable, resilient mesh governance.

#### Global Control Plane Configuration

**Pattern**: Global CP functions solely as policy configuration hub, accepting connections only from Zone CPs.

**Best Practice**: Configure firewall rules to prevent Data Plane Proxies from connecting directly to Global CP. This prevents connection storms and maintains control plane stability.

**Anti-Pattern**: ❌ Allowing DPs to connect directly to Global CP (overloads policy store, delays propagation). ❌ Zone CP accepting policy changes from local sources (breaks governance consistency).

#### Zone Control Plane Configuration

**Pattern**: Zone CP is execution layer managing local DPs, receiving policy updates from Global CP.

**Best Practice**: Zone CP enforces centralized governance by rejecting local policy modifications, ensuring all policies originate from Global CP.

### Step 2: Multi-Zone Topology

Enable cross-zone service discovery and routing via Zone Ingress.

#### Zone Ingress Configuration

**Pattern**: Zone Ingress proxy handles inbound traffic from remote zones, enabling automatic cross-zone routing.

**Template**: See `templates/zone-ingress.template` for standard configuration.

**Best Practice**: mTLS must be explicitly enabled on Mesh before cross-zone communication. Without mTLS, identity context required for routing cannot be established, causing cross-zone traffic failures.

**Anti-Pattern**: ❌ Attempting cross-zone routing without mTLS enabled (routing failures). ❌ Not configuring Zone Ingress for horizontal scalability (bottlenecks under load).

### Step 3: Zero Trust Security

Implement mTLS with automated CA rotation for production security.

#### mTLS Configuration with CA Rotation

**Pattern**: Multi-backend CA configuration enables zero-downtime certificate rotation.

**Template**: See `templates/mesh-mtls.template`.

**Best Practice**: Always deploy permissive MeshTrafficPermission policy before enabling mTLS. By default, mTLS denies all traffic until explicit authorization is granted. Deploying permissions first prevents immediate service interruption.

**Anti-Pattern**: ❌ Enabling mTLS before deploying MeshTrafficPermission (immediate traffic denial). ❌ Single CA backend without rotation capability (security debt).

#### mTLS Order of Operations

1. Deploy permissive MeshTrafficPermission (allows all traffic).
   **Template**: See `templates/mesh-traffic-permission.template`.
2. Enable mTLS on Mesh resource.
3. Gradually restrict permissions using fine-grained policies.

### Step 4: Control Plane Sizing

Size control plane resources based on data plane count and policy complexity.

#### Resource Allocation Heuristics

**Pattern**: Allocate ~1MB memory per data plane proxy. Standard starting point: 4vCPU and 2GB memory for 1000+ DPs.

**Best Practice**: Enable `reachable-services` feature for large meshes. This restricts XDS configuration to only services each DP actually communicates with, dramatically reducing payload size and `xds_generation` time.

**Anti-Pattern**: ❌ Under-provisioning control plane (slow policy propagation, high `xds_generation` latency). ❌ Not enabling reachable-services for large meshes (excessive configuration payload).

#### Performance Monitoring

Monitor key metrics:
- `xds_generation`: Time to compute configuration for DP
- `xds_delivery`: Time between policy change and DP receiving update

Sustained high latency indicates bottleneck requiring horizontal scaling or configuration optimization.

### Step 5: Policy Layering

Establish policy hierarchy distinguishing platform defaults from application overrides.

#### Policy Priority System

**Pattern**: Policy priority determined by targetRef specificity, origin label, and policy-role label.

**Template**: See `templates/mesh-timeout.template` for an example of a system-level policy.

**Best Practice**: Platform teams define organization-wide defaults using `kind: Mesh` targets with `kuma.io/policy-role: system`. Application owners override with specific targets (Dataplane by name/namespace) and `kuma.io/policy-role: workload-owner` for highest priority.

**Anti-Pattern**: ❌ Policy fragmentation across teams (inconsistent implementations). ❌ Application teams modifying platform defaults directly (governance violation).

#### Priority Determinants (Highest to Lowest)

1. `spec.targetRef` specificity: Dataplane by name > MeshService > Mesh
2. `kuma.io/origin` label: zone > global
3. `kuma.io/policy-role` label: workload-owner > consumer > producer > system

### Step 6: Data Plane Sizing

Configure production-ready sidecar resources to prevent throttling.

#### ContainerPatch for Sidecar Resources

**Pattern**: Use ContainerPatch CRD to override default sidecar resource requests and limits.

**Template**: See `templates/container-patch.template`.

**Best Practice**: Set minimum 100m CPU and 128Mi memory requests. Configure high limits (1 CPU, 1GB memory) to prevent Envoy throttling by Kubernetes scheduler.

**Anti-Pattern**: ❌ Using default sidecar resources (50m CPU, 64Mi memory) for production (throttling, high latency). ❌ Not applying ContainerPatch (resource starvation).

#### CNI Adoption for Security

For environments requiring strict security compliance (GKE Autopilot, OpenShift), install Kuma CNI. CNI DaemonSet handles traffic redirection on nodes, eliminating need for NET_ADMIN capability in application pods.

## Verification

Run these commands to verify the health and security of your Kuma deployment:

```bash
# Verify Control Plane Status
kubectl get pods -n kuma-system
kumactl inspect zones  # Check zone connectivity

# Verify mTLS Status
kumactl get mesh default -o json | jq '.mtls.enabledBackend'
# Should return "vault-ca" (or your configured backend)

# Verify Policy Distribution
kumactl inspect dataplane <dataplane-name> --type=policies
# Check that expected timeouts/permissions are applied

# Verify Cross-Zone Connectivity (from a pod inside the mesh)
curl -v http://<service-name>_<namespace>_svc_80.mesh
```

## Common Patterns

### Pattern 1: Global/Zone Control Plane Separation
Global CP serves as central policy configuration hub, accepting connections only from Zone CPs. Zone CPs manage local DPs and receive policy updates from Global CP. Network isolation prevents DPs from connecting directly to Global CP, maintaining stability and scalability.

**When to Use**: Multi-zone deployments, multi-cluster environments, organizations requiring centralized governance.

### Pattern 2: Multi-Zone Service Discovery
Zone Ingress proxies handle cross-zone traffic routing. Built-in DNS server resolves services to local replicas or remote Zone Ingress addresses, enabling automatic failover. mTLS is mandatory for cross-zone communication to establish identity context. See `templates/zone.template` and `templates/zone-ingress.template`.

**When to Use**: Multi-region deployments, disaster recovery requirements, geographical service distribution.

### Pattern 3: Delegated Gateway Pattern
External API gateway (Kong) handles perimeter security (rate limiting, authentication, request timeouts). Kuma manages internal service-to-service traffic, applying L4/L7 policies. Clear separation of concerns: gateway for external, mesh for internal. See `templates/delegated-gateway.template`.

**When to Use**: Integrating Kong or other API gateways with service mesh, separating perimeter and internal governance.

### Pattern 4: Policy Priority Hierarchy
Policies are prioritized by: targetRef specificity (most specific wins), origin label (zone overrides global), policy-role label (workload-owner overrides system). This enables platform defaults with application-specific overrides while maintaining governance.

**When to Use**: Large organizations with platform teams and application teams, need for consistent defaults with flexibility for exceptions.

## Best Practices

### Best Practice 1: mTLS Order of Operations
**Critical Sequence**:
1. Deploy permissive MeshTrafficPermission (`templates/mesh-traffic-permission.template`) allowing all traffic
2. Enable mTLS on Mesh resource (`templates/mesh-mtls.template`)
3. Gradually restrict permissions with fine-grained policies

**Rationale**: mTLS denies all traffic by default. Enabling mTLS before permissions causes immediate service interruption.

### Best Practice 2: Control Plane Sizing
**Heuristics**:
- ~1MB memory per data plane proxy
- 4vCPU and 2GB memory for 1000+ DPs
- Enable `reachable-services` feature for large meshes

**Rationale**: Adequate resources prevent slow policy propagation. Reachable-services dramatically reduces XDS payload size and generation time.

### Best Practice 3: CA Rotation
**Implementation**: Configure multiple CA backends in Mesh resource. Toggle `enabledBackend` to rotate. DPs automatically trust certificates from all defined CAs during transition.

**Rationale**: Zero-downtime certificate rotation maintains security posture without service disruption.

### Best Practice 4: Sidecar Resource Management
**Configuration**: Use ContainerPatch (`templates/container-patch.template`) to set minimum 100m CPU, 128Mi memory requests. Set high limits (1 CPU, 1GB) to prevent throttling.

**Rationale**: Default resources insufficient for production workloads. Throttling causes high latency and degraded performance.

### Best Practice 5: Policy Layering Governance
**Structure**: Platform defaults use `kind: Mesh` targets with `kuma.io/policy-role: system`. Application overrides use specific targets (Dataplane by name) with `kuma.io/policy-role: workload-owner`.

**Rationale**: Clear separation enables consistent organization-wide defaults while allowing application teams to meet specific SLOs.

## Workarounds

### Workaround 1: Argo CD Certificate Drift
**When**: Using Argo CD with Helm charts that auto-generate self-signed certificates.
**Issue**: Helm template command compares desired vs current state. Auto-generated certificates cause continuous control plane restarts due to perceived drift.
**Solution**: Pre-configure external certificates (Vault or corporate PKI) instead of relying on Helm chart's self-signed option.
**Trade-off**: Additional certificate management overhead, but eliminates control plane instability.

### Workaround 2: GKE Autopilot NET_ADMIN Restriction
**When**: Deploying on GKE Autopilot which forbids NET_ADMIN capability by default.
**Issue**: Standard Kuma initContainer requires NET_ADMIN to set up iptables rules for transparent proxying.
**Solution**: Install Kuma CNI (handles redirection on nodes) or specify `--workload-policies=allow-net-admin` during cluster creation.
**Trade-off**: CNI adds operational complexity but required for security compliance.

### Workaround 3: Cilium Compatibility
**When**: Using Cilium as Container Network Interface.
**Issue**: Cilium replacing kube-proxy breaks Kuma routing configurations.
**Solution**: Set `kubeProxyReplacement: false` in Cilium config. For recent versions, set `cni.exclusive: false` or `cni-exclusive: false` when chaining CNI plugins.
**Trade-off**: Limited Cilium features, but maintains Kuma compatibility.

### Workaround 4: Argo Rollouts Integration
**When**: Using Argo Rollouts for canary or blue-green deployments.
**Issue**: Argo Rollouts uses temporary service selector labels during traffic shifting. Kuma sidecar injector may misinterpret these labels, causing traffic interruption.
**Solution**: Configure control plane with `KUMA_RUNTIME_KUBERNETES_INJECTOR_IGNORED_SERVICE_SELECTOR_LABELS: rollouts-pod-template-hash`.
**Trade-off**: Temporary label handling complexity, but enables safe traffic shifting.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Policy Fragmentation
**Issue**: Application teams implementing network reliability logic (exponential retries, connection timeouts, circuit breakers) directly in business code.
**Impact**: Security vulnerabilities, technical debt, inconsistent implementations across languages, maintenance overhead.
**Resolution**: Delegate all network management and reliability logic to out-of-process sidecar proxy. Use Kuma policies (MeshRetry, MeshTimeout, MeshCircuitBreaker) for centralized enforcement.
**Detection**: Network logic (retries, timeouts, circuit breakers) present in application business code.

### Anti-Pattern 2: Quorum Loss
**Issue**: Deploying even number of control plane replicas (2, 4, 6) causing quorum break during single-node failure.
**Impact**: Control plane loses ability to accept policy changes, update DP status, or register new endpoints. Mesh governance layer effectively frozen.
**Resolution**: Deploy odd number of controllers (3 or 5) to ensure quorum maintained during single-node failures.
**Detection**: Control plane unable to accept policy changes, cluster health shows quorum loss.

### Anti-Pattern 3: In-Memory Storage
**Issue**: Using default in-memory store in Universal mode for production deployments.
**Impact**: All configured meshes, policies, and DP status information lost upon control plane restart.
**Resolution**: Use PostgreSQL for persistent state storage in Universal or Hybrid modes. Configure connection parameters and TLS settings.
**Detection**: State lost after control plane restart, no persistent storage configured.

### Anti-Pattern 4: Configuration Drift
**Issue**: Deploying policy changes directly to production without staggered deployment strategies.
**Impact**: Widespread service disruption, inability to quickly rollback, extended MTTR.
**Resolution**: Treat policies like infrastructure code. Apply changes first to small canary subset using fine-grained tags, validate functionality, then proceed with wide rollout.
**Detection**: Widespread service disruption immediately after policy change, no canary deployment evidence.

### Anti-Pattern 5: Missing mTLS for Cross-Zone
**Issue**: Attempting cross-zone service communication without mTLS enabled on Mesh.
**Impact**: Cross-zone traffic routing failures. Identity context required for routing cannot be established without mTLS.
**Resolution**: Enable mTLS on Mesh resource (`templates/mesh-mtls.template`) before configuring cross-zone routing. Ensure Zone Ingress proxies have valid certificates.
**Detection**: Cross-zone service calls failing with routing errors, mTLS not enabled on Mesh.

### Anti-Pattern 6: Default Sidecar Resources
**Issue**: Using default sidecar resource requests (50m CPU, 64Mi memory) for production workloads.
**Impact**: Envoy proxy throttled by Kubernetes scheduler, high latency, degraded performance, resource starvation.
**Resolution**: Apply ContainerPatch CRD (`templates/container-patch.template`) with production-ready resource requests (100m CPU, 128Mi memory minimum) and high limits.
**Detection**: Envoy throttling metrics, high latency, pod resource constraints, default resources in use.

## Error Handling

### 503 Service Unavailable
**Symptoms**: Envoy returns 503 errors, services unavailable.
**Diagnosis**:
1. Check XDS delivery metrics (`xds_delivery` time)
2. Verify policy targeting (MeshService exists, targetRef correct)
3. Check policy hierarchy (higher-priority policy not blocking)
**Resolution**: Fix policy targeting, verify XDS propagation, check policy priority conflicts.

### Envoy Cluster Not Found
**Symptoms**: 404 Not Found or cluster definition missing.
**Diagnosis**:
1. Query failing pod's Envoy admin interface (`/clusters` endpoint)
2. Verify expected destination service cluster is listed
3. Check XDS configuration delivery
**Resolution**: Verify MeshService resource exists, check policy targeting, ensure XDS configuration delivered to DP.

### Control Plane Quorum Loss
**Symptoms**: Control plane unable to accept policy changes, cluster health shows quorum break.
**Diagnosis**:
1. Verify odd number of control plane replicas (3 or 5)
2. Check cluster controller health
3. Verify network connectivity between controllers
**Resolution**: Ensure odd number of replicas, restore failed controllers, verify cluster networking.

## Security Guidelines

**CRITICAL**: Never hardcode sensitive information:
- ❌ No certificates, private keys, or tokens in YAML files
- ❌ No credentials in SKILL.md or templates
- ✅ Use external secret management (Vault, Kubernetes secrets)
- ✅ Route sensitive operations through secure channels

**Operational Constraints**:
- Always enable mTLS for production meshes
- Use MeshTrafficPermission for explicit authorization (deny-by-default)
- Configure CA rotation for certificate lifecycle management
- Use Kuma CNI in restricted environments (GKE Autopilot, OpenShift)

## Related Resources

For extensive reference materials, see:
- `templates/`: Full YAML policy templates for Mesh, Policies, and Dataplanes
- Kuma documentation: https://kuma.io/docs
- Kong Mesh documentation: https://docs.konghq.com/mesh/

## Notes

- Kuma supports both Kubernetes and Universal (VM/bare metal) deployments under single Global CP
- VM data plane lifecycle requires external automation (Ansible, Terraform, Puppet)
- Policy priority system enables platform governance with application flexibility
- Reachable-services feature mandatory for large-scale meshes (1000+ DPs)
- CNI adoption required for security-compliant environments
