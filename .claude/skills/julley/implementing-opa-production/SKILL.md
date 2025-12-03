---
name: implementing-opa-production
description: Guide for implementing production-grade Open Policy Agent (OPA) policies. Covers architecture patterns (Sidecar, Gateway, K8s), policy-data separation, RBAC/ABAC/Multi-tenant implementations, and strict testing/validation workflows. Use for K8s admission, microservices authz, or API gateways.
version: 1.0.0
---

# Implementing OPA Production

## Overview
This skill guides the implementation of production-ready OPA policies. It enforces best practices: decoupled policy/data, deterministic evaluation, 90%+ test coverage, and optimized performance.

## Prerequisites
- OPA runtime access (local or remote)
- Defined authorization requirements (e.g., RBAC matrix)
- Data sources identified (JWT, DB, Git)

## Implementation Workflow

Follow these phases to implement a robust OPA solution.

### Phase 1: Architecture & Pattern Selection
1.  **Identify the Integration Point**:
    *   **Kubernetes**: Use Gatekeeper/Admission Control.
    *   **Microservices**: Use Sidecar (Envoy/Istio) or Embedded library.
    *   **API Gateway**: Use Gateway/Proxy filter.
    *   **App Logic**: Use Sidecar or Centralized service.

2.  **Select the Policy Pattern**:
    *   **RBAC**: Role-based access. Use `templates/rbac-policy.rego.template`.
    *   **ABAC**: Attribute-based access. Use `templates/abac-policy.rego.template`.
    *   **Multi-Tenant**: Isolation rules. Use `templates/multi-tenant.rego.template`.
    *   **K8s Admission**: Validating webhooks. Use `templates/kubernetes-admission.rego.template`.

3.  **Define Data Strategy**:
    *   **High QPS / Low Latency**: Push data to OPA (Bundle API) or use JWTs.
    *   **Massive Datasets**: Use "Evaluation Pull" (fetch during eval) or "Partial Evaluation" (compile data into policy).

### Phase 2: Policy Development
1.  **Start with a Template**: Copy the relevant template from `templates/` to your policy directory.
2.  **Enforce "Default Deny"**: Ensure `default allow = false` is the first rule.
3.  **Separate Logic from Data**:
    *   Write static logic in `.rego` files.
    *   Place dynamic data (user roles, resource owners) in `data.json` or external bundles.
    *   *Anti-Pattern*: Do NOT hardcode user lists or configs inside `.rego` files.
4.  **Implement Security Best Practices**:
    *   Validate input schemas (type checking).
    *   Use `deny` (or `violation`) sets for granular error messages, not just boolean `allow`.

### Phase 3: Validation & Testing
1.  **Compilation Check**:
    Run `opa check --strict .` to catch unused variables and unsafe keywords.
2.  **Unit Testing**:
    *   Create `_test.rego` files for every policy.
    *   Mock `input` and `data` in tests.
    *   Run `opa test --coverage .` and ensure >90% coverage.
3.  **Performance Check**:
    *   Avoid iteration over large arrays. Use object lookups (`data.users[id]`).
    *   Use `opa bench` for critical paths.

## Production Readiness Checklist
Copy this checklist to track your implementation status:

```markdown
- [ ] **Security**: "Default Deny" is enabled (`default allow = false`).
- [ ] **Security**: No sensitive secrets (API keys) hardcoded in Rego.
- [ ] **Architecture**: Policy logic is separated from data (roles, configs).
- [ ] **Reliability**: `opa check --strict` passes without errors.
- [ ] **Testing**: `opa test --coverage` reports >90% coverage.
- [ ] **Observability**: Violation rules return meaningful error messages (not just `false`).
- [ ] **Performance**: No `O(n)` searches on large datasets (used indexed lookups).
- [ ] **Deployment**: Policies are versioned in Git (GitOps).
```

## Anti-Patterns to Avoid
*   **Mixing Policy & Data**: Hardcoding specific users or configurations in Rego requires a redeploy for minor data changes. Always use `input` or `data`.
*   **Business Logic in OPA**: OPA is for *authorization* (can they?), not business logic (should they? / calculation). Calculate `account_balance` in the app; check `account_balance > 0` in OPA.
*   **Large Bundles**: Don't load GBs of data into OPA memory. Use "Partial Evaluation" or external data fetching for large datasets.

## Reference: Policy Templates
*   **Basic**: `templates/basic-allow-deny.rego.template`
*   **RBAC**: `templates/rbac-policy.rego.template`
*   **ABAC**: `templates/abac-policy.rego.template`
*   **Multi-Tenant**: `templates/multi-tenant.rego.template`
*   **K8s Admission**: `templates/kubernetes-admission.rego.template`
*   **API Gateway**: `templates/api-gateway-authz.rego.template`
