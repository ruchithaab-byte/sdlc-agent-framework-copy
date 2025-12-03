#!/bin/bash
# Setup script for Vertex AI configuration
# Run this before executing test_real_sdlc_with_tracing.py

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREDENTIALS_FILE="${PROJECT_ROOT}/config/credentials/google-service-account.json"

# Check if credentials file exists
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo "❌ Error: Credentials file not found at: $CREDENTIALS_FILE"
    echo "   Please ensure google-service-account.json exists in config/credentials/"
    exit 1
fi

# Extract project ID from credentials file
PROJECT_ID=$(python3 -c "import json; print(json.load(open('$CREDENTIALS_FILE'))['project_id'])" 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "⚠️  Warning: Could not extract project_id from credentials file"
    PROJECT_ID="agents-with-claude"  # Default from your file
fi

echo "✅ Setting up Vertex AI environment..."
echo "   Project ID: $PROJECT_ID"
echo "   Credentials: $CREDENTIALS_FILE"
echo ""

# 1. Point to credentials file
export GOOGLE_APPLICATION_CREDENTIALS="$CREDENTIALS_FILE"
echo "✅ GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"

# 2. Set the Project ID
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
echo "✅ GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"

# 3. CRITICAL: Tell the SDK to use Vertex AI
export CLAUDE_CODE_USE_VERTEX=1
echo "✅ CLAUDE_CODE_USE_VERTEX=1"

# 4. Set the Region (Claude on Vertex - use "global" for claude-opus-4-5@20251101)
# Note: For Opus 4.5, "global" region is recommended as shown in AnthropicVertex examples
# Force to "global" to match the model configuration
export CLAUDE_VERTEX_REGION="global"
echo "✅ CLAUDE_VERTEX_REGION=global (forced for Opus 4.5 model)"

# 5. Unset Anthropic API key to force Vertex AI usage
unset ANTHROPIC_API_KEY
echo "✅ ANTHROPIC_API_KEY unset (forcing Vertex AI)"

echo ""
echo "🎯 Vertex AI configuration complete!"
echo ""
echo "To verify, run:"
echo "  python test_real_sdlc_with_tracing.py"
echo ""
echo "If you get 404 errors, try changing the region:"
echo "  export CLAUDE_VERTEX_REGION=europe-west1"
echo "  python test_real_sdlc_with_tracing.py"

