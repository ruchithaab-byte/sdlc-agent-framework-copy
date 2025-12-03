# Troubleshooting and Workarounds

## Common Issues & Resolutions

### Blank API Pages
**Symptoms**: API pages fail to render or show empty content.
**Steps**:
1. **Validate OpenAPI Version**: Ensure spec is strictly OpenAPI 3.x. Convert 2.0 specs.
2. **Check Path Matching**: Verify MDX frontmatter path matches OpenAPI spec exactly, character-for-character (check trailing slashes).
3. **Verify HTTP Methods**: Ensure methods in frontmatter are UPPERCASE (`GET`, `POST`).
4. **Confirm Filename**: Check that the `openapi` path in frontmatter matches the file location.

### API Playground Failures
**Symptoms**: Requests fail, authentication is missing, or CORS errors.
**Steps**:
1. **Check CORS**: If using non-proxied mode (direct browser requests), ensure target API allows Mintlify domain.
2. **Verify Field Names**: Field names in `apiPlaygroundInputs` (user data) must *exactly* match the OpenAPI `name` field for parameters.
3. **Check Structure**: Ensure `apiPlaygroundInputs` object structure aligns with configuration (headers vs query).

### Navigation Missing Operations
**Symptoms**: Endpoints defined in OpenAPI spec do not appear in sidebar.
**Steps**:
1. **Check Visibility**: Look for `x-hidden: true` flags in the OpenAPI spec.
2. **Verify Strategy**: If *any* endpoint is manually added to `navigation` in `docs.json`, auto-generation stops. You must list *all* endpoints manually.

### Custom Styling Breaks
**Symptoms**: CSS overrides no longer apply after a platform update.
**Steps**:
1. **Inspect Elements**: Use browser dev tools to check if selector class names or IDs have changed.
2. **Recalibrate**: Update CSS selectors to match new platform structure.
3. **Review**: consider if a supported customization option is now available.

## Workarounds for Platform Limitations

### 1. CORS Configuration for API Playground
**Context**: Direct browser requests from the API playground.
**Action**: Configure CORS on your API server to allow requests from your Mintlify documentation domain.

### 2. Custom UI Element Targeting (High Maintenance)
**Context**: Deep UI customization is required beyond standard theme options.
**Action**:
1. Use browser inspection to find platform identifiers.
2. Apply custom CSS against these selectors.
3. **Warning**: Accept maintenance debt; these selectors are not guaranteed to be stable.

### 3. File/Operation Conflict Resolution
**Context**: An MDX file conflicts with an OpenAPI operation path.
**Action**: Use `x-mint` extension in OpenAPI spec to redirect the operation.
```yaml
x-mint:
  href: /custom-path
```

