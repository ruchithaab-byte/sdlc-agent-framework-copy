# 6. Security and Compliance Architecture

Date: 2025-11-28

## Status
Accepted

## Context
The authentication microservice is a critical security component that requires the highest level of security controls and compliance measures:

**Security Requirements:**
- Protection against OWASP Top 10 vulnerabilities
- Defense against brute force attacks and credential stuffing
- Secure storage of credentials and sensitive data
- Encryption at rest and in transit
- Protection against token theft and replay attacks
- Secure key management and rotation
- Comprehensive security audit logging

**Compliance Requirements from PRD:**
- GDPR (General Data Protection Regulation)
- SOC 2 Type II
- Industry-specific standards (HIPAA, PCI DSS if applicable)
- OWASP ASVS Level 2
- NIST 800-63B Digital Identity Guidelines

**Threat Model:**
- External attackers attempting unauthorized access
- Credential theft via phishing or malware
- Token theft and replay attacks
- SQL injection and XSS attacks
- DDoS and resource exhaustion attacks
- Insider threats and privilege abuse
- Man-in-the-middle attacks

## Decision
We will implement a defense-in-depth security architecture with multiple layers of protection:

### 1. Credential Security

**Password Hashing**
```
Algorithm: Argon2id (winner of Password Hashing Competition)
Parameters:
  - Memory: 64 MB (65536 KiB)
  - Iterations: 3
  - Parallelism: 4 threads
  - Salt: 16 bytes (cryptographically random)
  - Output: 32 bytes

Rationale:
  - Argon2id combines best of Argon2i (side-channel resistance) and Argon2d (GPU resistance)
  - Memory-hard algorithm prevents GPU/ASIC attacks
  - ~500ms hashing time provides good balance between security and UX
  - Configurable parameters allow future tuning as hardware improves

Migration from existing systems:
  - Legacy bcrypt/PBKDF2 hashes supported during transition
  - Transparent upgrade on next successful login
  - All new passwords use Argon2id from day one
```

**Password Policy Enforcement**
```yaml
Minimum Requirements:
  - Length: 12 characters minimum (recommended: 16+)
  - Complexity: At least 3 of the following:
    - Uppercase letters (A-Z)
    - Lowercase letters (a-z)
    - Numbers (0-9)
    - Special characters (!@#$%^&*...)

Additional Controls:
  - Password history: Cannot reuse last 12 passwords
  - Password age: Maximum 90 days for privileged accounts (optional for regular users)
  - Dictionary check: Reject common passwords (top 10,000 list)
  - Breach check: Integrate with Have I Been Pwned API (k-anonymity)
  - Personal info check: Reject passwords containing username/email
  - Unicode support: Allow international characters (with normalization)

Implementation:
  - zxcvbn library for password strength estimation
  - Real-time feedback during password creation
  - Clear error messages without revealing policy details to attackers
```

**Credential Storage**
```sql
-- Users table with secure credential storage
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_normalized VARCHAR(255) UNIQUE NOT NULL,  -- Lowercase, trimmed
    password_hash VARCHAR(255) NOT NULL,            -- Argon2id hash
    password_algorithm VARCHAR(50) NOT NULL DEFAULT 'argon2id',
    password_changed_at TIMESTAMP NOT NULL,
    password_history JSONB,                         -- Array of previous hashes
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP,
    lockout_reason VARCHAR(100),
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret_encrypted VARCHAR(512),              -- AES-256 encrypted
    backup_codes_encrypted TEXT,                    -- Hashed backup codes
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Encryption for sensitive fields
-- Using application-level encryption with key from Vault
-- Format: {encryption_version}${iv}${ciphertext}${auth_tag}
-- Example: v1$a1b2c3d4$e5f6g7h8$i9j0k1l2
```

### 2. Attack Prevention

**Rate Limiting Strategy**
```yaml
Global Rate Limits (per IP address):
  - Default: 100 requests/minute
  - Burst allowance: 200 requests (token bucket)
  - DDoS threshold: 1000 requests/minute → temporary ban

Endpoint-Specific Limits:
  Login:
    - Rate: 5 attempts/minute per IP
    - Burst: 10 attempts
    - Lockout: 15 minutes after 5 failed attempts
    - Progressive delay: 1s, 2s, 4s, 8s, 16s

  Registration:
    - Rate: 3 registrations/hour per IP
    - Burst: 5 registrations
    - CAPTCHA required after 2 attempts

  Password Reset:
    - Rate: 2 requests/hour per email address
    - Rate: 5 requests/hour per IP
    - Email rate limiting: Max 3 reset emails/day per address

  Token Refresh:
    - Rate: 60 requests/hour per user
    - Burst: 100 requests

  MFA Verification:
    - Rate: 10 attempts/5 minutes per user
    - Lockout: 30 minutes after 10 failed attempts

  API Calls:
    - Token validation: 10,000 req/min (internal services)
    - Authorization check: 5,000 req/min (internal services)
    - User lookup: 1,000 req/min per service

Implementation:
  - Redis with sliding window algorithm
  - Distributed rate limiting across all service instances
  - Graceful degradation if Redis unavailable (local rate limiting)
  - 429 Too Many Requests response with Retry-After header
```

**Account Lockout Policy**
```yaml
Lockout Triggers:
  1. Failed Login Attempts:
     - Threshold: 5 consecutive failures
     - Duration: 15 minutes (exponential backoff: 15m, 30m, 1h, 24h)
     - Reset: Successful login or manual unlock by admin

  2. Failed MFA Attempts:
     - Threshold: 10 consecutive failures
     - Duration: 30 minutes
     - Alert: Security team notification

  3. Password Reset Abuse:
     - Threshold: 5 requests in 1 hour
     - Duration: 24 hours
     - Action: Require admin intervention

  4. Suspicious Activity:
     - Multiple countries in short time
     - Unusual access patterns
     - Action: Require email verification

Lockout Response:
  - Clear error message: "Account temporarily locked"
  - No distinction between locked account vs invalid password (prevent user enumeration)
  - Email notification to account owner
  - Self-service unlock via email link (for non-suspicious lockouts)
  - Admin override capability with audit trail
```

**CAPTCHA Integration**
```yaml
Triggers:
  - After 2 failed login attempts
  - All registration requests (bot prevention)
  - Password reset requests
  - Any request from known VPN/proxy IPs

Provider: hCaptcha (privacy-focused) or Google reCAPTCHA v3
Fallback: Mathematical challenge for accessibility

Implementation:
  - Server-side verification of CAPTCHA tokens
  - Score-based challenge (reCAPTCHA v3: show challenge if score < 0.5)
  - Bypass for trusted IPs (internal network)
  - Monitoring of CAPTCHA solve rates
```

### 3. Data Protection

**Encryption at Rest**
```yaml
Database Encryption:
  - Volume encryption: AES-256 (managed by cloud provider)
  - Transparent Data Encryption (TDE): Enabled on PostgreSQL
  - Column-level encryption: Sensitive PII fields

Application-Level Encryption:
  - Algorithm: AES-256-GCM (authenticated encryption)
  - Key management: HashiCorp Vault
  - Envelope encryption pattern:
    1. Data Encryption Key (DEK): Unique per record, stored encrypted
    2. Key Encryption Key (KEK): Stored in Vault, rotated annually
  - Encrypted fields:
    - Email addresses (for GDPR compliance)
    - Phone numbers
    - MFA secrets
    - OAuth tokens
    - Backup codes

Implementation:
  -- Example encrypted field structure
  {
    "version": "v1",           -- Encryption version for algorithm agility
    "encrypted_dek": "...",    -- DEK encrypted with KEK
    "iv": "...",               -- Initialization vector
    "ciphertext": "...",       -- Encrypted data
    "auth_tag": "..."          -- GCM authentication tag
  }
```

**Encryption in Transit**
```yaml
TLS Configuration:
  - Protocol: TLS 1.3 (TLS 1.2 as fallback)
  - Cipher suites (priority order):
    - TLS_AES_128_GCM_SHA256
    - TLS_AES_256_GCM_SHA384
    - TLS_CHACHA20_POLY1305_SHA256
  - Certificate: Let's Encrypt / AWS ACM with automated renewal
  - HSTS: Enabled with max-age=31536000, includeSubDomains
  - Certificate pinning: For mobile applications

Service-to-Service Communication:
  - mTLS (mutual TLS) via Istio service mesh
  - Certificate rotation: Every 24 hours (automated by Istio)
  - Cipher suites: Same as external TLS
  - Certificate validation: Strict mode, no self-signed certificates

Database Connections:
  - TLS required for all connections
  - Certificate verification: Verify full certificate chain
  - No fallback to unencrypted connections
```

**Secrets Management**
```yaml
HashiCorp Vault Configuration:
  - Deployment: High-availability cluster (3 nodes)
  - Storage backend: Encrypted Consul cluster
  - Unsealing: Shamir's Secret Sharing (5 keys, 3 threshold)
  - Authentication: Kubernetes service accounts
  - Audit logging: All access logged to dedicated audit log

Secrets Stored in Vault:
  - Database credentials (rotated every 90 days)
  - JWT signing keys (rotated every 90 days)
  - Data encryption keys (KEK)
  - OAuth client secrets
  - Third-party API keys (SendGrid, Twilio)
  - TLS certificates (if not using ACM)

Secret Rotation:
  - Automated rotation schedule:
    - Database passwords: 90 days
    - JWT signing keys: 90 days (with 30-day overlap)
    - API keys: 180 days (vendor-dependent)
    - Encryption keys (KEK): 365 days
  - Emergency rotation: Triggered manually for compromises
  - Zero-downtime rotation: Support for multiple valid keys during overlap

Access Control:
  - Principle of least privilege
  - Service accounts with minimal permissions
  - No human access to production secrets (break-glass procedure for emergencies)
  - All access audited and alerted
```

### 4. Security Monitoring and Incident Response

**Audit Logging**
```yaml
Events to Log:
  Authentication Events:
    - Successful login (user_id, IP, user_agent, timestamp)
    - Failed login (email, IP, reason, timestamp)
    - Logout (user_id, IP, timestamp)
    - Password change (user_id, changed_by, timestamp)
    - Account lockout (user_id, reason, timestamp)
    - Account unlock (user_id, unlocked_by, timestamp)

  Authorization Events:
    - Permission grant/revoke (user_id, permission, granted_by)
    - Role assignment/removal (user_id, role, assigned_by)
    - Authorization denied (user_id, permission, resource, reason)

  Security Events:
    - MFA setup/removal (user_id, method, timestamp)
    - Token revocation (user_id, token_type, reason)
    - Suspicious activity detection (user_id, activity_type, details)
    - API key creation/revocation (user_id, key_id, timestamp)

  Administrative Events:
    - Configuration changes (admin_id, change_type, before, after)
    - User impersonation (admin_id, target_user_id, duration)
    - Security policy changes (admin_id, policy, change)

Log Format:
  {
    "timestamp": "2025-11-28T10:30:00.123Z",
    "event_type": "login_success",
    "user_id": "uuid",
    "session_id": "uuid",
    "ip_address": "1.2.3.4",
    "user_agent": "Mozilla/5.0...",
    "geo_location": {"country": "US", "city": "New York"},
    "mfa_used": true,
    "request_id": "uuid",
    "metadata": {...}
  }

Storage:
  - TimescaleDB for structured audit logs (7-year retention)
  - S3/Cloud Storage for long-term archival (encrypted)
  - Real-time streaming to SIEM (Splunk/ELK)
  - Immutable append-only logs (no deletion/modification allowed)
```

**Security Monitoring**
```yaml
Real-Time Alerts:
  Critical (PagerDuty):
    - Multiple failed login attempts from single IP (>20/minute)
    - Account takeover pattern detected
    - Unusual privilege escalation
    - Token signing key accessed outside rotation schedule
    - Database credential change outside rotation schedule

  High Priority (Slack + Email):
    - Failed MFA rate spike (>10% failure rate)
    - Password reset rate spike (>3x baseline)
    - Geo-anomaly: Login from new country
    - Session hijacking indicators
    - API rate limit violations (>100/minute from single IP)

  Medium Priority (Slack):
    - Account lockouts (>5 users in 10 minutes)
    - Permission changes outside business hours
    - New role assignments
    - Vault access by non-service accounts

Anomaly Detection:
  - Machine learning model for behavioral analysis
  - Baseline: Normal login patterns (time, location, device)
  - Alerts on deviations: New device, new location, unusual time
  - Risk scoring: Combine multiple factors for overall risk score

Threat Intelligence Integration:
  - IP reputation check (AbuseIPDB, IPQualityScore)
  - Email breach check (Have I Been Pwned)
  - Known malicious IPs blocked at WAF level
  - Tor exit nodes flagged for additional verification
```

**Incident Response**
```yaml
Incident Response Plan:

  Phase 1: Detection (Target: <5 minutes)
    - Automated alert triggers
    - Security team notified via PagerDuty
    - Initial triage by on-call engineer

  Phase 2: Containment (Target: <30 minutes)
    - Identify affected accounts/systems
    - Revoke compromised tokens
    - Lock affected accounts
    - Block malicious IPs at WAF
    - Isolate compromised services

  Phase 3: Investigation (Target: <2 hours)
    - Review audit logs
    - Identify attack vector
    - Assess scope of compromise
    - Collect evidence for forensics

  Phase 4: Remediation (Target: <24 hours)
    - Patch vulnerabilities
    - Rotate compromised credentials
    - Notify affected users
    - Implement additional controls
    - Document lessons learned

  Phase 5: Recovery (Target: <48 hours)
    - Restore normal operations
    - Monitor for recurrence
    - Update security policies
    - Conduct post-mortem

Runbooks:
  - Account Takeover Response
  - Data Breach Response
  - DDoS Attack Response
  - Insider Threat Response
  - Third-Party Compromise Response
```

### 5. Compliance Controls

**GDPR Compliance**
```yaml
Data Subject Rights:
  Right to Access:
    - API endpoint: GET /api/v1/users/{user_id}/data-export
    - Returns: All personal data in machine-readable JSON
    - Includes: Profile, login history, permissions, audit logs
    - Response time: <48 hours

  Right to Erasure (Right to be Forgotten):
    - API endpoint: DELETE /api/v1/users/{user_id}
    - Action: Soft delete (anonymize PII, retain audit logs)
    - Retention: Audit logs kept for 7 years (legal requirement)
    - Anonymization: Replace PII with hashed values

  Right to Data Portability:
    - Export format: JSON, CSV
    - Includes: User profile, preferences, activity history

  Right to Rectification:
    - API endpoint: PATCH /api/v1/users/{user_id}
    - Audit trail: All changes logged

  Right to Restrict Processing:
    - Account suspension (retain data, block processing)

Consent Management:
  - Explicit consent for data processing
  - Granular consent (email marketing, analytics, etc.)
  - Consent audit trail (when granted, by whom)
  - Easy consent withdrawal

Data Protection Measures:
  - Privacy by design: Minimal data collection
  - Data minimization: Only collect necessary data
  - Purpose limitation: Use data only for stated purpose
  - Storage limitation: Delete data after retention period
  - Encryption: All PII encrypted at rest
  - DPO contact information in privacy policy
```

**SOC 2 Type II Controls**
```yaml
Security Principle:
  - Access controls: RBAC with least privilege
  - Encryption: At rest and in transit
  - Vulnerability management: Monthly scans, quarterly pen tests
  - Incident response: Documented procedures, tested quarterly
  - Change management: All changes reviewed and approved

Availability Principle:
  - SLA: 99.9% uptime
  - Monitoring: 24/7 automated monitoring
  - Failover: Automated failover tested quarterly
  - Backups: Daily backups, tested monthly
  - Disaster recovery: DR plan tested bi-annually

Confidentiality Principle:
  - Data classification: PII, confidential, public
  - Encryption: AES-256 for confidential data
  - Access logging: All access to confidential data logged
  - Secure disposal: Cryptographic erasure

Processing Integrity Principle:
  - Input validation: All inputs validated and sanitized
  - Error handling: Secure error messages (no sensitive info)
  - Audit logging: All transactions logged
  - Data integrity checks: Checksums, signatures

Privacy Principle (if applicable):
  - Notice: Clear privacy policy
  - Choice: Opt-in for optional processing
  - Collection: Minimal data collection
  - Use: Purpose limitation
  - Access: Data subject access rights
  - Disclosure: Third-party disclosure logging
  - Security: Encryption, access controls
  - Quality: Data accuracy mechanisms
  - Monitoring: Ongoing compliance monitoring
```

**Additional Compliance Standards**
```yaml
OWASP ASVS Level 2:
  - Authentication: Multi-factor authentication available
  - Session management: Secure session handling
  - Access control: Comprehensive authorization checks
  - Input validation: All inputs validated
  - Cryptography: Industry-standard algorithms
  - Error handling: Secure error messages
  - Data protection: Encryption at rest and in transit
  - Communications: TLS 1.3
  - Malicious code: Dependency scanning, SAST/DAST
  - Business logic: Rate limiting, anti-automation
  - Configuration: Secure defaults, hardened deployment

NIST 800-63B (Digital Identity Guidelines):
  - Authenticator Assurance Level 2 (AAL2)
  - Password requirements: Length, complexity, breach check
  - MFA required for privileged accounts
  - Account recovery: Secure password reset process
  - Session management: Idle timeout, absolute timeout
  - Threat modeling: Regular threat assessments
```

## Consequences

### Positive Consequences
- **Strong Security Posture**: Defense-in-depth approach protects against multiple attack vectors
- **Compliance Ready**: Meets GDPR, SOC 2, OWASP ASVS, and NIST requirements
- **Comprehensive Audit Trail**: 7-year retention enables compliance and forensics
- **Incident Detection**: Real-time monitoring enables rapid response
- **Data Protection**: Encryption at rest and in transit protects sensitive data
- **Credential Security**: Argon2id hashing prevents credential cracking
- **Attack Prevention**: Rate limiting and CAPTCHA prevent brute force attacks

### Negative Consequences
- **User Experience Impact**: Security controls (CAPTCHA, MFA, rate limiting) may frustrate users
- **Performance Overhead**: Encryption and security checks add latency
- **Operational Complexity**: Key rotation, monitoring, and compliance require dedicated resources
- **Cost**: Security tools (SIEM, WAF, Vault) increase infrastructure costs
- **Privacy Trade-offs**: Extensive logging vs privacy concerns

### Risk Mitigation
- **Key Compromise**: Automated rotation and emergency rotation procedures
- **Insider Threats**: Least privilege, audit logging, separation of duties
- **Data Breach**: Encryption limits exposure, incident response plan
- **Compliance Violations**: Regular audits, automated compliance checks
- **False Positives**: Tuned anomaly detection, manual review process

### Future Considerations
- **Zero Trust Architecture**: Continuous verification, never trust always verify
- **Passwordless Authentication**: WebAuthn/FIDO2 for phishing-resistant authentication
- **Privacy-Enhancing Technologies**: Homomorphic encryption, secure multi-party computation
- **Quantum-Resistant Cryptography**: Prepare for post-quantum cryptography standards
- **Blockchain Audit Trail**: Immutable distributed audit logs
- **Behavioral Biometrics**: Continuous authentication based on typing patterns, mouse movements

## Testing and Validation

**Security Testing**
- Quarterly penetration testing by certified third-party
- Monthly vulnerability scanning (OWASP ZAP, Burp Suite)
- Continuous dependency scanning (Snyk, Dependabot)
- SAST (Static Application Security Testing): SonarQube
- DAST (Dynamic Application Security Testing): Weekly scans
- Secret scanning: Prevent secrets in code (git-secrets, TruffleHog)

**Compliance Audits**
- Annual SOC 2 Type II audit
- Quarterly internal compliance reviews
- Monthly access reviews
- Weekly backup restoration tests
- Daily log integrity checks

## References
- OWASP Top 10 2021
- OWASP Authentication Cheat Sheet
- OWASP Session Management Cheat Sheet
- NIST SP 800-63B Digital Identity Guidelines
- GDPR (Regulation EU 2016/679)
- SOC 2 Trust Services Criteria
- CIS Controls v8
- OWASP ASVS (Application Security Verification Standard)
- NIST Cybersecurity Framework
