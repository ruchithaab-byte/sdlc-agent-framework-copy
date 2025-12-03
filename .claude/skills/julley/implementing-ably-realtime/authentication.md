# Authentication

Token authentication is mandatory for client-side applications. Basic authentication (API keys) is suitable for trusted server-side only.

See [SKILL.md](SKILL.md) for overview.

## Client-Side Token Authentication

**Pattern**: Token Authentication for client-side (mandatory)

**Anti-Pattern**: Basic Auth on Client-Side (Golden Key vulnerability)

```javascript
// Frontend: Use token authentication (mandatory)
const ably = new Ably.Realtime({
  authUrl: '/api/ably-token',  // Backend endpoint generates token
  authMethod: 'GET'
});

// Backend: Generate short-lived token
app.get('/api/ably-token', authenticate, (req, res) => {
  const tokenRequest = {
    clientId: req.user.id,
    capability: { 'chat:*': ['subscribe', 'publish'] },
    ttl: 3600000  // 1 hour
  };
  const token = ably.auth.requestToken(tokenRequest);
  res.json(token);
});
```

**Best Practice**: Tokens are short-lived, revocable, and fine-grained. Never expose API keys to client-side code.

## Server-Side Basic Authentication

**Pattern**: Basic Authentication for server-side (trusted backend)

```javascript
// Backend: Use API key (persistent, low-latency)
const ably = new Ably.Rest({
  key: process.env.ABLY_API_KEY
});

// No token renewal overhead for server-side
```

**Best Practice**: API keys are persistent and suitable for trusted server environments only.

## Security Guidelines

**CRITICAL**: Never hardcode sensitive information:
- ❌ No API keys in client-side code
- ❌ No API keys in example code
- ❌ No credentials in version control
- ✅ Use environment variables for all API keys
- ✅ Use token authentication for all client-side applications
- ✅ Generate tokens on backend with appropriate capabilities and TTL
- ✅ Route sensitive operations through secure backend channels

**Operational Constraints**:
- Token authentication is mandatory for client-side (browsers, mobile devices)
- Basic authentication (API keys) is suitable for trusted server-side only
- Tokens should have appropriate TTL (typically 1 hour) and be renewed before expiration
- Monitor token generation service availability (dependency for client connectivity)
- Use Search-Only API keys for read-only operations when available

