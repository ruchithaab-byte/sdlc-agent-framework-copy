# 3. JWT Token Strategy and Security

Date: 2025-11-28

## Status
Accepted

## Context
The authentication microservice requires a secure, scalable token-based authentication mechanism that can:
- Support stateless authentication to enable horizontal scaling
- Handle 100,000 authentication requests per minute
- Maintain token validation response time under 50ms (P95)
- Provide secure token revocation capabilities
- Support both short-lived access tokens and long-lived refresh tokens
- Enable secure key rotation without service disruption

Key security considerations:
- Token tampering and forgery prevention
- Protection against token replay attacks
- Secure token storage on both client and server
- Compliance with OWASP and NIST authentication standards
- Key compromise recovery mechanisms

## Decision
We will implement a dual-token JWT strategy with the following specifications:

### Token Types and Lifecycle

1. **Access Tokens**
   - Algorithm: RS256 (RSA-SHA256 with 2048-bit keys)
   - TTL: 15 minutes (short-lived to limit exposure)
   - Claims: sub (user_id), iat, exp, aud, roles, permissions
   - Purpose: API authentication and authorization
   - Storage: HttpOnly, Secure, SameSite cookies for web clients
   - No server-side persistence (fully stateless)

2. **Refresh Tokens**
   - Format: Opaque tokens (cryptographically random 256-bit values)
   - TTL: 7 days (configurable per client application)
   - Storage: Hashed in PostgreSQL database with user_id association
   - Purpose: Obtaining new access tokens without re-authentication
   - Rotation: Automatic rotation on each use (refresh token rotation)
   - Revocation: Immediate via database flag update

### Key Management

1. **RSA Key Pair Generation**
   - 2048-bit RSA keys for production (4096-bit for high-security environments)
   - Generated using cryptographically secure random number generator
   - Private keys stored exclusively in HashiCorp Vault
   - Public keys exposed via JWKS (JSON Web Key Set) endpoint

2. **Key Rotation Strategy**
   - Automatic rotation every 90 days
   - Overlap period: 30 days (old and new keys both valid)
   - Process:
     1. Generate new key pair in Vault
     2. Add new public key to JWKS endpoint
     3. Start signing new tokens with new key
     4. Maintain old key for validation during overlap period
     5. Remove old key from JWKS after overlap period
   - Emergency rotation: Manual trigger for key compromise scenarios

3. **Key Storage and Access**
   - Primary storage: HashiCorp Vault with encryption at rest
   - Access control: Service account with minimal permissions
   - Audit: All key access logged to security monitoring system
   - Backup: Encrypted backups in separate geographic region

### Token Security Controls

1. **Token Validation**
   - Signature verification using public key from JWKS
   - Expiration time (exp claim) validation
   - Issuer (iss claim) verification
   - Audience (aud claim) validation
   - Not-before (nbf claim) validation
   - JWT ID (jti claim) for token tracking

2. **Token Revocation**
   - Redis-based blacklist for revoked access tokens
   - TTL on blacklist entries matches token expiration
   - Refresh token revocation via database flag
   - Blacklist check: O(1) operation using Redis SET
   - Automatic cleanup of expired blacklist entries

3. **Rate Limiting**
   - Token generation: 5 requests per minute per user
   - Token validation: 10,000 requests per minute (internal service)
   - Token refresh: 60 requests per hour per user
   - Failed attempts trigger account lockout (5 attempts → 15-minute lockout)

### Implementation Details

1. **Token Generation Flow**
   ```
   1. User authenticates successfully
   2. Service retrieves private key from Vault
   3. Generate access token JWT with user claims
   4. Generate cryptographic random refresh token
   5. Hash refresh token with bcrypt (cost factor 12)
   6. Store hashed refresh token in database
   7. Cache user permissions in Redis (TTL: 5 minutes)
   8. Return both tokens to client
   ```

2. **Token Validation Flow**
   ```
   1. Extract JWT from Authorization header
   2. Check Redis blacklist for token revocation
   3. Retrieve public key from JWKS endpoint (cached)
   4. Verify token signature
   5. Validate claims (exp, iss, aud, nbf)
   6. Extract user claims and permissions
   7. Cache validation result in Redis (TTL: 1 minute)
   8. Return validation result
   ```

3. **Token Refresh Flow**
   ```
   1. Validate refresh token against database
   2. Check if refresh token is revoked or expired
   3. Verify token belongs to requesting user
   4. Generate new access token
   5. Generate new refresh token (rotation)
   6. Revoke old refresh token
   7. Store new refresh token hash in database
   8. Return new token pair
   ```

### Performance Optimization

1. **Caching Strategy**
   - Public keys cached in memory with 1-hour TTL
   - User permissions cached in Redis with 5-minute TTL
   - Token validation results cached for 1 minute
   - JWKS endpoint responses cached with CDN (15-minute TTL)

2. **Database Optimization**
   - Index on refresh_token.token_hash for fast lookups
   - Index on refresh_token.user_id for user session management
   - Partitioning for audit logs by timestamp
   - Connection pooling with PgBouncer (pool size: 100)

3. **Redis Optimization**
   - Token blacklist using SET data structure
   - TTL-based automatic cleanup
   - Redis Sentinel for high availability
   - Read replicas for validation operations

## Consequences

### Positive Consequences
- **Stateless Architecture**: Access tokens contain all necessary information, eliminating database lookups for validation
- **High Performance**: Token validation achieves <10ms latency with Redis caching, well below 50ms target
- **Scalability**: Stateless tokens enable linear horizontal scaling
- **Security**: RS256 algorithm provides strong cryptographic security with public-key verification
- **Revocation Capability**: Redis blacklist enables immediate token revocation when needed
- **Key Rotation**: 90-day rotation with overlap period ensures security without service disruption
- **Compliance**: Meets OWASP ASVS Level 2 and NIST 800-63B requirements

### Negative Consequences
- **Token Size**: JWT tokens are larger than opaque tokens (typical size: 800-1200 bytes)
- **Revocation Complexity**: Stateless tokens require Redis blacklist for revocation
- **Clock Synchronization**: Requires NTP synchronization across all services for exp validation
- **Key Management Overhead**: HashiCorp Vault adds infrastructure complexity
- **Migration Impact**: Existing session-based systems require significant refactoring

### Risk Mitigation
- **Key Compromise**: Emergency key rotation procedure with automated notifications
- **Token Theft**: Short 15-minute TTL limits exposure window
- **Replay Attacks**: jti claim + Redis tracking prevents token reuse
- **XSS Attacks**: HttpOnly cookies prevent JavaScript access to tokens
- **CSRF Attacks**: SameSite=Strict cookie attribute prevents cross-site requests
- **Redis Failure**: Graceful degradation - deny access if blacklist unavailable (fail-secure)

### Trade-offs Considered

1. **Symmetric (HS256) vs Asymmetric (RS256)**
   - Chose RS256 despite higher CPU cost because:
     - Public key can be shared with downstream services for validation
     - No shared secret distribution required
     - Better key rotation capabilities
     - Industry standard for microservices

2. **Opaque Tokens vs JWT**
   - Chose JWT for access tokens because:
     - Eliminates database lookup on every request
     - Contains user claims for authorization
     - Can be validated by downstream services independently
   - Chose opaque tokens for refresh tokens because:
     - Enables immediate revocation via database
     - Smaller size for storage efficiency
     - Lower security risk if compromised

3. **Token TTL Selection**
   - 15-minute access token: Balance between security and user experience
   - 7-day refresh token: Reduces re-authentication frequency while maintaining security
   - Configurable per client application for flexibility

### Future Considerations
- **Token Binding**: Consider implementing token binding (RFC 8471) for additional security
- **JWT Encrypted Tokens**: Evaluate JWE (JSON Web Encryption) for sensitive claims
- **Shorter Access Token TTL**: Consider reducing to 5 minutes for high-security applications
- **Refresh Token Families**: Implement refresh token families for better revocation tracking
- **mTLS for Service-to-Service**: Consider mutual TLS for internal service authentication
- **Hardware Security Modules (HSM)**: Evaluate HSM for key storage in high-security environments
- **Passwordless Authentication**: Plan for WebAuthn/FIDO2 support for passwordless flows

## References
- RFC 7519: JSON Web Token (JWT)
- RFC 7515: JSON Web Signature (JWS)
- RFC 7517: JSON Web Key (JWK)
- OWASP Authentication Cheat Sheet
- NIST SP 800-63B: Digital Identity Guidelines
- OAuth 2.0 Token Revocation (RFC 7009)
