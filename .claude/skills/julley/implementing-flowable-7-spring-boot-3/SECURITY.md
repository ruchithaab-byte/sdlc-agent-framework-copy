# Flowable Implementation Security Guidelines

## Critical Security Practices

### Credential Management

**CRITICAL**: Never hardcode credentials in configuration files or code.

**Required Practices**:
- ✅ Use environment variables for passwords (`${DB_PASSWORD}`)
- ✅ Use external credential management systems (Vault, AWS Secrets Manager)
- ✅ Separate DDL user credentials (migration) from application runtime credentials (execution)
- ✅ Use Secret Values in Flowable Control/Design for externalized configuration

**Prohibited**:
- ❌ Hardcoded passwords in `application.properties` or Java code
- ❌ Credentials in version control
- ❌ Shared credentials across environments

### Process Definition Security

- **Validate Inputs**: Sanitize all process variables entering the system.
- **Access Control**: Configure Spring Security to restrict access to Flowable REST APIs (`/process-api/**`, `/cmmn-api/**`, `/dmn-api/**`).
- **Identity Management**: Integrate with enterprise IdP (LDAP/AD/OIDC) rather than using Flowable's internal identity tables for production users.

