"""HTTP API server for authentication, summary, and agents endpoints."""

from __future__ import annotations

import asyncio
from aiohttp import web
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.auth.auth_api import AuthAPI
from src.dashboard.summary_api import SummaryAPI
from src.dashboard.agents_api import AgentsAPI
from src.dashboard.websocket_server import DashboardServer


def setup_cors(app: web.Application) -> None:
    """Add CORS middleware to allow frontend requests."""
    
    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response = web.Response()
        else:
            try:
                response = await handler(request)
            except Exception as e:
                # Log the error for debugging
                import traceback
                print(f"❌ CORS middleware caught error: {e}")
                traceback.print_exc()
                # Create error response with CORS headers
                response = web.json_response(
                    {"error": str(e)}, status=500
                )
        
        # Add CORS headers to all responses (including errors)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        
        return response
    
    app.middlewares.append(cors_middleware)


async def create_app(db_path: str = "logs/agent_execution.db", ws_server: DashboardServer | None = None) -> web.Application:
    """Create and configure the aiohttp application."""
    # Create app without normalize_path_middleware to avoid conflicts
    # We'll handle path normalization manually if needed
    app = web.Application()
    
    # Setup CORS (must be first middleware)
    setup_cors(app)
    
    # Setup API routes
    auth_api = AuthAPI(db_path=db_path)
    auth_api.setup_routes(app)
    
    summary_api = SummaryAPI(db_path=db_path)
    summary_api.setup_routes(app)
    
    agents_api = AgentsAPI(db_path=db_path)
    agents_api.setup_routes(app)
    
    # WebSocket endpoint
    if ws_server:
        async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            
            # Convert aiohttp WebSocket to websockets-compatible interface
            class AioHttpWebSocketAdapter:
                def __init__(self, ws: web.WebSocketResponse):
                    self.ws = ws
                    self.closed = False
                
                async def send(self, message: str):
                    await self.ws.send_str(message)
                
                async def recv(self):
                    msg = await self.ws.receive()
                    if msg.type == web.WSMsgType.TEXT:
                        return msg.data
                    elif msg.type == web.WSMsgType.ERROR:
                        raise Exception(f"WebSocket error: {msg.data}")
                    return None
                
                async def __aiter__(self):
                    async for msg in self.ws:
                        if msg.type == web.WSMsgType.TEXT:
                            yield msg.data
                        elif msg.type == web.WSMsgType.ERROR:
                            break
                
                async def close(self):
                    await self.ws.close()
            
            adapter = AioHttpWebSocketAdapter(ws)
            # Register with the WebSocket server
            ws_server.clients.add(adapter)
            print(f"📊 WebSocket client connected: {len(ws_server.clients)} total")
            try:
                await ws_server._send_initial_data(adapter)
                # Keep connection alive by reading messages until connection closes
                async for msg in ws:
                    if msg.type == web.WSMsgType.ERROR:
                        print(f"❌ WebSocket error: {msg.data}")
                        break
                    elif msg.type == web.WSMsgType.CLOSE:
                        print("📊 WebSocket close received")
                        break
                    elif msg.type == web.WSMsgType.TEXT:
                        # Dashboard is push-only; ignore incoming data
                        pass
            except Exception as e:
                print(f"❌ WebSocket handler error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                ws_server.clients.discard(adapter)
                print(f"📊 WebSocket client disconnected: {len(ws_server.clients)} total")
            
            return ws
        
        app.router.add_get("/ws", websocket_handler)
    
    # Health check endpoint
    async def health_check(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "service": "sdlc-agent-framework-api"})
    
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)
    
    return app


async def run_http_server(host: str = "0.0.0.0", port: int = 8766, db_path: str = "logs/agent_execution.db") -> None:
    """Run the HTTP API server with integrated WebSocket support."""
    # Create WebSocket server instance
    ws_server = DashboardServer(db_path=db_path)
    
    # Start polling task for WebSocket events
    asyncio.create_task(ws_server._poll_new_events())
    
    app = await create_app(db_path=db_path, ws_server=ws_server)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"🌐 HTTP API server running on http://{host}:{port}")
    print(f"   - Auth endpoints: /api/auth/*")
    print(f"   - Summary endpoints: /api/summary/*")
    print(f"   - Agents endpoints: /api/agents/*")
    print(f"   - WebSocket endpoint: ws://{host}:{port}/ws")
    print(f"   - Health check: /health")
    
    # Keep server running
    try:
        await asyncio.Future()  # run forever
    finally:
        await runner.cleanup()


async def main() -> None:
    """Entry point for running the HTTP server standalone."""
    await run_http_server()


if __name__ == "__main__":
    asyncio.run(main())

