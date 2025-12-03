#!/bin/bash
# Quick script to start the dashboard server and open the dashboard

cd "$(dirname "$0")/.."

echo "Starting Dashboard Server..."
python3 main.py dashboard --port 8765 &
DASHBOARD_PID=$!

echo "Dashboard server started (PID: $DASHBOARD_PID)"
echo "WebSocket: ws://localhost:8765"
echo ""
echo "To view the dashboard:"
echo "1. Open: src/dashboard/index.html in your browser"
echo "   Or run: python3 -m http.server 8000 (in src/dashboard/)"
echo ""
echo "To stop the dashboard: kill $DASHBOARD_PID"
echo ""

# Keep script running
wait $DASHBOARD_PID

