"""WebSocket dashboard server for real-time execution monitoring."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import Dict, Set

from websockets.server import WebSocketServerProtocol, serve

from src.logging.execution_logger import ExecutionLogger


class DashboardServer:
    """Broadcasts execution events to connected WebSocket clients."""

    def __init__(self, db_path: str = "logs/agent_execution.db") -> None:
        self.db_path = db_path
        self.clients: Set[WebSocketServerProtocol] = set()
        self.logger = ExecutionLogger(db_path=db_path)
        self.last_event_id = 0

    async def register(self, websocket: WebSocketServerProtocol) -> None:
        self.clients.add(websocket)
        print(f"📊 Client connected: {len(self.clients)} total")
        await self._send_initial_data(websocket)

    async def unregister(self, websocket: WebSocketServerProtocol) -> None:
        self.clients.discard(websocket)
        print(f"📊 Client disconnected: {len(self.clients)} total")

    async def _send_initial_data(self, websocket: WebSocketServerProtocol) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Join with agent_performance to get cost data
                cursor.execute(
                    """
                    SELECT el.id, el.timestamp, el.session_id, el.hook_event, el.tool_name,
                           el.agent_name, el.phase, el.status, el.duration_ms,
                           ap.total_cost_usd
                    FROM execution_log el
                    LEFT JOIN agent_performance ap 
                        ON el.session_id = ap.session_id 
                        AND el.agent_name = ap.agent_name
                    ORDER BY el.timestamp DESC
                    LIMIT 50
                    """
                )
                rows = cursor.fetchall()
                if rows:
                    self.last_event_id = max(row[0] for row in rows)
                else:
                    self.last_event_id = 0
            payload = {
                "type": "initial_data",
                "executions": [
                    {
                        "timestamp": row[1] or "",
                        "session_id": row[2] or "",
                        "hook_event": row[3] or "",
                        "tool_name": row[4] or "",
                        "agent_name": row[5] or "",
                        "phase": row[6] or "",
                        "status": row[7] or "success",
                        "duration_ms": row[8],
                        "cost_usd": row[9] if row[9] is not None else 0.0,
                        "budget_exceeded": False,  # Not stored in DB, calculate from budget if needed
                    }
                    for row in rows
                ],
            }
            await websocket.send(json.dumps(payload))
            print(f"📊 Sent {len(rows)} initial events to client")
        except Exception as exc:
            print(f"❌ Error sending initial data: {exc}")

    async def broadcast_execution(self, execution_data: Dict[str, str]) -> None:
        if not self.clients:
            return
        message = json.dumps({"type": "new_execution", "data": execution_data})
        for websocket in set(self.clients):
            try:
                await websocket.send(message)
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"Error sending to client: {exc}")
                await self.unregister(websocket)

    async def handler(self, websocket: WebSocketServerProtocol) -> None:
        await self.register(websocket)
        try:
            async for _ in websocket:
                # Dashboard is push-only; ignore incoming data.
                pass
        finally:
            await self.unregister(websocket)

    async def _poll_new_events(self) -> None:
        """Poll database for new events and broadcast them."""
        while True:
            try:
                await asyncio.sleep(1)  # Poll every second
                if not self.clients:
                    continue
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    # Join with agent_performance to get cost data
                    cursor.execute(
                        """
                        SELECT el.id, el.timestamp, el.session_id, el.hook_event, el.tool_name,
                               el.agent_name, el.phase, el.status, el.duration_ms,
                               ap.total_cost_usd
                        FROM execution_log el
                        LEFT JOIN agent_performance ap 
                            ON el.session_id = ap.session_id 
                            AND el.agent_name = ap.agent_name
                        WHERE el.id > ?
                        ORDER BY el.timestamp ASC
                        """,
                        (self.last_event_id,),
                    )
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        self.last_event_id = row[0]
                        execution_data = {
                            "timestamp": row[1],
                            "session_id": row[2],
                            "hook_event": row[3],
                            "tool_name": row[4],
                            "agent_name": row[5],
                            "phase": row[6],
                            "status": row[7],
                            "duration_ms": row[8],
                            "cost_usd": row[9] if row[9] is not None else 0.0,
                            "budget_exceeded": False,  # Not stored in DB, calculate from budget if needed
                        }
                        await self.broadcast_execution(execution_data)
            except Exception as exc:
                print(f"Error polling events: {exc}")

    async def run(self, host: str = "0.0.0.0", port: int = 8766) -> None:
        async with serve(self.handler, host, port):
            print(f"Dashboard server running on ws://{host}:{port}")
            # Start polling task in background
            asyncio.create_task(self._poll_new_events())
            await asyncio.Future()  # run forever


async def main() -> None:
    server = DashboardServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
