# Agent Skill Quick Start Guide

A quick reference guide for creating Agent Skills efficiently.

---

## Quick Checklist

### Pre-Creation
- [ ] Identified specific, repeatable task requiring specialized knowledge
- [ ] Determined skill name (lowercase, hyphenated, gerund form recommended)
- [ ] Defined clear use cases and expected outcomes

### Structure
- [ ] Created skill directory with correct naming (matches skill identifier)
- [ ] Created `SKILL.md` file with YAML frontmatter
- [ ] Added optional subdirectories if needed (`scripts/`, `templates/`, `resources/`)

### YAML Frontmatter
- [ ] `name`: Max 64 chars, lowercase-hyphenated, no reserved terms
- [ ] `description`: Max 1024 chars, highly specific and action-oriented
- [ ] `version`: Semantic versioning (optional)
- [ ] `dependencies`: List of required packages (optional)

### Content
- [ ] Instructions are concise and token-efficient
- [ ] Large resources moved to `resources/` directory
- [ ] Scripts embedded in code blocks or referenced in `scripts/`
- [ ] Examples included with clear input/output
- [ ] Security guidelines included (no hardcoded credentials)

### Testing
- [ ] Tested locally with representative data
- [ ] Validated YAML syntax
- [ ] Verified all referenced files exist
- [ ] Tested across model capability tiers (if applicable)

### Deployment
- [ ] Packaged as ZIP with skill folder at root level
- [ ] Dependencies pre-installed in execution environment (for API deployment)
- [ ] Enabled skill in agent environment
- [ ] Tested with diverse prompts
- [ ] Reviewed invocation patterns and refined description if needed

---

## Step-by-Step Creation Workflow

### 1. Define the Skill

**Identify the Task**:
- What specific, repeatable task does this skill handle?
- What procedural knowledge does it provide?
- When should the agent use this skill?

**Example**: "Generate customer-facing changelogs from Git commit history"

### 2. Choose the Name

**Requirements**:
- Lowercase letters, numbers, and hyphens only
- Maximum 64 characters
- Gerund form recommended (verb + -ing)
- Avoid generic terms (helper, utils, tools)

**Example**: `generating-changelogs`

### 3. Create Directory Structure

```bash
mkdir generating-changelogs
cd generating-changelogs
mkdir scripts templates resources  # Optional subdirectories
touch SKILL.md
```

### 4. Write YAML Frontmatter

```yaml
---
name: generating-changelogs
description: Generates user-facing changelogs by analyzing Git commit history and transforming technical commits into customer-friendly release notes. Use this skill when a human-readable release summary is needed from a technical repository.
version: 1.0.0
dependencies:
  - python>=3.9
  - gitpython>=3.1.41
---
```

**Critical**: The `description` field is the primary discovery mechanism. Make it:
- Highly specific
- Action-oriented
- Explicit about use cases
- Clear about functional outcome

### 5. Write Instructions

**Principles**:
- Write for an intelligent colleague (assume the agent is smart)
- Be concise and actionable
- Provide only domain-specific knowledge
- Include immediate code examples

**Structure**:
1. Overview (brief)
2. When to Use (specific scenarios)
3. Prerequisites (if any)
4. Execution Steps (clear, sequential)
5. Examples (concrete input/output)
6. Error Handling (common issues)
7. Security Guidelines (no credentials)

### 6. Add Scripts (If Needed)

For deterministic operations, embed scripts:

```python
# scripts/analyze_git.py
import git
import json

def analyze_commits(repo_path, limit=100):
    # Implementation
    return result
```

Reference in instructions with clear execution guidance.

### 7. Externalize Large Resources

Move extensive materials to `resources/`:
- Long reference documents → `resources/REFERENCE.md`
- Many examples → `resources/EXAMPLES.md`
- Large templates → `resources/TEMPLATES.md`

### 8. Test Locally

- Run scripts with test data
- Verify output format
- Check error handling
- Validate all file references

### 9. Package for Deployment

```bash
# From parent directory
zip -r generating-changelogs.zip generating-changelogs/
```

**Verify**: Skill folder is at root of ZIP, not nested.

### 10. Deploy and Validate

1. Upload ZIP to agent platform
2. Enable skill in agent environment
3. Test with diverse prompts
4. Review agent's reasoning trace
5. Iterate on description if invocation is inconsistent

---

## Common Pitfalls to Avoid

### ❌ Vague Description

**Bad**:
```yaml
description: Tool for code.
```

**Good**:
```yaml
description: Generates user-facing changelogs by analyzing Git commit history and transforming technical commits into customer-friendly release notes. Use this skill when a human-readable release summary is needed from a technical repository.
```

### ❌ Generic Naming

**Bad**: `helper`, `utils`, `tools`, `files`

**Good**: `processing-pdfs`, `analyzing-spreadsheets`, `generating-changelogs`

### ❌ Hardcoded Credentials

**Bad**:
```python
api_key = "sk-1234567890abcdef"
```

**Good**: Use environment variables or external credential management

### ❌ Over-Explaining Basics

**Bad**:
```markdown
# What is a PDF?
A PDF is a Portable Document Format file...
```

**Good**:
```markdown
# PDF Processing
```python
import pdfplumber
with pdfplumber.open(file_path) as pdf:
    text = pdf.pages[0].extract_text()
```

### ❌ Large Content in SKILL.md

**Bad**: 50-page brand guidelines embedded in SKILL.md

**Good**: Reference `resources/BRAND_GUIDELINES.md` in SKILL.md

### ❌ Incorrect ZIP Structure

**Bad**:
```
archive.zip
└── some-folder/
    └── skill-name/
        └── SKILL.md
```

**Good**:
```
archive.zip
└── skill-name/
    └── SKILL.md
```

### ❌ Missing Dependencies

**Bad**: Script uses `pandas` but not listed in dependencies

**Good**: All required packages listed in YAML frontmatter

### ❌ Platform-Specific Assumptions

**Bad**: Assuming specific platform features or APIs

**Good**: Platform-agnostic instructions that work across environments

---

## Validation Checklist

### Pre-Deployment

- [ ] **Syntax**: YAML frontmatter is valid
- [ ] **Naming**: Directory name matches `name` field exactly
- [ ] **Description**: Highly specific, action-oriented, max 1024 chars
- [ ] **Name Field**: Lowercase-hyphenated, max 64 chars, no reserved terms
- [ ] **Files**: All referenced files exist
- [ ] **Dependencies**: All required packages listed
- [ ] **Instructions**: Clear, concise, actionable
- [ ] **Examples**: Concrete input/output provided
- [ ] **Security**: No hardcoded credentials
- [ ] **Testing**: Tested locally with representative data

### Post-Deployment

- [ ] **Enabled**: Skill is active in agent environment
- [ ] **Discovery**: Agent can find skill with appropriate prompts
- [ ] **Invocation**: Skill is invoked when relevant
- [ ] **Execution**: Skill executes correctly
- [ ] **Output**: Output matches expected format
- [ ] **Error Handling**: Errors are handled gracefully
- [ ] **Iteration**: Description refined if invocation is inconsistent

### Model Compatibility

- [ ] **High Capability**: Tested with high capability model (minimal instructions work)
- [ ] **Medium Capability**: Tested with medium capability model (baseline)
- [ ] **Low Capability**: Tested with low capability model (sufficient detail)

---

## Description Writing Formula

Use this formula for effective descriptions:

```
[Action Verb] + [Specific Outcome] + [Method/Context] + [When to Use]
```

**Example**:
```
Generates user-facing changelogs by analyzing Git commit history and 
transforming technical commits into customer-friendly release notes. 
Use this skill when a human-readable release summary is needed from 
a technical repository.
```

**Breakdown**:
- **Action**: "Generates"
- **Outcome**: "user-facing changelogs"
- **Method**: "by analyzing Git commit history and transforming technical commits"
- **When**: "when a human-readable release summary is needed from a technical repository"

---

## Architectural Boundaries Quick Reference

### Skills vs External Connectivity

| Aspect | Skills | External Connectivity |
|--------|--------|----------------------|
| **Purpose** | Procedural knowledge (how-to) | Data access and connections |
| **Example** | "Format reports using corporate formulas" | "Access the database" |
| **Location** | Filesystem-based | External servers/APIs |

**Use Both**: External Connectivity gets data, Skills process it.

### Skills vs Prompts

| Aspect | Skills | Prompts |
|--------|--------|---------|
| **Persistence** | Reusable across conversations | One-off instructions |
| **Loading** | Automatically loaded when relevant | Conversation-based |
| **Purpose** | Specific, repeatable tasks | General role or immediate task |

---

## Directory Structure Template

```
your-skill-name/
├── SKILL.md                    # Required
├── scripts/                    # Optional
│   └── your_script.py
├── templates/                  # Optional
│   └── template.md
└── resources/                  # Optional
    └── REFERENCE.md
```

---

## YAML Frontmatter Template

```yaml
---
name: your-skill-name
description: Highly specific, action-oriented description (max 1024 chars). Clearly states what it does, how it works, and when to use it.
version: 1.0.0
dependencies:
  - python>=3.9
  - package-name>=1.0.0
---
```

---

## Key Principles Summary

1. **Discovery First**: Description quality determines skill success
2. **Token Efficiency**: Every token must justify inclusion
3. **Microservice Modularity**: Many small, specialized skills
4. **Security Always**: Never hardcode credentials
5. **Test Rigorously**: Validate across model tiers and use cases
6. **Iterate Continuously**: Refine based on invocation patterns

---

## Next Steps

1. Read `AGENT_SKILL_GUIDE.md` for comprehensive details
2. Use `AGENT_SKILL_TEMPLATE.md` as your starting point
3. Follow this quick start workflow
4. Validate using the checklists
5. Deploy and iterate based on results

---

## Quick Reference: Character Limits

- **name**: Maximum 64 characters
- **description**: Maximum 1024 characters
- **Format**: Lowercase letters, numbers, hyphens only
- **Naming**: Gerund form recommended (verb + -ing)

---

## Quick Reference: Required vs Optional

**Required**:
- Skill directory (matches name)
- `SKILL.md` file
- `name` field in YAML
- `description` field in YAML

**Optional**:
- `version` field
- `dependencies` field
- `scripts/` subdirectory
- `templates/` subdirectory
- `resources/` subdirectory

---

## Troubleshooting

### Skill Not Being Invoked

**Problem**: Agent doesn't select skill when it should

**Solutions**:
1. Refine `description` to be more specific and action-oriented
2. Add more explicit use case scenarios
3. Include keywords that match user queries
4. Review agent's reasoning trace to understand selection logic

### Skill Invoked Incorrectly

**Problem**: Agent selects skill when it shouldn't

**Solutions**:
1. Make `description` more specific about when NOT to use
2. Add prerequisites or constraints
3. Clarify the skill's scope and limitations

### Execution Errors

**Problem**: Skill fails during execution

**Solutions**:
1. Verify all dependencies are installed
2. Check file paths and references
3. Validate script syntax and logic
4. Review error handling guidelines
5. Test with representative data locally

### Token Usage Too High

**Problem**: Skill consumes too many context tokens

**Solutions**:
1. Move large content to `resources/` directory
2. Reduce verbosity in instructions
3. Remove redundant explanations
4. Use more concise language
5. Externalize examples to separate files

---

## Success Metrics

A well-designed skill should:
- ✅ Be discovered reliably when relevant
- ✅ Execute correctly with expected inputs
- ✅ Produce consistent, correct outputs
- ✅ Handle errors gracefully
- ✅ Be composable with other skills
- ✅ Maintain token efficiency
- ✅ Follow security best practices

---

**Remember**: The `description` field is your most powerful tool for skill discovery. Invest time in crafting a highly specific, action-oriented description that clearly communicates when and how to use the skill.

