#!/bin/bash
# Setup script for configuring user email for agent executions
# Run this once to set your default email for all agent runs

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Agent Framework - User Email Setup                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to validate email format
validate_email() {
    local email=$1
    if [[ $email =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Check if email is already configured
CONFIG_FILE="$HOME/.agent_user_email"
if [ -f "$CONFIG_FILE" ]; then
    CURRENT_EMAIL=$(cat "$CONFIG_FILE" | tr -d '[:space:]')
    echo -e "${YELLOW}⚠️  You already have an email configured:${NC}"
    echo -e "   ${CURRENT_EMAIL}"
    echo ""
    read -p "Do you want to update it? (y/n): " update_choice
    if [[ ! $update_choice =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✓ Keeping existing email: ${CURRENT_EMAIL}${NC}"
        exit 0
    fi
    echo ""
fi

# Prompt for email
echo -e "${BLUE}Enter your email address for agent executions:${NC}"
read -p "Email: " user_email

# Validate email
if [ -z "$user_email" ]; then
    echo -e "${RED}✗ Error: Email cannot be empty${NC}"
    exit 1
fi

# Trim whitespace
user_email=$(echo "$user_email" | xargs)

if ! validate_email "$user_email"; then
    echo -e "${RED}✗ Error: Invalid email format: $user_email${NC}"
    echo "   Please enter a valid email address (e.g., user@company.com)"
    exit 1
fi

# Ask for setup method
echo ""
echo -e "${BLUE}Choose setup method:${NC}"
echo "  1) Config file (~/.agent_user_email) - Recommended for individual machines"
echo "  2) Shell profile (~/.zshrc or ~/.bashrc) - Recommended for shared machines"
echo "  3) Both"
read -p "Choice (1-3) [default: 1]: " method_choice
method_choice=${method_choice:-1}

# Setup config file
if [[ $method_choice == "1" || $method_choice == "3" ]]; then
    echo "$user_email" > "$CONFIG_FILE"
    chmod 600 "$CONFIG_FILE"  # Restrict permissions
    echo -e "${GREEN}✓ Config file created: $CONFIG_FILE${NC}"
fi

# Setup shell profile
if [[ $method_choice == "2" || $method_choice == "3" ]]; then
    # Detect shell
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_PROFILE="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_PROFILE="$HOME/.bashrc"
    else
        SHELL_PROFILE="$HOME/.profile"
    fi
    
    # Check if already exists
    if grep -q "AGENT_USER_EMAIL" "$SHELL_PROFILE" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  AGENT_USER_EMAIL already exists in $SHELL_PROFILE${NC}"
        read -p "Do you want to update it? (y/n): " update_shell
        if [[ $update_shell =~ ^[Yy]$ ]]; then
            # Remove old entry
            sed -i.bak "/AGENT_USER_EMAIL/d" "$SHELL_PROFILE"
        else
            echo -e "${YELLOW}⚠️  Skipping shell profile update${NC}"
            method_choice="1"  # Only config file was set
        fi
    fi
    
    if [[ $method_choice == "2" || $method_choice == "3" ]]; then
        # Add to shell profile
        echo "" >> "$SHELL_PROFILE"
        echo "# Agent Framework - User Email" >> "$SHELL_PROFILE"
        echo "export AGENT_USER_EMAIL=\"$user_email\"" >> "$SHELL_PROFILE"
        echo -e "${GREEN}✓ Added to shell profile: $SHELL_PROFILE${NC}"
        echo -e "${YELLOW}⚠️  Run 'source $SHELL_PROFILE' or restart your terminal to apply${NC}"
    fi
fi

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup Complete!                                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Your email is configured:${NC} ${GREEN}$user_email${NC}"
echo ""

# Show priority order
echo -e "${BLUE}Email priority order:${NC}"
echo "  1. CLI parameter (--user-email) - highest priority"
if [[ $method_choice == "2" || $method_choice == "3" ]]; then
    echo -e "  2. ${GREEN}Environment variable (AGENT_USER_EMAIL)${NC} - configured"
else
    echo "  2. Environment variable (AGENT_USER_EMAIL) - not configured"
fi
if [[ $method_choice == "1" || $method_choice == "3" ]]; then
    echo -e "  3. ${GREEN}Config file (~/.agent_user_email)${NC} - configured"
else
    echo "  3. Config file (~/.agent_user_email) - not configured"
fi
echo "  4. Authenticated email (from login token) - fallback"
echo ""

# Test the configuration
echo -e "${BLUE}Testing configuration...${NC}"
if command -v python3 &> /dev/null; then
    cd "$(dirname "$0")/.." || exit 1
    TEST_EMAIL=$(python3 -c "from src.utils.user_utils import get_user_email_from_env; print(get_user_email_from_env() or 'Not found')" 2>/dev/null || echo "Not found")
    if [ "$TEST_EMAIL" == "$user_email" ]; then
        echo -e "${GREEN}✓ Configuration verified!${NC}"
    else
        echo -e "${YELLOW}⚠️  Configuration not yet active (may need shell reload)${NC}"
    fi
fi

echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  • Run agents normally: ${GREEN}python main.py agent <agent-name>${NC}"
echo "  • Your email will be used automatically"
echo "  • Override per run: ${GREEN}python main.py agent <agent-name> --user-email other@email.com${NC}"
echo ""

