# How to Run Agents & See Events in Real-Time Dashboard

## ✅ Setup Complete!

All agents now have **hooks enabled** to log execution events, and the dashboard server **polls for new events every second** to display them in real-time.

---

## Step 1: Start the Dashboard (If Not Running)

The dashboard consists of two servers:

### Terminal 1: WebSocket Server
```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 main.py dashboard --port 8765
```

### Terminal 2: HTTP Server
```bash
cd sdlc-agent-framework/src/dashboard
python3 -m http.server 8000
```

**Or use the helper script:**
```bash
cd sdlc-agent-framework
./scripts/start_dashboard.sh
```

---

## Step 2: Open Dashboard in Browser

Open your browser and navigate to:
```
http://localhost:8000
```

You should see:
- ✅ "Connected to dashboard server" status
- Empty table (will populate when agents run)

---

## Step 3: Run an Agent (In a NEW Terminal)

Open a **new terminal window** and run any agent:

### Option 1: ProductSpec Agent
```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 main.py agent productspec --requirements "Build a todo app"
```

### Option 2: ArchGuard Agent
```bash
python3 main.py agent archguard
```

### Option 3: SprintMaster Agent
```bash
python3 main.py agent sprintmaster
```

### Option 4: CodeCraft Agent
```bash
python3 main.py agent codecraft --task-type backend
```

### Option 5: QualityGuard Agent
```bash
python3 main.py agent qualityguard
```

---

## Step 4: Watch Real-Time Events!

As the agent runs, you'll see events appear in the dashboard:

- **Timestamp**: When each event occurred
- **Session**: Session ID for grouping events
- **Event**: Hook event type:
  - `SessionStart` - Agent session begins
  - `PreToolUse` - Before tool execution
  - `PostToolUse` - After tool execution
  - `SessionEnd` - Agent session ends
  - `Stop` - Agent stopped
- **Tool**: Tool name (Read, Write, Bash, etc.)
- **Status**: `success` or `error`
- **Duration**: Execution time in milliseconds

---

## What Was Fixed

### ✅ Added Hooks to All Agents
- **ProductSpec Agent**: Now logs all execution events
- **ArchGuard Agent**: Now logs all execution events
- **SprintMaster Agent**: Now logs all execution events
- **CodeCraft Agent**: Now logs all execution events
- **QualityGuard Agent**: Now logs all execution events

### ✅ Real-Time Dashboard Updates
- Dashboard server now **polls the database every second** for new events
- Events are **broadcast immediately** to all connected clients
- No need to refresh the page!

---

## Troubleshooting

### No Events Showing?

1. **Check if hooks are working:**
   ```bash
   # Look for hook messages in agent output:
   # 🔧 [PreToolUse] Read - Session: abc123
   # ✅ [PostToolUse] Read - 45ms - Session: abc123
   ```

2. **Check database:**
   ```bash
   sqlite3 logs/agent_execution.db "SELECT COUNT(*) FROM execution_log;"
   ```

3. **Check dashboard server logs:**
   ```bash
   tail -f /tmp/dashboard_ws.log
   ```

### Dashboard Not Connecting?

1. **Check if servers are running:**
   ```bash
   lsof -i :8765  # WebSocket server
   lsof -i :8000  # HTTP server
   ```

2. **Restart servers:**
   ```bash
   pkill -f "python3 main.py dashboard"
   pkill -f "python3 -m http.server 8000"
   # Then restart using Step 1
   ```

---

## Quick Test

Run this to generate test events:

```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 scripts/simple_dashboard_test.py
```

You should see events appear in the dashboard immediately!

---

## Architecture

```
Agent Execution
    ↓
Hooks (documentation_hooks.py)
    ↓
ExecutionLogger → SQLite Database (logs/agent_execution.db)
    ↓
DashboardServer (polls every 1 second)
    ↓
WebSocket Broadcast (ws://localhost:8765)
    ↓
Dashboard HTML (http://localhost:8000)
    ↓
Browser Display (Real-Time Updates!)
```

---

## Next Steps

- Run multiple agents simultaneously to see parallel execution
- Monitor tool usage patterns across different agents
- Track agent performance metrics
- Debug agent execution issues in real-time

Enjoy your real-time agent monitoring! 🎉

