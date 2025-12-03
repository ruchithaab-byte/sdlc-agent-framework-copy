#!/bin/bash
# Quick status check for dashboard and hooks

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  📊 DASHBOARD & HOOKS STATUS CHECK                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check WebSocket server
if lsof -ti:8765 > /dev/null 2>&1; then
    echo "✅ WebSocket Server: RUNNING (port 8765)"
else
    echo "❌ WebSocket Server: NOT RUNNING"
fi

# Check HTTP server
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ HTTP Server: RUNNING (port 8000)"
else
    echo "❌ HTTP Server: NOT RUNNING"
fi

# Check database
if [ -f "logs/agent_execution.db" ]; then
    COUNT=$(sqlite3 logs/agent_execution.db "SELECT COUNT(*) FROM execution_log;" 2>/dev/null || echo "0")
    echo "✅ Database: EXISTS ($COUNT events)"
else
    echo "❌ Database: NOT FOUND"
fi

# Check hooks in agents
HOOKS_COUNT=$(grep -r "hooks = {" src/agents/*.py 2>/dev/null | wc -l | tr -d ' ')
if [ "$HOOKS_COUNT" -ge 5 ]; then
    echo "✅ Hooks: ENABLED in $HOOKS_COUNT agents"
else
    echo "⚠️  Hooks: Only in $HOOKS_COUNT agents (expected 5)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Quick Commands:"
echo "  • Verify: python3 scripts/verify_hooks.py"
echo "  • Dashboard: http://localhost:8000"
echo "  • Test agent: python3 scripts/test_agent_with_dashboard.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
