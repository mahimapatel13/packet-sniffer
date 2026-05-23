import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.infrastructure.database.session import init_db
from app.application.services import global_coordinator, global_db_writer, global_capture_engine, global_stats_engine
from app.interfaces.websockets.manager import WebSocketConnectionManager
from app.infrastructure.services.geo import geo_resolver
from app.interfaces.api.routes import capture, traffic, metrics

# Ensure logging is established
setup_logging()

# Instantiating the WebSocket Manager and injecting it into the Traffic Coordinator
ws_manager = WebSocketConnectionManager()
global_coordinator.websocket_manager = ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} backend...")

    await init_db()

    await global_coordinator.cleanup_stale_sessions()

    global_db_writer.start()

    yield

    logger.info("Shutting down backend...")
    sessions_snapshot = list(global_capture_engine._active_sessions.values())

    
    # Stop all capture threads
    global_capture_engine.stop_all_sessions()

    geo_resolver.shutdown()
    logger.info("GeoIP resolver shut down.")

    # Flush DB queue
    await global_db_writer.stop()

    # Shutdown DNS resolver thread pools
    for session in global_capture_engine._active_sessions.values():
        session._parser.resolver.shutdown()

    logger.info("Backend cleanup complete. Shutdown successful.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready backend for the Network Traffic Analyzer, exposing REST APIs and WebSockets.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for multi-origin dashboard environments (React, Vue, Flutter, Angular, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST Routers
app.include_router(capture.router)
app.include_router(traffic.router)
app.include_router(metrics.router)

# Health Check Route
@app.get("/")
async def health_check():
    active_sessions = global_capture_engine.get_active_sessions()
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "active_captures": active_sessions
    }

# --- WebSocket Channel Endpoints ---
@app.websocket("/ws/live-traffic")
async def ws_live_traffic(websocket: WebSocket):
    await ws_manager.connect(websocket, "live-traffic")
    try:
        while True:
            await asyncio.sleep(1)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        ws_manager.disconnect(websocket, "live-traffic")

@app.websocket("/ws/statistics")
async def ws_statistics(websocket: WebSocket):
    await ws_manager.connect(websocket, "statistics")
    try:
        while True:
            await asyncio.sleep(1)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        ws_manager.disconnect(websocket, "statistics")

@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket, "alerts")
    try:
        while True:
            await asyncio.sleep(1)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        ws_manager.disconnect(websocket, "alerts")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
