# Quick Start - User Email Setup

## For Team Members

### One-Time Setup

Run the setup script to configure your email:

```bash
# Option 1: Python script (recommended)
python3 scripts/setup_user_email.py

# Option 2: Bash script
./scripts/setup_user_email.sh
```

The script will:
1. Prompt for your email address
2. Validate the email format
3. Ask which method you prefer:
   - **Config file** (recommended for individual machines)
   - **Shell profile** (recommended for shared machines)
   - **Both**

### After Setup

Once configured, all your agent runs will automatically use your email:

```bash
# Your email will be used automatically
python main.py agent codecraft
python main.py agent archguard
```

### Override for Specific Runs

If you need a different email for a specific run:

```bash
python main.py agent codecraft --user-email other@email.com
```

## Manual Setup (Alternative)

If you prefer to set it up manually:

### Method 1: Config File
```bash
echo "your.email@company.com" > ~/.agent_user_email
```

### Method 2: Shell Profile
```bash
# Add to ~/.zshrc or ~/.bashrc
export AGENT_USER_EMAIL="your.email@company.com"

# Then reload
source ~/.zshrc  # or source ~/.bashrc
```

## Verify Setup

Check if your email is configured:

```bash
# Check config file
cat ~/.agent_user_email

# Or test with Python
python3 -c "from src.utils.user_utils import get_user_email_from_env; print(get_user_email_from_env())"
```

## Need Help?

See detailed documentation:
- `docs/USER_EMAIL_CAPTURE.md` - Complete usage guide
- `docs/TEAM_SETUP_GUIDE.md` - Team setup options

