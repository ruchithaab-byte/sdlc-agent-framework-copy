# User Email Capture for Shared IDE Accounts

This document explains how to capture individual user emails when team members share the same IDE account.

## Problem

When multiple team members use the same IDE account setup, all agent executions are logged under the same authenticated email. This makes it difficult to track individual contributions.

## Solution

The framework now supports multiple ways to specify individual user emails with a priority order:

### Priority Order

1. **CLI Parameter** (`--user-email`) - Highest priority
2. **Environment Variable** (`AGENT_USER_EMAIL`)
3. **Config File** (`~/.agent_user_email`)
4. **Authenticated Email** (from login token) - Fallback

## Usage Methods

### Method 1: CLI Parameter (Recommended for One-off Runs)

```bash
# Each team member specifies their email when running agents
python main.py agent codecraft --user-email john.doe@company.com
python main.py agent archguard --user-email jane.smith@company.com
```

### Method 2: Environment Variable (Recommended for Scripts)

```bash
# Set environment variable before running
export AGENT_USER_EMAIL="john.doe@company.com"
python main.py agent codecraft

# Or inline
AGENT_USER_EMAIL="jane.smith@company.com" python main.py agent archguard
```

### Method 3: Config File (Recommended for Persistent Setup)

Each team member creates their own config file:

```bash
# Create per-user config file
echo "john.doe@company.com" > ~/.agent_user_email

# Now all agent runs will use this email (unless overridden)
python main.py agent codecraft
```

### Method 4: Authenticated Email (Default)

If none of the above are set, the system uses the email from the authentication token:

```bash
# Login first
python main.py login --email team@company.com --password <password>

# Run agent (uses authenticated email)
python main.py agent codecraft
```

## Examples

### Example 1: Team Member A

```bash
# Set personal email in config file
echo "alice@company.com" > ~/.agent_user_email

# Run agent - will use alice@company.com
python main.py agent codecraft --task-type backend
```

### Example 2: Team Member B (Same Machine)

```bash
# Override with CLI parameter for this run
python main.py agent archguard --user-email bob@company.com

# Or set environment variable
export AGENT_USER_EMAIL="bob@company.com"
python main.py agent archguard
```

### Example 3: CI/CD Script

```bash
#!/bin/bash
# CI/CD script that uses environment variable
export AGENT_USER_EMAIL="ci-bot@company.com"
python main.py agent qualityguard
```

## How It Works

1. When `run_agent()` is called, it checks for `--user-email` CLI parameter first
2. If not provided, it checks `AGENT_USER_EMAIL` environment variable
3. If not set, it checks `~/.agent_user_email` config file
4. If none are found, it uses the authenticated email from the login token
5. The selected email is set in `AGENT_USER_EMAIL` environment variable
6. The hooks use lazy initialization to read this environment variable when logging

## Verification

To verify which email is being used, check the console output:

```
🔐 Running as: john.doe@company.com
🌍 Environment: dev
```

Or check the database:

```sql
SELECT DISTINCT user_email FROM execution_log ORDER BY timestamp DESC;
```

## Best Practices

1. **For Individual Developers**: Use config file (`~/.agent_user_email`)
2. **For Shared Machines**: Use CLI parameter (`--user-email`)
3. **For Scripts/Automation**: Use environment variable (`AGENT_USER_EMAIL`)
4. **For CI/CD**: Use environment variable in CI configuration

## Troubleshooting

### Email not being captured

1. Check if email is set: `echo $AGENT_USER_EMAIL`
2. Check config file: `cat ~/.agent_user_email`
3. Verify email format is valid
4. Check console output for which email is being used

### Multiple methods set

The priority order ensures the highest priority method wins:
- CLI parameter always takes precedence
- Environment variable overrides config file
- Config file overrides authenticated email

