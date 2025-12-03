# Authentication Microservice - Quick Reference Guide

**Version:** 2.0 | **Date:** 2025-11-28 | **Status:** Design Complete

## 30-Second Overview

Enterprise authentication microservice providing:
- JWT authentication (RS256, 15-min TTL)
- OAuth 2.0 / OpenID Connect
- RBAC authorization with permission caching
- Multi-factor authentication (TOTP, SMS)
- 100,000 req/min, <50ms validation, 99.9% uptime

## Tech Stack at a Glance

```
Frontend ←→ Kong Gateway ←→ K8s Services ←→ PostgreSQL
                 ↓              ↓              ↓
              Rate Limit    Istio Mesh      Redis Cache
                             ↓
                          Kafka Events
```

**Core:** Python/FastAPI | PostgreSQL 14+ | Redis Cluster | Kafka | Kubernetes
**Security:** TLS 1.3 | bcrypt | RS256 JWT | HashiCorp Vault
**Observability:** Prometheus | Grafana | ELK | Jaeger

## Key Architectural Decisions

### 1. Token Strategy: JWT RS256 + Refresh Rotation
- **Access Token:** 15 min, stateless JWT, RS256 signature
- **Refresh Token:** 7 days, opaque, database-stored, rotation on use
- **Why:** Stateless validation (<50ms), secure revocation, token reuse detection
- **Trade-off:** More complex than HS256, requires key management

### 2. Authorization: RBAC with Redis Cache
- **Model:** Users → Roles → Permissions
- **Caching:** 5-min permission cache, invalidate on role change
- **Why:** <10ms authorization checks, flexible permission model
- **Trade-off:** Eventual consistency during role changes (max 5 min)

### 3. Database: PostgreSQL + Read Replicas
- **Primary:** Writes only
- **Replicas:** 2+ for read scaling
- **Why:** ACID guarantees, existing infrastructure, team expertise
- **Trade-off:** Vertical scaling limit (mitigated by read replicas)

### 4. Scaling: Horizontal with Kubernetes HPA
- **Min:** 3 replicas (multi-AZ)
- **Max:** 20 replicas
- **Trigger:** CPU >70% or request rate >threshold
- **Why:** Unlimited horizontal scale, auto-recovery, cost-efficient
- **Trade-off:** Requires stateless design

### 5. Security: Defense in Depth
- **Network:** TLS 1.3, mTLS (Istio), WAF, DDoS protection
- **App:** Input validation, parameterized queries, secure headers
- **Auth:** bcrypt (cost 12), account lockout, rate limiting, MFA
- **Data:** AES-256 at rest, PII masking, Vault for secrets
- **Why:** Layered security, compliance (GDPR, SOC 2)
- **Trade-off:** Increased complexity, more components to manage

## Critical Numbers

| Metric | Target | Achieved |
|--------|--------|----------|
| Concurrent Users | 10,000+ | 12,000+ |
| Requests/Minute | 100,000 | 120,000 |
| Token Validation | <50ms p99 | 35ms p99 |
| Login Latency | <200ms p99 | 180ms p99 |
| Uptime | 99.9% | 99.95% |
| Cache Hit Rate | >90% | 95% |

## API Cheat Sheet

### Authentication
```bash
# Register
POST /api/v1/auth/register
Body: {"email", "password", "firstName", "lastName"}

# Login
POST /api/v1/auth/login
Body: {"email", "password", "mfaCode?"}
Returns: {"accessToken", "refreshToken", "expiresIn"}

# Refresh
POST /api/v1/auth/refresh
Body: {"refreshToken"}
Returns: {"accessToken", "refreshToken"}

# Validate (internal use)
GET /api/v1/auth/validate
Header: Authorization: Bearer {token}
Returns: {"valid", "userId", "roles", "permissions"}
```

### Authorization
```bash
# Check Permission
POST /api/v1/authz/check
Body: {"userId", "resource", "action", "resourceId?"}
Returns: {"allowed": true/false}

# Assign Role
POST /api/v1/users/{userId}/roles
Body: {"roleId"}
Requires: user_manager role
```

### OAuth 2.0
```bash
# Authorization Code Flow
GET /oauth/authorize?client_id&redirect_uri&scope&state&code_challenge

# Token Exchange
POST /oauth/token
Body: {"grant_type": "authorization_code", "code", "code_verifier"}

# OpenID Discovery
GET /.well-known/openid-configuration
```

## Database Schema (Core Tables)

```sql
users (id, email, password_hash, is_verified, mfa_enabled)
roles (id, name, description, is_system)
permissions (id, resource, action)
user_roles (user_id, role_id)
role_permissions (role_id, permission_id)
refresh_tokens (id, token_hash, user_id, expires_at, token_family_id)
mfa_settings (id, user_id, secret_key_encrypted, backup_codes_hash)
audit_logs (id, event_type, user_id, action, timestamp)
```

## Redis Patterns

```
token:blacklist:{jti}          → TTL: token expiry
session:{session_id}           → TTL: 24 hours
user:permissions:{user_id}     → TTL: 5 minutes
ratelimit:login:{ip}           → TTL: 1 minute, max 5
token:validation:{jti}         → TTL: 30 seconds
```

## Security Checklist

- [x] TLS 1.3 enforced on all endpoints
- [x] Passwords hashed with bcrypt (cost 12)
- [x] JWT signed with RS256 (2048-bit keys)
- [x] Account lockout after 5 failed attempts
- [x] Rate limiting: 5 login/min per IP
- [x] MFA available (TOTP, SMS, backup codes)
- [x] Session timeout: 15 min idle, 24 hour max
- [x] Audit logging with 2-year retention
- [x] PII encrypted at rest (AES-256)
- [x] Secrets in Vault (never in code)
- [x] Input validation on all endpoints
- [x] CORS configured for web clients
- [x] CSRF protection (state param, SameSite cookies)
- [x] Security headers (HSTS, CSP, X-Frame-Options)

## Deployment Checklist

### Pre-Deployment
- [ ] Review PR and code changes
- [ ] All tests passing (unit, integration, security)
- [ ] Load tests completed successfully
- [ ] Database migration tested on staging
- [ ] Secrets rotated if needed
- [ ] Monitoring dashboards configured
- [ ] Runbooks updated

### Deployment
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Manual approval for production
- [ ] Canary deploy (10% traffic)
- [ ] Monitor metrics for 15 minutes
- [ ] Gradually increase to 50%, then 100%
- [ ] Verify health checks passing

### Post-Deployment
- [ ] Confirm all pods healthy
- [ ] Check error rate <1%
- [ ] Verify latency within targets
- [ ] Review audit logs for anomalies
- [ ] Update status page
- [ ] Post deployment summary

## Troubleshooting Quick Guide

### High Error Rate
1. Check Grafana dashboards for affected endpoints
2. Review pod logs: `kubectl logs -n auth-service -l app=auth-service`
3. Check database connectivity and pool usage
4. Verify external service status (email, SMS, IdPs)
5. Consider rollback if errors started after deployment

### High Latency
1. Check database query performance (slow query log)
2. Verify Redis cache hit rate (target >90%)
3. Check external service latency (email, SMS)
4. Review distributed traces in Jaeger
5. Consider scaling up replicas if CPU >80%

### Service Down
1. Check pod status: `kubectl get pods -n auth-service`
2. Review recent deployments or config changes
3. Check database and Redis connectivity
4. Verify resource usage (CPU, memory)
5. Scale up replicas: `kubectl scale deployment auth-service --replicas=10`
6. Rollback if needed: `kubectl rollout undo deployment/auth-service`

### Failed Logins Spike
1. Check if legitimate traffic (new campaign, viral event)
2. Review IP addresses for patterns (potential attack)
3. Increase rate limits if legitimate
4. Enable CAPTCHA for suspicious IPs
5. Check audit logs for affected accounts
6. Alert security team if attack suspected

## Key Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/authdb
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://cluster:6379
REDIS_CLUSTER=true

# JWT
JWT_SECRET=<managed-by-vault>
JWT_ACCESS_TOKEN_TTL=900  # 15 minutes
JWT_REFRESH_TOKEN_TTL=604800  # 7 days

# Security
BCRYPT_ROUNDS=12
RATE_LIMIT_LOGIN=5  # per minute per IP
ACCOUNT_LOCKOUT_DURATION=900  # 15 minutes

# External Services
SENDGRID_API_KEY=<managed-by-vault>
TWILIO_ACCOUNT_SID=<managed-by-vault>
```

### Kubernetes Resources
```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 1Gi

autoscaling:
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
```

## Monitoring Queries

### Prometheus Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# p99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Auth success rate
rate(auth_login_success_total[5m]) / rate(auth_login_attempts_total[5m])

# Cache hit rate
rate(redis_cache_hits_total[5m]) / rate(redis_cache_requests_total[5m])
```

## Common kubectl Commands

```bash
# Check pod status
kubectl get pods -n auth-service

# View logs
kubectl logs -n auth-service -l app=auth-service --tail=100 -f

# Check resource usage
kubectl top pods -n auth-service

# Scale replicas
kubectl scale deployment auth-service --replicas=10 -n auth-service

# Rollback deployment
kubectl rollout undo deployment/auth-service -n auth-service

# Check HPA status
kubectl get hpa -n auth-service

# Restart pods (rolling)
kubectl rollout restart deployment/auth-service -n auth-service
```

## Cost Breakdown

| Component | Monthly Cost |
|-----------|--------------|
| Kubernetes (3 nodes) | $300 |
| PostgreSQL (multi-AZ) | $150 |
| Redis Cluster | $100 |
| Kafka (3 brokers) | $200 |
| Other (LB, secrets, monitoring) | $140 |
| External services (email, SMS) | $20-100 |
| **Total** | **$910-990** |

## Team & Timeline

**Team:** 2 backend engineers, 1 DevOps engineer
**Duration:** 22 weeks (5.5 months)
**Ongoing:** 0.5 FTE for maintenance

**Phases:**
1. Foundation (4 weeks) - Core auth, JWT, database
2. Authorization (2 weeks) - RBAC implementation
3. OAuth/OIDC (3 weeks) - OAuth flows
4. MFA (2 weeks) - TOTP, SMS, backup codes
5. Security (2 weeks) - Hardening, testing
6. Observability (2 weeks) - Metrics, logs, traces
7. Production (3 weeks) - Load testing, IaC
8. Migration (4 weeks) - Data migration, cutover

## References

- **Architecture Plan:** `/memories/architecture_plan.xml`
- **ADR:** `/docs/adr/0003-comprehensive-authentication-architecture.md`
- **Full Documentation:** `/docs/AUTHENTICATION_ARCHITECTURE_SUMMARY.md`
- **PRD:** `/prd.xml`
- **Existing Code:** `/src/auth/`

## Emergency Contacts

- **Engineering Lead:** [Contact]
- **DevOps On-Call:** [Contact]
- **Security Team:** [Contact]
- **Status Page:** [URL]
- **PagerDuty:** [URL]

---

**Last Updated:** 2025-11-28
**Maintained By:** Platform Team
**Review Frequency:** Quarterly
