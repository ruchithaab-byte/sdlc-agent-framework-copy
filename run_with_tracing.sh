#!/bin/bash

# Run agents with LangSmith tracing enabled
# This script sets up all required environment variables

echo "🔧 Setting up environment for LangSmith tracing..."

# Source the LangSmith setup (includes Linear and Vertex AI)
source "$(dirname "$0")/setup_langsmith.sh"

echo ""
echo "✅ Environment configured:"
echo "   LangSmith Tracing: $LANGSMITH_TRACING"
echo "   LangSmith Project: $LANGSMITH_PROJECT"
echo "   Linear Team: $LINEAR_TEAM_ID"
echo "   GitHub Token: ${GITHUB_TOKEN:0:10}...${GITHUB_TOKEN: -4}"
echo "   Vertex AI: Enabled"
echo ""
echo "🚀 Ready to run agents with tracing!"
echo ""
echo "Example: python3 main.py agent archguard"
echo "Example: python3 test_real_sdlc_with_tracing.py"

