# Troubleshooting & Workarounds

## Workarounds

### 1. Records vs JPA Entities Mapping
**Problem**: Records cannot be used as JPA Entities (Hibernate requires mutability/proxies).
**Solution**: Use Records for DTOs, traditional POJOs for Entities. Map explicitly in the Service layer.

### 2. Jakarta EE Namespace Migration
**Problem**: Spring Boot 3.x requires `jakarta.*` namespace.
**Solution**: Replace `javax.persistence.*`, `javax.servlet.*`, etc., with `jakarta.*`. Use OpenRewrite or IDE tools.

### 3. Property Migration
**Problem**: Configuration property keys changed in 3.x.
**Solution**: Use `spring-boot-properties-migrator` dependency to generate a report on startup, then update `application.properties`.

### 4. Virtual Threads Configuration
**Problem**: Enabling Virtual Threads requires explicit config.
**Solution**: Set `spring.threads.virtual.enabled=true`.

## Common Error Resolutions

### Jakarta Migration Failures
- **Symptom**: Compilation errors or ClassNotFoundExceptions for `javax.*`.
- **Fix**: Verify all imports are `jakarta.*`. Check transitive dependencies.

### Property Migration Issues
- **Symptom**: App fails to start or config is ignored.
- **Fix**: Check startup logs from `properties-migrator`. Update keys (e.g., `spring.redis` -> `spring.data.redis`).

### Tracing Setup Failures
- **Symptom**: No traces in Zipkin.
- **Fix**: Verify OpenTelemetry bridge dependency. Check `management.tracing.sampling.probability=1.0`. Check Zipkin URL accessibility.

