# Team Setup Guide - User Email Capture

This guide explains different approaches for team members to set their individual emails when sharing IDE accounts.

## Option 1: Local Config File (Recommended for Individual Developers)

Each team member creates their own config file on their local machine:

```bash
# Team Member A
echo "alice@company.com" > ~/.agent_user_email

# Team Member B (on their own machine)
echo "bob@company.com" > ~/.agent_user_email
```

**Pros:**
- ✅ Persistent - set once, works for all runs
- ✅ Personal - each developer manages their own
- ✅ Simple - no need to remember to set it each time

**Cons:**
- ❌ Each team member needs to set it up
- ❌ Not suitable for shared machines

**Best for:** Individual developers working on their own machines

---

## Option 2: Environment Variable in Shell Profile (Recommended for Shared Machines)

Each team member adds their email to their shell profile (`.zshrc`, `.bashrc`, etc.):

```bash
# Add to ~/.zshrc or ~/.bashrc
export AGENT_USER_EMAIL="alice@company.com"
```

Then reload the shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

**Pros:**
- ✅ Works on shared machines (each user has their own shell profile)
- ✅ Persistent per user session
- ✅ Can be version controlled in dotfiles

**Cons:**
- ❌ Each team member needs to configure their shell
- ❌ Requires shell reload if changed

**Best for:** Shared development machines where each user has their own account

---

## Option 3: CLI Parameter (Recommended for Ad-hoc Runs)

Each team member specifies their email per run:

```bash
# Team Member A
python main.py agent codecraft --user-email alice@company.com

# Team Member B
python main.py agent archguard --user-email bob@company.com
```

**Pros:**
- ✅ No setup required
- ✅ Works immediately
- ✅ Can use different emails for different runs

**Cons:**
- ❌ Must remember to add it each time
- ❌ Easy to forget

**Best for:** Occasional use or when you need different emails per run

---

## Option 4: Shell Alias/Wrapper Script (Recommended for Teams)

Create a wrapper script or shell alias that automatically includes the email:

### Option 4a: Shell Alias

```bash
# Add to ~/.zshrc or ~/.bashrc
alias agent-run='python main.py agent --user-email $(whoami)@company.com'

# Usage
agent-run codecraft
```

### Option 4b: Wrapper Script

Create `~/bin/agent`:
```bash
#!/bin/bash
# Get email from config, env, or construct from username
EMAIL="${AGENT_USER_EMAIL:-$(cat ~/.agent_user_email 2>/dev/null || echo "$(whoami)@company.com")}"
python main.py agent "$@" --user-email "$EMAIL"
```

Make it executable:
```bash
chmod +x ~/bin/agent
```

Usage:
```bash
agent codecraft --task-type backend
```

**Pros:**
- ✅ Automatic - no need to remember
- ✅ Can be shared across team
- ✅ Flexible - can use config, env, or username

**Cons:**
- ❌ Requires initial setup
- ❌ Team needs to agree on approach

**Best for:** Teams that want a standardized approach

---

## Option 5: Project-Level Configuration (For Git Repos)

If the project is in a Git repository, you can use Git config:

```bash
# Set per-repository
git config user.email "alice@company.com"

# Or set globally
git config --global user.email "alice@company.com"
```

Then modify the system to read from Git config (would require code changes).

---

## Recommended Team Workflow

### For Individual Developers (Own Machines)
**Use:** Config file (`~/.agent_user_email`)
```bash
echo "your.email@company.com" > ~/.agent_user_email
```

### For Shared Machines (Each User Has Own Account)
**Use:** Environment variable in shell profile
```bash
# Add to ~/.zshrc
export AGENT_USER_EMAIL="your.email@company.com"
```

### For Shared Machines (Same User Account)
**Use:** CLI parameter per run
```bash
python main.py agent codecraft --user-email your.email@company.com
```

### For CI/CD or Automation
**Use:** Environment variable in CI config
```yaml
# GitHub Actions example
env:
  AGENT_USER_EMAIL: ci-bot@company.com
```

---

## Quick Setup Script for Teams

You can create a setup script that team members run once:

```bash
#!/bin/bash
# setup_agent_email.sh

read -p "Enter your email for agent executions: " email

# Validate email format
if [[ ! $email =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "Invalid email format"
    exit 1
fi

# Create config file
echo "$email" > ~/.agent_user_email
echo "✓ Email configured: $email"
echo "✓ All agent runs will use this email (unless overridden)"
```

---

## Verification

After setup, verify your email is configured:

```bash
# Check config file
cat ~/.agent_user_email

# Or test with Python
python3 -c "from src.utils.user_utils import get_user_email_from_env; print(get_user_email_from_env())"
```

---

## Summary

| Method | Setup Required | Persistence | Best For |
|--------|---------------|-------------|----------|
| Config File | Once per machine | ✅ Persistent | Individual developers |
| Shell Profile | Once per user | ✅ Persistent | Shared machines (per user) |
| CLI Parameter | None | ❌ Per run | Ad-hoc or shared accounts |
| Wrapper Script | Once per team | ✅ Persistent | Standardized team approach |

**Recommendation:** Use config file for individual developers, CLI parameter for shared accounts, and shell profile for shared machines with separate user accounts.

