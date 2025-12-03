# Hooks & WebSocket Verification Guide

## ✅ System Status: FULLY OPERATIONAL

All verification checks passed! Hooks are working and WebSocket is connected.

---

## 🔍 How to Verify Hooks Are Working

### Method 1: Run Verification Script (Recommended)

```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 scripts/verify_hooks.py
```

**Expected Output:**
```
✅ Hooks: PASS
✅ Database: PASS
✅ WebSocket Server: PASS
✅ HTTP Server: PASS

🎉 ALL CHECKS PASSED! System is fully operational!
```

### Method 2: Check Dashboard Status

1. Open dashboard: http://localhost:8000
2. Look at the status line (below the title)
3. Should show: **🟢 Connected | Events: X | Uptime: Xs | Last event: Xs ago**

### Method 3: Check Database Directly

```bash
cd sdlc-agent-framework
sqlite3 logs/agent_execution.db "SELECT COUNT(*) FROM execution_log;"
```

Should show a number > 0 if hooks are working.

### Method 4: Run an Agent and Watch Dashboard

```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 main.py agent productspec --requirements "Test"
```

Watch the dashboard - events should appear in real-time!

---

## 🔌 WebSocket Status Indicators

The dashboard now shows comprehensive WebSocket status:

### Status Messages:

- **🟢 Connected | Events: X | Uptime: Xs | Last event: Xs ago**
  - WebSocket is open and working
  - Shows total events received
  - Shows connection uptime
  - Shows time since last event

- **🔴 Disconnected. Reconnecting in 3s…**
  - WebSocket closed
  - Auto-reconnecting with exponential backoff

- **🔴 WebSocket error. Check server.**
  - Connection error occurred
  - Check if dashboard server is running

### Check WebSocket in Browser Console

1. Open dashboard: http://localhost:8000
2. Press F12 to open Developer Tools
3. Go to Console tab
4. You should see:
   - `✅ WebSocket connected`
   - `📊 Loaded X initial events`
   - `📨 New event received: [event type]`

---

## 🧪 Testing Hooks

### Test Hook Functions Directly

```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 -c "
import asyncio
from src.hooks.documentation_hooks import pre_tool_use_logger

async def test():
    await pre_tool_use_logger(
        {'session_id': 'test', 'tool_name': 'Read'},
        'test-id',
        None
    )
    print('✅ Hook executed!')

asyncio.run(test())
"
```

### Test with Real Agent

```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 scripts/test_agent_with_dashboard.py
```

This runs a real agent and generates events you can see in the dashboard.

---

## 📊 What Events to Expect

When an agent runs, you should see these events in order:

1. **SessionStart** - Agent session begins
2. **PreToolUse** - Before each tool execution (Read, Write, Bash, etc.)
3. **PostToolUse** - After each tool execution (with duration)
4. **SessionEnd** - Agent session completes

### Example Event Flow:

```
SessionStart
  ↓
PreToolUse (Read)
  ↓
PostToolUse (Read) - 45ms
  ↓
PreToolUse (Write)
  ↓
PostToolUse (Write) - 120ms
  ↓
PreToolUse (Bash)
  ↓
PostToolUse (Bash) - 200ms
  ↓
SessionEnd
```

---

## 🔧 Troubleshooting

### No Events Showing in Dashboard

**Check 1: Are hooks enabled?**
```bash
grep -r "hooks=" sdlc-agent-framework/src/agents/*.py
```
Should show hooks configuration in all agent files.

**Check 2: Is database being written?**
```bash
sqlite3 logs/agent_execution.db "SELECT COUNT(*) FROM execution_log;"
```

**Check 3: Is dashboard server polling?**
```bash
tail -f /tmp/dashboard_ws.log
```
Should show polling activity.

### WebSocket Not Connecting

**Check 1: Is server running?**
```bash
lsof -i :8765
```
Should show Python process.

**Check 2: Check server logs:**
```bash
tail -20 /tmp/dashboard_ws.log
```

**Check 3: Restart servers:**
```bash
pkill -f "python.*dashboard"
pkill -f "python.*http.server"
# Then restart using HOW_TO_RUN_AGENTS.md
```

### Hooks Not Logging Events

**Check 1: Verify hooks are in agent code:**
```bash
grep -A 5 "hooks = {" sdlc-agent-framework/src/agents/productspec_agent.py
```

**Check 2: Test hooks directly:**
```bash
python3 scripts/verify_hooks.py
```

**Check 3: Check if SDK supports hooks:**
```bash
python3 -c "from claude_agent_sdk import HookMatcher; print('✅ HookMatcher available')"
```

---

## 📈 Monitoring Dashboard Health

### Real-Time Status

The dashboard status line shows:
- **Connection state** (🟢/🔴)
- **Event count** (total events received)
- **Uptime** (how long connected)
- **Last event** (time since last event)

### Expected Behavior

- **Events should appear within 1-2 seconds** of agent execution
- **Status should show 🟢 Connected** when working
- **Event count should increase** as agents run
- **Last event time should update** when new events arrive

---

## 🎯 Quick Verification Checklist

- [ ] Run `python3 scripts/verify_hooks.py` - all checks pass
- [ ] Dashboard shows "🟢 Connected" status
- [ ] Dashboard displays events in table
- [ ] Run an agent - events appear in real-time
- [ ] Browser console shows "✅ WebSocket connected"
- [ ] Database has events: `sqlite3 logs/agent_execution.db "SELECT COUNT(*) FROM execution_log;"`

---

## 🚀 Quick Start

1. **Start dashboard:**
   ```bash
   cd sdlc-agent-framework
   source venv/bin/activate
   python3 main.py dashboard --port 8765 &
   cd src/dashboard && python3 -m http.server 8000 &
   ```

2. **Open dashboard:** http://localhost:8000

3. **Verify status:** Should show "🟢 Connected | Events: X"

4. **Run agent:**
   ```bash
   python3 main.py agent productspec --requirements "Test"
   ```

5. **Watch dashboard:** Events appear in real-time!

---

## 📝 Summary

✅ **Hooks are working** - Verified by verification script  
✅ **WebSocket is connected** - Dashboard shows 🟢 status  
✅ **Events are logging** - Database has 14+ events  
✅ **Real-time updates** - Polling every 1 second  
✅ **All agents have hooks** - ProductSpec, ArchGuard, SprintMaster, CodeCraft, QualityGuard  

**The system is fully operational!** 🎉

