import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import logger, setup_logging
from infrastructure.database.session import init_db
from application.services import global_coordinator, global_db_writer, global_capture_engine
from interfaces.websockets.manager import WebSocketConnectionManager
from interfaces.api.routes import capture, traffic, metrics

# Ensure logging is established
setup_logging()

# Instantiating the WebSocket Manager and injecting it into the Traffic Coordinator
ws_manager = WebSocketConnectionManager()
global_coordinator.websocket_manager = ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown lifecycle events.
    Bootstraps DB models, starts batch writers, and safely disposes sniffers on exit.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} backend...")
    
    # 1. Initialize DB tables
    await init_db()
    
    # 2. Cleanup stale database sessions from previous runs
    await global_coordinator.cleanup_stale_sessions()
    
    # 3. Start high-throughput database batch writer
    global_db_writer.start()
    
    yield
    
    logger.info("Shutting down backend...")
    # 1. Terminate all active sniffing sessions
    global_capture_engine.stop_all_sessions()
    
    # 2. Stop and flush DB batch writer
    await global_db_writer.stop()
    
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
    allow_origins=["*"],
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
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "live-traffic")


@app.websocket("/ws/statistics")
async def ws_statistics(websocket: WebSocket):
    """Real-time metrics stream endpoint, broadcasting statistics summaries once per second."""
    await ws_manager.connect(websocket, "statistics")
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "statistics")
    except Exception as e:
        logger.error(f"Error on statistics WebSocket: {e}")
        ws_manager.disconnect(websocket, "statistics")


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """Security alert stream endpoint, broadcasting IDS logs instantly as they trigger."""
    await ws_manager.connect(websocket, "alerts")
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "alerts")
    except Exception as e:
        logger.error(f"Error on alerts WebSocket: {e}")
        ws_manager.disconnect(websocket, "alerts")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
