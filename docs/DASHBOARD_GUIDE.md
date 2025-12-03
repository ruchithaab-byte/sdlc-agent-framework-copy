# Dashboard Guide

## Overview

The SDLC Agent Dashboard provides real-time monitoring of agent execution events through a WebSocket connection.

## Quick Start

### Step 1: Start the Dashboard Server

```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 main.py dashboard
```

The server will start on `ws://localhost:8765` by default.

### Step 2: Generate Test Events

In a new terminal, run:

```bash
cd sdlc-agent-framework
source venv/bin/activate
python3 scripts/simple_dashboard_test.py
```

This creates sample execution events in the database.

### Step 3: View the Dashboard

**Option A: Direct File Access**
```bash
# Open in your browser
open src/dashboard/index.html
# Or on Linux:
xdg-open src/dashboard/index.html
```

**Option B: HTTP Server (Recommended)**
```bash
cd src/dashboard
python3 -m http.server 8000
```

Then open: http://localhost:8000

## What the Dashboard Shows

The dashboard displays:
- **Timestamp** - When the event occurred
- **Session** - Session ID for grouping events
- **Event** - Hook event type (SessionStart, PreToolUse, PostToolUse, etc.)
- **Tool** - Tool name if applicable
- **Status** - success or error
- **Duration** - Execution time in milliseconds

## Dashboard Features

1. **Real-time Updates**: New events appear automatically via WebSocket
2. **Initial Data Load**: Shows last 50 events when you connect
3. **Auto-reconnect**: Reconnects if connection is lost
4. **Event Limit**: Shows last 100 events (older events are removed)

## Running Agents with Dashboard

To see real agent execution in the dashboard:

```bash
# Terminal 1: Start dashboard
python3 main.py dashboard

# Terminal 2: Run an agent
python3 main.py agent productspec --requirements "Build authentication system"
```

The dashboard will show all execution events from the agent run.

## Troubleshooting

### Dashboard shows "Connecting..."

**Check:**
1. Dashboard server is running: `python3 main.py dashboard`
2. Port 8765 is not blocked by firewall
3. Browser console for WebSocket errors

### No events showing

**Check:**
1. Events exist in database:
   ```bash
   sqlite3 logs/agent_execution.db "SELECT COUNT(*) FROM execution_log;"
   ```
2. Create test events: `python3 scripts/simple_dashboard_test.py`
3. Refresh the dashboard page

### WebSocket connection errors

**Solutions:**
1. Check if port 8765 is available: `lsof -i :8765`
2. Try different port: `python3 main.py dashboard --port 8766`
3. Update `index.html` WebSocket URL if using different port

## Scripts

- `scripts/simple_dashboard_test.py` - Creates test events without running agents
- `scripts/test_dashboard.py` - Full test with agent execution
- `scripts/start_dashboard.sh` - Quick dashboard startup script

## Architecture

```
Agent Execution
    ↓
Hooks (documentation_hooks.py)
    ↓
ExecutionLogger → SQLite Database (logs/agent_execution.db)
    ↓
DashboardServer → WebSocket (ws://localhost:8765)
    ↓
Dashboard HTML → Browser Display
```

## Database Schema

Events are stored in `logs/agent_execution.db`:

- **execution_log** - Individual execution events
- **tool_usage** - Aggregated tool statistics
- **agent_performance** - Agent-level metrics

## Customization

### Change Dashboard Port

```bash
python3 main.py dashboard --port 9000
```

Update `index.html` WebSocket URL:
```javascript
const ws = new WebSocket("ws://localhost:9000");
```

### Change Event Limit

Edit `src/dashboard/index.html`:
```javascript
while (eventsTable.children.length > 200) {  // Change 100 to 200
```

## Next Steps

- Run real agents to see live execution
- Monitor tool usage patterns
- Track agent performance metrics
- Debug agent execution issues

