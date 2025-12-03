---
name: implementing-kong-gateway
description: Deploys Kong Gateway in DB-less mode. Handles routing, authentication, rate-limiting, and CORS for microservices. Use when configuring API gateways, routing public traffic, or integrating with service mesh.
version: 1.0.0
dependencies:
  - kong:3.4+
---

# Implementing Kong Gateway

## Overview

Implements Kong Gateway as an API gateway for production microservices using DB-less declarative configuration. Covers service topology, plugin architecture (CORS, Rate Limiting), and service mesh integration.

## Deployment Workflow

Copy this checklist to track your progress:

```markdown
Deployment Progress:
- [ ] Step 1: Create configuration file (from templates/kong.yml)
- [ ] Step 2: Validate configuration syntax
- [ ] Step 3: Configure deployment (from templates/docker-compose.yml)
- [ ] Step 4: Deploy and verify health
```

### Step 1: Create configuration file

Create `kong/kong.yml` using the template.

**Template**: [templates/kong.yml](templates/kong.yml)

**Key Configuration Rules**:
1.  **Format Version**: Always use `_format_version: "3.0"`.
2.  **Service Topology**: One Kong service per upstream microservice.
3.  **Path Handling**: Use `strip_path: false` for microservices to preserve full request paths.
4.  **Security**: Do NOT hardcode secrets. Use environment variables.

### Step 2: Validate configuration syntax

Before deploying, validate the declarative config file structure.

**Option A: Using Kong CLI (if installed)**
```bash
kong config parse kong/kong.yml
```

**Option B: Visual Inspection Checklist**
- [ ] `_format_version` is "3.0"
- [ ] Indentation is valid YAML (2 spaces)
- [ ] No duplicate route names
- [ ] Upstream URLs are reachable (use Docker service names like `http://auth-service:8080`)

### Step 3: Configure deployment

Create `docker-compose.yml` to deploy Kong in DB-less mode.

**Template**: [templates/docker-compose.yml](templates/docker-compose.yml)

**Best Practices**:
- `KONG_DATABASE: "off"`: Mandatory for declarative config.
- `volumes`: Mount `kong.yml` as `:ro` (read-only).
- `ports`: Bind Admin API (8001) to `127.0.0.1` or internal networks only.

### Step 4: Deploy and verify health

1.  Start Kong:
    ```bash
    docker-compose up -d kong
    ```

2.  Verify Status:
    ```bash
    curl -I http://localhost:8001/status
    ```
    *Expected: HTTP 200 OK*

3.  Verify Routes:
    ```bash
    curl -I http://localhost:8001/routes
    ```

## Plugin Architecture

Apply cross-cutting concerns at the appropriate scope.

| Plugin | Scope | Config Pattern |
| :--- | :--- | :--- |
| **CORS** | Global or Service | `origins: ["https://app.com"]`, `credentials: true` |
| **Rate Limiting** | Route or Service | `policy: local` (Redis for cluster), `fault_tolerant: true` |
| **Health Checks** | Service | Active checks on `/actuator/health` (Spring Boot) |

## Common Anti-Patterns

| Anti-Pattern | Impact | Solution |
| :--- | :--- | :--- |
| **Database Mode in Prod** | Ops complexity, SPOF | Use DB-less mode (`KONG_DATABASE: "off"`). |
| **Hardcoded Upstreams** | Coupling, maintenance | Use Docker DNS/K8s Service names. |
| **Public Admin API** | Security vulnerability | Restrict port 8001 to internal/localhost. |
| **Strip Path True** | Routing failures | Use `strip_path: false` for path-aware apps. |
| **Missing Health Checks** | Traffic to bad pods | Configure active health checks on all services. |

## Troubleshooting

- **404 No Route Matched**: Check `strip_path` and route regex. Ensure `Host` header matches if using host-based routing.
- **502 Bad Gateway**: Upstream unreachable. Check Docker network and Service URL.
- **503 Unavailable**: Rate limit exceeded or unhealthy upstream. Check plugin config.
