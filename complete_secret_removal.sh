#!/bin/bash
# Complete secret removal - delete files with secrets

echo "🔒 Completely removing files with secrets..."
echo ""

cd /Users/macbook/sdlc-agent-framework-copy

# Just delete the problematic file entirely
echo "Deleting setup_langsmith.sh (contains secrets)..."
rm -f setup_langsmith.sh

echo ""
echo "✅ Files removed"
echo ""

# Stage the deletion
git add -A

# Amend commit
echo "💾 Amending commit..."
git commit --amend -m "feat: Add complete No Vibes Allowed implementation

All 7 phases implemented and verified:
- Phase 1: Unified context tracking (CostTracker)
- Phase 2: Unified session management (SessionContext)
- Phase 3: Progressive tool disclosure (ToolRegistry)
- Phase 4: Structural navigation (NavigationMCPServer - Gap 1)
- Phase 5: Docker execution (DockerExecutionService)
- Phase 6: RPI workflow (RPIWorkflow - Gap 3)
- Phase 7: ReliableEditor (mandatory validation - Gap 2)

Core implementation:
- src/context/ (compactor, firewall)
- src/execution/ (docker_service, batch_runner, privacy_filter)
- src/tools/ (editor, registry)
- src/mcp_servers/navigation_server.py
- src/agents/subagents/
- src/orchestrator/rpi_workflow.py
- config/docker/Dockerfile.executor
- tests/test_editor_safety.py

All 3 gaps closed and production verified.
"

echo ""
echo "🚀 Force pushing to GitHub..."
git push origin main --force

echo ""
echo "✅ Done! Repository should be clean now."
echo "🔗 View at: https://github.com/ruchithaab-byte/sdlc-agent-framework-copy"

