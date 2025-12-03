---
name: your-skill-name-here
description: Highly specific, action-oriented description of what this skill does and when to use it. Maximum 1024 characters. This description is critical for skill discovery - it must clearly communicate the functional outcome and specific scenarios for use. Example: "Generates user-facing changelogs by analyzing Git commit history and transforming technical commits into customer-friendly release notes."
version: 1.0.0
dependencies:
  - python>=3.9
  - package-name>=1.0.0
---

# Skill Name (Human-Readable Title)

## Overview

Brief, concise description of what this skill does. Write as if for an intelligent colleague - assume the agent already understands the domain concepts. Focus only on what makes this skill unique or the specific procedural knowledge it provides.

## When to Use

Clear, specific scenarios when this skill should be invoked. Be explicit about:
- The type of task or problem it solves
- The input format or context required
- The expected output or outcome

**Example**: Use this skill when you need to transform technical commit messages into customer-facing release notes, or when generating changelogs from Git history for external publication.

## Prerequisites

List any requirements that must be met before using this skill:
- Required environment setup
- Necessary files or data structures
- Access permissions or configurations

## Execution Steps

### Step 1: [Action Name]

Clear, actionable instruction. Be concise - provide only the essential steps the agent wouldn't inherently know.

```python
# scripts/your_script.py
# Deterministic operations that require precise execution
# Use code blocks for scripts that need exact implementation

import required_library

def execute_operation(input_data):
    # Implementation details
    return result
```

**Instructions**: 
- How to run the script
- What parameters to pass
- Expected output format

### Step 2: [Next Action]

Continue with clear, sequential steps. Each step should be:
- Actionable (verb-based)
- Specific (no ambiguity)
- Concise (no unnecessary explanation)

## Transformation Rules

If the skill involves data transformation, provide clear rules:

1. **Rule Category 1**: Specific transformation logic
   - Sub-rule or example
   - Edge case handling

2. **Rule Category 2**: Another transformation pattern
   - When to apply
   - Expected output format

## Examples

### Example 1: [Use Case Name]

**Input Prompt**: "Generate release notes for the current branch."

**Expected Output**: 
```markdown
# Release Notes

## Features
- Customer-friendly feature description

## Improvements
- Customer-friendly improvement description
```

**Processing Steps**:
1. Extract commits from Git history
2. Categorize by type (Features, Improvements, Bug Fixes)
3. Transform technical language to customer-friendly language
4. Format according to corporate standards

### Example 2: [Another Use Case]

**Input**: [Description of input]

**Output**: [Description of output]

**Key Steps**: [Brief summary]

## Error Handling

Guidelines for handling common errors:

- **Error Type 1**: Description and resolution approach
- **Error Type 2**: Description and resolution approach
- **Fallback Strategy**: What to do if primary approach fails

## Security and Guidelines

**CRITICAL**: Never hardcode sensitive information:
- ❌ No API keys, passwords, or tokens in code
- ❌ No credentials in SKILL.md or scripts
- ✅ Use external credential management systems
- ✅ Route sensitive operations through secure channels

**Operational Constraints**:
- Read-only operations (if applicable)
- Resource limits or quotas
- Rate limiting considerations

## Dependencies

This skill requires the following packages (listed in frontmatter):
- `package-name>=1.0.0`: Purpose of dependency
- `another-package>=2.0.0`: Another purpose

**Note**: For API-based deployments, all dependencies must be pre-installed in the execution environment. The skill cannot install packages at runtime.

## Performance Considerations

- Optimization strategies for large datasets
- Token usage recommendations
- Caching or memoization approaches

## Related Resources

For extensive reference materials, see:
- `resources/REFERENCE.md`: Detailed documentation
- `resources/EXAMPLES.md`: Additional examples
- `templates/`: Reusable templates

## Notes

- Additional implementation details
- Platform-specific considerations (if any)
- Limitations or known issues
- Future enhancements

