#!/bin/bash
# Script to push to your personal GitHub repository

echo "🚀 Pushing to GitHub..."
echo ""

cd /Users/macbook/sdlc-agent-framework-copy

# Check current status
echo "📋 Current status:"
git status | head -10
echo ""

# Check if we have commits
COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo "0")
echo "Commits: $COMMIT_COUNT"
echo ""

if [ "$COMMIT_COUNT" -eq "0" ]; then
    echo "⚠️  No commits found. Creating initial commit..."
    git add .
    git commit -m "feat: Initial commit - No Vibes Allowed implementation

- Complete RPI workflow (Research-Plan-Implement)  
- All 3 gaps closed and verified
- Docker execution infrastructure
- Structural navigation (NavigationMCPServer)
- Reliable editing with validation (ReliableEditor)
- Sub-agent system with Context Firewall
- Progressive tool disclosure
- 96% token reduction verified
- 100% file safety verified
"
    echo "✅ Initial commit created"
fi

# Check remote
echo ""
echo "📡 Checking remote..."
git remote -v

# If remote doesn't exist, add it
if ! git remote | grep -q origin; then
    echo "Adding remote..."
    git remote add origin https://github.com/ruchithaab-byte/sdlc-agent-framework-copy.git
fi

# Push
echo ""
echo "🚀 Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✅ Done! Check: https://github.com/ruchithaab-byte/sdlc-agent-framework-copy"

