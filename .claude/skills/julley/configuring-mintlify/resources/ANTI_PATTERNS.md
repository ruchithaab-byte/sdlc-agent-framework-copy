# Anti-Patterns and Pitfalls

## Critical Configuration Mistakes

### 1. OpenAPI 2.0 Usage
- **Issue**: Mintlify does not support OpenAPI 2.0, resulting in completely blank API pages.
- **Resolution**: Mandatory conversion to OpenAPI 3.x.
- **Validation**: Use `mint openapi-check` or Swagger Editor.

### 2. Path Mismatch
- **Issue**: Discrepancies between MDX frontmatter and OpenAPI spec paths cause blank pages.
- **Example**: Frontmatter has `GET /users/{id}/` but spec has `/users/{id}`.
- **Resolution**: Enforce exact character-for-character matching, including trailing slashes.
- **Check**: Verify OpenAPI filename/alias matches exactly.

### 3. Case Sensitivity Failure
- **Issue**: Lowercase HTTP methods in frontmatter prevent page generation.
- **Example**: Navigation uses `get /users` instead of `GET /users`.
- **Resolution**: Strict uppercase enforcement (GET, POST, PUT, DELETE) in all configurations.

### 4. Partial Inclusion Pitfall
- **Issue**: Manually including even one endpoint in `docs.json` navigation disables auto-generation for the entire OpenAPI spec.
- **Resolution**: Choose fully automatic OR fully manual navigation strategy - no mixing.
- **Workaround**: If mixing is required, you must explicitly list *all* required endpoints.

### 5. File/Operation Conflict
- **Issue**: An MDX file exists at the same path as an OpenAPI operation.
- **Resolution**: Use the `x-mint` extension in the OpenAPI spec to redirect the operation to a custom path.
```yaml
paths:
  /users:
    get:
      x-mint:
        href: /custom-users-page
```

## Maintenance Hazards

### 6. Undocumented Selectors
- **Issue**: Using browser inspection to find platform identifiers (e.g., `APIPlaygroundInput`) for custom CSS.
- **Risk**: Selectors are unstable and may change with platform updates, breaking styles.
- **Resolution**: If used, schedule regular maintenance reviews to verify selectors still exist.

## Summary Table

| Anti-Pattern | Issue | Resolution |
|--------------|------|------------|
| OpenAPI 2.0 Usage | Blank API pages | Convert to OpenAPI 3.x |
| Path Mismatch | Blank pages | Enforce exact string matching |
| Case Sensitivity | Pages don't generate | Uppercase HTTP methods |
| Partial Inclusion | Missing operations | Choose auto OR manual |
| Undocumented Selectors | Breaks after updates | Schedule maintenance reviews |

