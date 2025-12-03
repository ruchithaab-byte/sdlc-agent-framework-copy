# Agent Skill Development Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Architectural Foundation](#architectural-foundation)
3. [Directory Structure](#directory-structure)
4. [SKILL.md Structure](#skillmd-structure)
5. [Naming Conventions](#naming-conventions)
6. [Authoring Best Practices](#authoring-best-practices)
7. [Discovery and Progressive Disclosure](#discovery-and-progressive-disclosure)
8. [Architectural Boundaries](#architectural-boundaries)
9. [Security and Auditing](#security-and-auditing)
10. [Testing and Validation](#testing-and-validation)
11. [Deployment Workflow](#deployment-workflow)
12. [Advanced Patterns](#advanced-patterns)

---

## Introduction

Agent Skills represent a critical architectural component for transforming general-purpose agents into domain specialists. Skills provide persistent, reusable procedural knowledge that agents can dynamically load and apply to specific tasks.

This guide provides comprehensive instructions for creating production-ready Agent Skills based on established architectural principles and best practices.

---

## Architectural Foundation

### What Are Agent Skills?

Agent Skills are filesystem-based mechanisms that provide:
- **Procedural Knowledge**: The "how-to" guidance, specialized workflows, and best practices
- **Reusability**: Persistent resources that are automatically loaded across conversations
- **Modularity**: Small, focused capabilities that can be composed together
- **Domain Specialization**: Transform general agents into specialists for specific tasks

### Execution Environment

Skills operate within an agent's execution environment (sandbox/VM) that provides:
- Filesystem access for reading and writing files
- Code execution capabilities for deterministic operations
- Resource management within defined constraints

### Key Architectural Principles

1. **Progressive Disclosure**: Only essential metadata is loaded initially; full content loads when relevant
2. **Token Efficiency**: Every token must justify its inclusion in the context window
3. **Microservice Modularity**: Many small, specialized skills rather than monolithic ones
4. **Composability**: Skills can be automatically chained together by the agent

---

## Directory Structure

### Canonical Layout

Every Agent Skill must be housed within a dedicated directory whose name precisely matches the skill's internal identifier:

```
your-skill-name/
├── SKILL.md                    # Required: Core skill definition
├── scripts/                    # Optional: Executable code files
│   └── your_script.py
├── templates/                  # Optional: Reusable document structures
│   └── template.md
└── resources/                  # Optional: Extensive reference materials
    └── REFERENCE.md
```

### Required Components

- **SKILL.md**: The core resource defining the skill's function and instructions. This file is mandatory.

### Optional Subdirectories

- **scripts/**: Store executable code files (Python, Bash, etc.) for deterministic operations
- **templates/**: Contain reusable document structures or code snippets
- **resources/**: Store extensive supplemental materials (e.g., legal documents, brand guidelines) that are too large for SKILL.md

### Packaging for Deployment

When preparing a skill for deployment via upload:
1. Compress the skill folder into a ZIP archive
2. **Critical**: The skill folder itself must reside at the root level of the ZIP file
3. Do not nest the skill folder within arbitrary subfolders

**Correct Structure**:
```
skill-archive.zip
└── your-skill-name/
    ├── SKILL.md
    └── scripts/
```

**Incorrect Structure**:
```
skill-archive.zip
└── some-folder/
    └── your-skill-name/
        ├── SKILL.md
        └── scripts/
```

---

## SKILL.md Structure

### YAML Frontmatter

The SKILL.md file must begin with a YAML frontmatter block containing metadata critical for skill discovery.

#### Required Fields

**name** (Discovery Identifier)
- Maximum length: 64 characters
- Format: lowercase letters, numbers, and hyphens only
- Prohibited: XML tags, reserved terms (platform-specific restrictions may apply)
- Purpose: Unique identifier for the skill
- Example: `document-changelog-generator`

**description** (Critical Discovery Mechanism)
- Maximum length: 1024 characters
- Purpose: Primary textual input the agent uses to decide whether to invoke the skill
- Requirements:
  - Highly specific and action-oriented
  - Clearly states what the skill does
  - Explicitly states when to use it
  - Describes the functional outcome
- Example: "Generates user-facing changelogs by analyzing Git commit history and transforming technical commits into customer-friendly release notes. Use this skill when a human-readable release summary is needed from a technical repository."

#### Optional Fields

**version**
- Format: Semantic versioning (e.g., `1.0.0`)
- Purpose: Track iterations and changes for troubleshooting and quality assurance

**dependencies**
- Format: List of required software packages
- Example:
  ```yaml
  dependencies:
    - python>=3.9
    - pandas>=1.5.0
    - gitpython>=3.1.41
  ```
- **Critical Note**: For API-based deployments, all dependencies must be pre-installed in the execution environment. Skills cannot install packages at runtime.

### Markdown Body

The body of SKILL.md contains the actual instructions and procedural knowledge. Follow these principles:

1. **Token Efficiency**: Every token must justify its inclusion
2. **Conciseness**: Write for an intelligent colleague, not a beginner
3. **Actionability**: Provide clear, step-by-step instructions
4. **Externalization**: Move extensive materials to `resources/` directory

---

## Naming Conventions

### Skill Directory and Identifier

- **Format**: Lowercase letters, numbers, and hyphens only
- **Pattern**: Gerund form (verb + -ing) is recommended
- **Examples**: 
  - ✅ `processing-pdfs`
  - ✅ `testing-code`
  - ✅ `analyzing-spreadsheets`
  - ✅ `generating-changelogs`

### Avoid Generic Names

Generic or vague naming conventions inhibit skill discovery:
- ❌ `helper`
- ❌ `utils`
- ❌ `tools`
- ❌ `files`

These names are too broad and prevent the agent from confidently selecting the appropriate skill.

### Consistency Requirements

- Skill folder name must exactly match the `name` field in YAML frontmatter
- Use consistent naming patterns across related skills
- Follow organizational naming conventions if they exist

---

## Authoring Best Practices

### Token-Efficient Instruction Writing

The entire SKILL.md file is loaded into the context window when the skill is invoked, competing with conversation history and system prompts. This necessitates ruthless conciseness.

#### Principles

1. **Assume Intelligence**: The agent is already very smart. Only provide:
   - Organizational workflows it wouldn't know
   - Specific tool usage methods
   - Domain-specific procedural steps

2. **Immediate Actionability**: Present necessary code immediately rather than explaining concepts:
   ```python
   # ✅ Good: Immediate code
   import pdfplumber
   with pdfplumber.open(file_path) as pdf:
       text = pdf.pages[0].extract_text()
   
   # ❌ Bad: Verbose explanation
   # A PDF file is a Portable Document Format file that contains...
   # To extract text, you need to use a library called pdfplumber...
   ```

3. **Externalize Large Content**: Move extensive materials to `resources/`:
   - 50-page brand guidelines → `resources/BRAND_GUIDELINES.md`
   - Extensive API documentation → `resources/API_REFERENCE.md`
   - Large example sets → `resources/EXAMPLES.md`

### Script Integration

Use executable scripts for deterministic operations that require precision:

```python
# scripts/analyze_git.py
import git
import json
from datetime import datetime

def analyze_commits(repo_path, limit=100):
    repo = git.Repo(repo_path)
    commits = repo.iter_commits('main', max_count=limit)
    
    commit_data = []
    for commit in commits:
        commit_data.append({
            'hash': commit.hexsha,
            'message': commit.message,
            'date': commit.committed_datetime.isoformat()
        })
    
    return json.dumps(commit_data)
```

**Guidelines**:
- Embed scripts in code blocks within SKILL.md
- Reference scripts in `scripts/` directory when appropriate
- Provide clear instructions on how to execute
- Document expected inputs and outputs

### Writing Style

- **Clarity**: Use clear, direct language
- **Brevity**: Eliminate unnecessary words
- **Structure**: Use headings, lists, and code blocks for scannability
- **Examples**: Include concrete examples over abstract descriptions

---

## Discovery and Progressive Disclosure

### How Skill Discovery Works

Skill discovery relies entirely on the agent's reasoning process based on textual descriptions. There is no algorithmic skill selection or external intent detection layer.

**Discovery Flow**:
1. **Initial Load**: Only skill metadata (name and description) is pre-loaded
2. **Relevance Assessment**: Agent's reasoning engine evaluates description against user query
3. **Full Load**: If relevant, entire SKILL.md is loaded into context
4. **Invocation**: Agent applies skill instructions to complete the task

### Optimizing for Discovery

The `description` field is the primary driver of skill discovery. Its quality directly correlates with invocation reliability.

#### Effective Description Patterns

**✅ High Efficacy**:
```
"Generates user-facing changelogs by analyzing Git commit history and 
transforming technical commits into customer-friendly release notes. 
Use this skill when a human-readable release summary is needed from 
a technical repository."
```

**❌ Low Efficacy**:
```
"Tool for code."
```

#### Description Best Practices

1. **Be Specific**: Clearly state what the skill does
2. **State Use Cases**: Explicitly describe when to use it
3. **Describe Outcome**: Explain the functional result
4. **Action-Oriented**: Use active voice and action verbs
5. **Include Context**: Mention required inputs or conditions

### Progressive Disclosure Benefits

- **Token Efficiency**: Only relevant skills consume context tokens
- **Cost Optimization**: Reduces unnecessary token usage
- **Performance**: Faster initial context loading
- **Scalability**: Supports large skill ecosystems

---

## Architectural Boundaries

Understanding the boundaries between Skills, External Connectivity, and Prompts is critical for effective agent architecture.

### Skills vs External Connectivity

**Agent Skills** provide:
- Procedural knowledge (how-to, workflows, best practices)
- Domain-specific logic and transformations
- Reusable instruction sets

**External Connectivity** (MCP Servers, APIs) provides:
- Data access and system connections
- Real-time information retrieval
- Authenticated access to external systems

**Relationship**: High-performance agents typically employ both:
- External Connectivity handles "access the database" or "call the Slack API"
- Skills dictate "how to process that data" or "format reports using corporate formulas"

### Skills vs Prompts

**Skills** are:
- Persistent and reusable across conversations
- Automatically loaded when relevant
- Designed for specific, repeatable tasks
- Filesystem-based resources

**Prompts** are:
- Ephemeral, one-off instructions
- Context for immediate tasks
- General agent personality or role definition
- Conversation-based

### Design Philosophy: Microservice Modularity

Instead of monolithic skills, create numerous small, highly specialized skills:
- `git-analyzer`: Analyzes Git repositories
- `internal-comms`: Handles internal communication patterns
- `theme-factory`: Generates UI themes

The agent can automatically chain and compose multiple specialized skills together, providing robustness and flexibility without explicit orchestration.

---

## Security and Auditing

### Credential Management

**CRITICAL**: Never hardcode sensitive information in skills.

**Prohibited**:
- ❌ API keys in SKILL.md or scripts
- ❌ Passwords or tokens in code
- ❌ Private credentials in any skill file

**Required**:
- ✅ Use external credential management systems
- ✅ Route sensitive operations through secure channels
- ✅ Use environment variables or secure vaults
- ✅ Leverage External Connectivity (MCP) for authenticated access

### Third-Party Auditing

Before enabling skills from non-trusted sources, perform thorough auditing:

1. **Code Review**: Inspect all bundled files and scripts
2. **Dependency Analysis**: Review all code dependencies
3. **Network Assessment**: Check for external network connections
4. **Instruction Review**: Assess instructions for security implications

### Sandbox Considerations

Skills execute within a sandbox environment. Consider:
- File system access limitations
- Network access restrictions
- Resource quotas and timeouts
- Isolation from other processes

### Error Handling

Include robust error handling guidelines:
- Graceful degradation strategies
- Clear error messages
- Fallback approaches
- Prerequisites documentation

---

## Testing and Validation

### Pre-Deployment Validation

Before deploying a skill:

1. **Syntax Review**: Verify YAML frontmatter is valid
2. **Description Quality**: Ensure description accurately reflects usage scenarios
3. **File Verification**: Confirm all referenced files exist
4. **Dependency Check**: Verify all dependencies are listed
5. **Instruction Clarity**: Review instructions for clarity and completeness
6. **Example Testing**: Test examples with representative data

### Post-Deployment Validation

After deploying a skill:

1. **Enable Skill**: Activate the skill in the agent environment
2. **Diverse Testing**: Test with various prompts intended to trigger the skill
3. **Reasoning Trace Review**: Review agent's internal logic to confirm:
   - Correct invocation timing
   - Proper execution flow
   - Appropriate skill selection
4. **Iteration**: If invocation is inconsistent, refine the description

### Model Compatibility Testing

Skills should be tested against different model capability tiers:

**High Capability Models**:
- Require minimal instructional detail
- Can infer context from brief guidance
- Prioritize avoiding over-explanation

**Medium Capability Models**:
- Serve as baseline target for standard instructions
- Balance of cost and capability
- Require clear, structured guidance

**Low Capability Models**:
- May require more explicit, detailed guidance
- Need step-by-step instructions
- Benefit from comprehensive examples

**Testing Protocol**:
1. Test with high capability model (validate minimal instructions)
2. Test with medium capability model (baseline validation)
3. Test with low capability model (ensure sufficient detail)
4. Iterate instructions to balance across tiers

---

## Deployment Workflow

### Seven-Stage Process

#### Stage 1: Concept to Structure

1. Identify a specific, repeatable task requiring specialized procedural knowledge
2. Create the dedicated skill folder
3. Ensure directory name adheres to naming conventions (lowercase, hyphenated)

#### Stage 2: Metadata Definition

1. Create `SKILL.md` file
2. Populate YAML frontmatter:
   - Define `name` (max 64 chars, lowercase-hyphenated)
   - Craft `description` (max 1024 chars, highly specific and action-oriented)
   - Specify `dependencies` if needed
   - Add `version` for tracking

#### Stage 3: Instruction Authoring

1. Write detailed instructions in Markdown body
2. Ensure conciseness by moving extensive resources to `resources/` folder
3. Embed necessary Python or Bash scripts using code blocks
4. Include clear examples and use cases

#### Stage 4: Local Testing and Validation

1. Test instructions and scripts with representative input data
2. Validate outside the agent environment to ensure:
   - Underlying code is functional
   - Output format is correct
   - Error handling works as expected

#### Stage 5: Packaging

1. Compress the skill folder into a ZIP file
2. **Verify**: Skill folder is the sole item at the root of the archive
3. **Avoid**: Nested directories that prevent deployment

#### Stage 6: Deployment

1. Upload the ZIP file via the agent platform's API or administrative settings
2. For API deployment: Ensure the agent's execution environment is pre-configured with all listed dependencies
3. Enable the skill in the agent environment

#### Stage 7: Live Validation and Iteration

1. Execute a wide range of prompts intended to trigger the skill
2. Review agent's internal logic trace to confirm:
   - Skill is being discovered correctly
   - Invocation timing is appropriate
   - Execution flow is correct
3. If invocation reliability is low, iterate on the `description` field
4. Refine until the agent consistently selects the skill when relevant

---

## Advanced Patterns

### Complex File Handling

Skills can handle proprietary binary formats by combining deterministic code with procedural instructions:

**Example Pattern**:
- Use libraries like `pdfplumber` for PDF operations
- Extract text, tables, and metadata
- Create, merge, and split documents
- Handle complex forms

### Business Automation

Skills can automate business processes:

**Example Patterns**:
- **Invoice Organizer**: Read financial files, extract data, rename according to archival policy
- **Domain Name Brainstormer**: Generate naming ideas, check availability across TLDs
- **Report Generator**: Transform data into formatted reports using corporate templates

### Meta-Skill Pattern

Create skills that manage or improve the agent environment itself:

**Example**: A `skill-creator` skill that standardizes the creation of new enterprise-specific skills internally.

### Skill Composition

Skills can be automatically chained together:
- Skill A processes input data
- Skill B transforms the output
- Skill C formats the final result

The agent's reasoning engine handles composition automatically without explicit orchestration.

---

## Conclusion

Effective Agent Skill development requires:
1. **Clear Architecture**: Understanding boundaries between Skills, External Connectivity, and Prompts
2. **Optimized Discovery**: Crafting highly specific, action-oriented descriptions
3. **Token Efficiency**: Writing concise, actionable instructions
4. **Security First**: Never hardcoding credentials, always auditing third-party skills
5. **Rigorous Testing**: Validating across model capability tiers and use cases
6. **Iterative Refinement**: Continuously improving based on invocation patterns

By following this guide, you can create production-ready Agent Skills that reliably extend agent capabilities with specialized procedural knowledge.

