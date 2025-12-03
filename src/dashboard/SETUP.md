# Dashboard Setup Guide

This guide explains how to set up and run the React dashboard for the SDLC Agent Framework.

## Architecture

The dashboard consists of two parts:
1. **Python WebSocket Server** (port 8765) - Broadcasts agent execution events
2. **React Dashboard** (port 3000) - Displays real-time agent execution data

## Prerequisites

- Python 3.10+ with virtual environment
- Node.js 18+ and npm
- All Python dependencies installed (see main project README)

## Quick Start

### 1. Start the Python WebSocket Server

From the project root:

```bash
cd sdlc-agent-framework
source venv/bin/activate  # or ./venv/bin/activate
python main.py dashboard
```

The server will start on `ws://localhost:8765`

### 2. Start the React Dashboard

In a new terminal:

```bash
cd sdlc-agent-framework/src/dashboard/react-app
npm install  # First time only
npm run dev
```

The dashboard will be available at `http://localhost:3000`

## Development Workflow

1. **Terminal 1**: Run the Python WebSocket server
   ```bash
   python main.py dashboard
   ```

2. **Terminal 2**: Run the React dev server
   ```bash
   cd src/dashboard/react-app
   npm run dev
   ```

3. **Terminal 3**: Run an agent to generate events
   ```bash
   python main.py agent productspec --requirements "Build authentication system"
   ```

## Environment Variables

Create a `.env` file in `react-app/` directory:

```env
VITE_WS_URL=ws://localhost:8765
```

## Building for Production

```bash
cd src/dashboard/react-app
npm run build
```

The built files will be in `dist/` directory. You can serve them with any static file server or integrate them into the Python server.

## Project Structure

```
dashboard/
├── react-app/              # React application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks (WebSocket)
│   │   ├── pages/         # Page components
│   │   └── types/         # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── websocket_server.py    # Python WebSocket server
└── index.html            # Legacy HTML dashboard (can be removed)
```

## Troubleshooting

### WebSocket Connection Failed

- Ensure the Python server is running on port 8765
- Check firewall settings
- Verify `VITE_WS_URL` in `.env` matches the server URL

### Build Errors

- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

### Port Already in Use

- Change the React dev server port in `vite.config.ts`
- Or change the WebSocket server port in `main.py dashboard --port <new-port>`

