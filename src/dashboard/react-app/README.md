# SDLC Agent Dashboard

A modern React-based dashboard for monitoring and managing SDLC agent executions in real-time.

## Features

- **Real-time Monitoring**: Live WebSocket connection for instant agent execution updates
- **Execution Logs**: Comprehensive table view of all agent activities
- **Statistics**: Real-time metrics including success rates, error counts, and average durations
- **Routing**: Multi-page support for future integrations (Git, Deployments)
- **Modern UI**: Built with Ant Design and Tailwind CSS

## Tech Stack

- **React 19** with TypeScript
- **Vite** for fast development and building
- **Ant Design** for UI components
- **Tailwind CSS** for utility styling
- **React Router** for navigation
- **Zustand** (ready for state management)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python WebSocket server running on port 8765

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

### Environment Variables

Create a `.env` file in the root directory:

```env
VITE_WS_URL=ws://localhost:8765
```

## Project Structure

```
src/
├── components/
│   ├── AgentExecution/
│   │   ├── ExecutionLog.tsx      # Table component for execution events
│   │   └── RealTimeFeed.tsx     # Main dashboard with stats and logs
│   └── shared/
│       └── Layout.tsx           # Main layout with sidebar navigation
├── hooks/
│   └── useWebSocket.ts          # WebSocket connection hook
├── pages/
│   ├── Dashboard.tsx            # Agent execution dashboard
│   ├── Git.tsx                 # Git integration (coming soon)
│   └── Deployments.tsx         # Deployment management (coming soon)
├── types/
│   └── index.ts                # TypeScript type definitions
├── App.tsx                     # Main app component with routing
└── main.tsx                    # Entry point
```

## WebSocket Protocol

The dashboard connects to the Python WebSocket server and expects messages in the following format:

### Initial Data
```json
{
  "type": "initial_data",
  "executions": [
    {
      "timestamp": "2025-01-27T12:00:00",
      "session_id": "session-123",
      "hook_event": "PostToolUse",
      "tool_name": "Write",
      "agent_name": "codecraft",
      "phase": "build",
      "status": "success",
      "duration_ms": 150
    }
  ]
}
```

### New Execution
```json
{
  "type": "new_execution",
  "data": {
    "timestamp": "2025-01-27T12:01:00",
    "session_id": "session-123",
    "hook_event": "PreToolUse",
    "tool_name": "Read",
    "status": "success"
  }
}
```

## Future Enhancements

- [ ] Git repository integration
- [ ] Deployment status tracking
- [ ] Agent performance charts
- [ ] Filtering and search capabilities
- [ ] Export functionality
- [ ] Real-time notifications
- [ ] Agent configuration management
