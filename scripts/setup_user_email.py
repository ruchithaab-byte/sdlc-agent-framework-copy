#!/usr/bin/env python3
"""
One-time setup script to configure user email for agent runs.

This script helps you set up your email address so it's automatically
used in all future agent executions.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config.agent_config import PROJECT_ROOT


def get_config_file_path() -> Path:
    """Return path to user config file."""
    return PROJECT_ROOT / ".claude" / "user_config.json"


def get_shell_profile_path() -> Path:
    """Detect and return shell profile path."""
    shell = os.environ.get("SHELL", "/bin/bash")
    home = Path.home()
    
    if "zsh" in shell:
        return home / ".zshrc"
    elif "bash" in shell:
        return home / ".bashrc"
    else:
        return home / ".profile"


def setup_config_file(email: str) -> bool:
    """Set up email in .claude/user_config.json."""
    config_file = get_config_file_path()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    
    config = {}
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
        except Exception:
            pass
    
    config["user"] = email
    
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✓ Created/updated config file: {config_file}")
        return True
    except Exception as e:
        print(f"✗ Failed to write config file: {e}")
        return False


def setup_shell_profile(email: str) -> bool:
    """Add email to shell profile as environment variable."""
    profile = get_shell_profile_path()
    
    env_line = f'\nexport CLAUDE_AGENT_USER_EMAIL="{email}"\n'
    
    # Check if already exists
    if profile.exists():
        with open(profile) as f:
            content = f.read()
            if f'CLAUDE_AGENT_USER_EMAIL="{email}"' in content:
                print(f"✓ Email already configured in {profile}")
                return True
            if "CLAUDE_AGENT_USER_EMAIL" in content:
                print(f"⚠ Found existing CLAUDE_AGENT_USER_EMAIL in {profile}")
                print(f"  You may want to update it manually")
    
    try:
        with open(profile, "a") as f:
            f.write(env_line)
        print(f"✓ Added email to shell profile: {profile}")
        print(f"  Run 'source {profile}' or restart your terminal to apply")
        return True
    except Exception as e:
        print(f"✗ Failed to update shell profile: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("Claude Agent User Email Setup")
    print("=" * 60)
    print()
    
    # Get email
    email = input("Enter your email address: ").strip()
    if not email or "@" not in email:
        print("✗ Invalid email address")
        sys.exit(1)
    
    print()
    print("Choose setup method:")
    print("  1. Config file only (.claude/user_config.json)")
    print("  2. Shell profile only (adds to ~/.zshrc or ~/.bashrc)")
    print("  3. Both (recommended)")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    print()
    success = True
    
    if choice == "1":
        success = setup_config_file(email)
    elif choice == "2":
        success = setup_shell_profile(email)
        if success:
            print()
            print("⚠ Remember to run 'source ~/.zshrc' (or ~/.bashrc) or restart terminal")
    elif choice == "3":
        success1 = setup_config_file(email)
        print()
        success2 = setup_shell_profile(email)
        success = success1 and success2
        if success2:
            print()
            print("⚠ Remember to run 'source ~/.zshrc' (or ~/.bashrc) or restart terminal")
    else:
        print("✗ Invalid choice")
        sys.exit(1)
    
    print()
    if success:
        print("=" * 60)
        print("✓ Setup complete!")
        print("=" * 60)
        print()
        print("Your email will be used in all future agent runs.")
        print()
        if choice in ["2", "3"]:
            print("Next steps:")
            print(f"  1. Run: source {get_shell_profile_path()}")
            print("  2. Or restart your terminal")
            print("  3. Then run your agents as usual")
    else:
        print("✗ Setup encountered errors. Please check the messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

