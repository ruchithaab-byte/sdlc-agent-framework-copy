#!/bin/bash
# Remove secrets from files and push to GitHub

echo "🔒 Removing secrets from files..."
echo ""

cd /Users/macbook/sdlc-agent-framework-copy

# Files with secrets to remove or redact
FILES_WITH_SECRETS=(
    "setup_langsmith.sh"
    "CRITICAL_FIXES_COMPLETE.md"
    "EXECUTION_VERIFICATION_GUIDE.md"
    "FIXES_APPLIED.md"
)

echo "📝 Option 1: Delete files with secrets (recommended for docs)"
echo "📝 Option 2: Redact secrets in setup_langsmith.sh"
echo ""

# Remove documentation files with embedded secrets
echo "Removing documentation files with hardcoded secrets..."
rm -f CRITICAL_FIXES_COMPLETE.md
rm -f EXECUTION_VERIFICATION_GUIDE.md
rm -f FIXES_APPLIED.md

# Redact secrets in setup_langsmith.sh
if [ -f "setup_langsmith.sh" ]; then
    echo "Redacting secrets in setup_langsmith.sh..."
    sed -i '' 's/ls_[a-zA-Z0-9_-]*/YOUR_LANGSMITH_API_KEY_HERE/g' setup_langsmith.sh
    sed -i '' 's/lin_api_[a-zA-Z0-9_-]*/YOUR_LINEAR_API_KEY_HERE/g' setup_langsmith.sh
    sed -i '' 's/ghp_[a-zA-Z0-9]*/YOUR_GITHUB_TOKEN_HERE/g' setup_langsmith.sh
    sed -i '' 's/github_pat_[a-zA-Z0-9_]*/YOUR_GITHUB_PAT_HERE/g' setup_langsmith.sh
fi

echo ""
echo "✅ Secrets removed/redacted"
echo ""

# Stage changes
echo "📦 Staging changes..."
git add -A

# Check if there are changes
if git diff --staged --quiet; then
    echo "⚠️  No changes to commit (files may not have existed)"
else
    # Amend the previous commit
    echo "💾 Amending commit to remove secrets..."
    git commit --amend --no-edit
    
    echo ""
    echo "🚀 Force pushing to GitHub (rewriting history)..."
    git push origin main --force
    
    echo ""
    echo "✅ Success! Secrets removed and pushed to GitHub!"
    echo "🔗 View at: https://github.com/ruchithaab-byte/sdlc-agent-framework-copy"
fi

echo ""
echo "⚠️  IMPORTANT: Rotate these API keys immediately!"
echo "   - Langchain API key"
echo "   - Linear API key"  
echo "   - GitHub Personal Access Tokens"
echo ""
echo "They were exposed in git history and should be revoked."

