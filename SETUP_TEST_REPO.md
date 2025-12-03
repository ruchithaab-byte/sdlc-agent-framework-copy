# Setup Test Repository Guide

## Option 1: Create Separate Git Repository

### Step 1: Create New Repository on GitHub

1. Go to GitHub
2. Create new repository: `sdlc-agent-framework-test`
3. Don't initialize with README (we'll push existing code)

### Step 2: Clone Current Framework to New Location

```bash
# Go to parent directory
cd /Users/macbook/agentic-coding-framework

# Create a copy
cp -r sdlc-agent-framework sdlc-agent-framework-test

# Initialize as new repo
cd sdlc-agent-framework-test
rm -rf .git
git init
git remote add origin https://github.com/YOUR-ORG/sdlc-agent-framework-test.git
git add .
git commit -m "Initial commit: No Vibes Allowed implementation"
git push -u origin main
```

### Step 3: Register in repo_registry.yaml

Add to your ORIGINAL framework's `config/repo_registry.yaml`:

```yaml
repositories:
  # ... existing repos ...
  
  - id: sdlc-agent-framework-test
    description: "Test environment for SDLC Agent Framework with No Vibes architecture"
    github_url: https://github.com/YOUR-ORG/sdlc-agent-framework-test
    local_path: ../sdlc-agent-framework-test
    branch: main
    enable_code_execution: true  # Enable for testing
```

### Step 4: Test Against the Copy

```python
# In test_real_sdlc_with_tracing.py or new test script
target_repo = "sdlc-agent-framework-test"  # Points to test copy
```

---

## Option 2: Use Existing Sandbox Repo

You already have `repos/sandbox` - you could copy the framework there:

```bash
cd /Users/macbook/agentic-coding-framework/sdlc-agent-framework

# Copy framework code to sandbox
cp -r src/* repos/sandbox/src/
cp -r tests repos/sandbox/
cp requirements.txt repos/sandbox/

# Update registry
# (sandbox already exists in repo_registry.yaml, just enable code execution)
```

---

## Option 3: Create Test Branch (Safest)

Keep everything in one repo but use a test branch:

```bash
cd /Users/macbook/agentic-coding-framework/sdlc-agent-framework

# Create test branch
git checkout -b test/rpi-verification

# All your changes are here already
# Run agents against this branch
```

Then in repo_registry.yaml:

```yaml
- id: sdlc-agent-framework-test-branch
  description: "Test branch for RPI verification"
  github_url: https://github.com/YOUR-ORG/sdlc-agent-framework
  local_path: .
  branch: test/rpi-verification  # Test branch
  enable_code_execution: true
```

---

## Recommendation

**Option 3 (Test Branch)** is the safest because:
- ✅ No duplication
- ✅ Git history preserved
- ✅ Easy to merge back to main when verified
- ✅ Can run agents against test branch

**Would you like me to help you set up Option 3, or do you prefer Option 1 (separate repo)?**

