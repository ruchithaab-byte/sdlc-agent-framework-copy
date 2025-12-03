#!/bin/bash

# Fix for Claude Opus 4.5 Agent Framework
# Sets proper credentials and runs the agent

echo "🔧 Setting up Claude Opus 4.5 Agent Framework..."

# Set the Google Cloud credentials (without line breaks!)
export GOOGLE_APPLICATION_CREDENTIALS="/Users/macbook/agentic-coding-framework/sdlc-agent-framework/config/credentials/google-service-account.json"

echo "✅ Credentials set: $GOOGLE_APPLICATION_CREDENTIALS"

# Verify credentials file exists
if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✅ Credentials file found"
else
    echo "❌ Credentials file not found!"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

echo "🚀 Starting ProductSpec agent with Claude Opus 4.5..."
echo "Model: claude-opus-4@20250514"
echo "Project: agents-with-claude"
echo "Region: us-east5"
echo ""

# Run the agent with the provided requirements
python3 main.py agent productspec --requirements "${1:-Create a simple test dashboard}"