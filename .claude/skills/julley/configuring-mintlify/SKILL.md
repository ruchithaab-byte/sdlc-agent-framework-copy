---
name: configuring-mintlify
description: Implements and configures Mintlify documentation sites. Use when setting up new Mintlify sites, troubleshooting configuration errors, configuring OpenAPI/API reference pages, or implementing personalization. Includes guidance on avoiding anti-patterns and applying workarounds.
version: 1.0.0
dependencies: []
---

# Mintlify Documentation Implementation

## Overview

Mintlify is a managed documentation platform. This skill provides procedural knowledge for configuring Mintlify sites, integrating API references, and implementing personalization while avoiding common configuration failures.

## When to Use

- Setting up a new Mintlify documentation site
- Configuring OpenAPI/API reference pages
- Troubleshooting blank API pages or configuration errors
- Implementing personalization or authentication features
- Setting up CI/CD workflows for documentation

## Prerequisites

- Mintlify account and repository access
- OpenAPI 3.x specification (strictly required for API docs)
- Node.js environment for local development (`mint dev`)

## Execution Steps

### Step 1: Core Configuration (docs.json)

The `docs.json` file is the blueprint for site configuration.

**Template**: See `templates/docs.json.template`

**Critical Practices**:
- Always include `$schema` reference.
- Select theme strategically: `maple` (modern), `aspen` (complex nav), `palm` (fintech), `linden` (retro).

### Step 2: API Reference Configuration

Mintlify requires strict OpenAPI 3.x compliance.

**Template**: See `templates/openapi-frontmatter.template`

**Critical Requirements**:
- **OpenAPI 3.x only**: OpenAPI 2.0 results in blank pages.
- **Exact matching**: Frontmatter path must match OpenAPI spec character-for-character (including trailing slashes).
- **Uppercase Methods**: `GET`, `POST`, `PUT`, `DELETE`.

**Navigation Strategies**:
- **Automatic**: Let Mintlify generate all operations.
- **Manual**: Explicitly list every operation.
- **Mixed**: NOT SUPPORTED. Manual inclusion of one endpoint disables auto-generation for the whole spec.

### Step 3: Avoid Common Anti-Patterns

Common configuration mistakes can cause blank pages or broken navigation.

**Key Anti-Patterns**:
1.  **OpenAPI 2.0 Usage**: Must convert to 3.x.
2.  **Path Mismatch**: `/users` != `/users/`.
3.  **Case Sensitivity**: `get` != `GET`.
4.  **Partial Inclusion**: Don't mix auto and manual navigation.

> **Detailed Guide**: See `resources/ANTI_PATTERNS.md` for a complete list of pitfalls and resolutions.

### Step 4: Personalization Setup

**Template**: See `templates/personalization-config.template`

**Configuration**:
- User data must include `apiPlaygroundInputs`.
- Field names must **exactly match** the API playground configuration (case-sensitive).

### Step 5: Customization & Components

**Template**: See `templates/custom-component.template` for React component structure.

**Styling**:
- **Tailwind**: Supported (v3 utilities).
- **Custom CSS**: Add CSS files to repo.
- **Deep Customization**: Can target platform selectors, but this is high-risk (see Troubleshooting).

### Step 6: CI/CD Integration

- **Trunk-Based**: Small, frequent commits.
- **Preview Deployments**: Use as QA gates before merging.

## Troubleshooting

If you encounter blank pages, API connection failures, or styling issues, refer to the troubleshooting guide.

> **Guide**: See `resources/TROUBLESHOOTING.md` for solutions to common errors and known workarounds.

## File Reference

- **`templates/`**:
    - `docs.json.template`: Base site configuration.
    - `openapi-frontmatter.template`: Header for API pages.
    - `personalization-config.template`: JSON structure for auth prefilling.
    - `custom-component.template`: React component pattern with optimization.
- **`resources/`**:
    - `ANTI_PATTERNS.md`: detailed list of configuration mistakes to avoid.
    - `TROUBLESHOOTING.md`: Error resolution and workarounds.
