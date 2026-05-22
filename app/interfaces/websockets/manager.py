import time
import json
import asyncio
from typing import Set, Optional, Any
from fastapi import WebSocket
from domain.entities import TrafficRecord, Alert
from core.config import settings
from core.logging import logger
from infrastructure.services.stats import global_stats_engine

class WebSocketConnectionManager:
    """
    Manages active WebSocket connections for live traffic feeds, 
    periodic statistics dashboards, and threat alerts.
    """
    def __init__(self):
        # Specific active client sets
        self.live_traffic_clients: Set[WebSocket] = set()
        self.statistics_clients: Set[WebSocket] = set()
        self.alerts_clients: Set[WebSocket] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Throttling live traffic broadcast to prevent flooding the client's browser
        self._last_live_broadcast = 0.0
        self._live_broadcast_interval = 1.0 / settings.LIVE_STREAM_FPS  # e.g. 1/30s = ~33ms

        # Background stats broadcaster state
        self._stats_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        self._loop = asyncio.get_running_loop()
        if channel == "live-traffic":
            self.live_traffic_clients.add(websocket)
            logger.info(f"Client connected to /ws/live-traffic. Total: {len(self.live_traffic_clients)}")
        elif channel == "statistics":
            self.statistics_clients.add(websocket)
            logger.info(f"Client connected to /ws/statistics. Total: {len(self.statistics_clients)}")
            # Ensure background broadcast loop is running
            self._start_stats_loop_if_needed()
        elif channel == "alerts":
            self.alerts_clients.add(websocket)
            logger.info(f"Client connected to /ws/alerts. Total: {len(self.alerts_clients)}")

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel == "live-traffic":
            self.live_traffic_clients.discard(websocket)
            logger.info(f"Client disconnected from /ws/live-traffic. Total: {len(self.live_traffic_clients)}")
        elif channel == "statistics":
            self.statistics_clients.discard(websocket)
            logger.info(f"Client disconnected from /ws/statistics. Total: {len(self.statistics_clients)}")
        elif channel == "alerts":
            self.alerts_clients.discard(websocket)
            logger.info(f"Client disconnected from /ws/alerts. Total: {len(self.alerts_clients)}")

    def broadcast_live_traffic(self, record: TrafficRecord):
        """
        Broadcasts parsed packets to `/ws/live-traffic` clients.
        Uses rate-limiting to avoid degrading client UI performance.
        """
        if not self.live_traffic_clients:
            return

        now = time.time()
        # Throttling check
        if now - self._last_live_broadcast < self._live_broadcast_interval:
            return
        
        self._last_live_broadcast = now

        payload = {
            "timestamp": record.timestamp.isoformat(),
            "source_ip": record.source_ip,
            "destination_ip": record.destination_ip,
            "source_port": record.source_port,
            "destination_port": record.destination_port,
            "protocol": record.protocol,
            "size": record.packet_size,
            "ttl": record.ttl,
            "mac_src": record.mac_src,
            "mac_dst": record.mac_dst,
            "domain": record.domain
        }
        
        # Schedule the task thread-safely on the active event loop
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._safe_broadcast(self.live_traffic_clients, payload),
                self._loop
            )

    async def broadcast_alert(self, alert: Alert):
        """Broadcasts security IDS alerts instantly to `/ws/alerts`"""
        if not self.alerts_clients:
            return

        payload = {
            "id": alert.id,
            "timestamp": alert.timestamp.isoformat(),
            "severity": alert.severity,
            "message": alert.message,
            "source_ip": alert.source_ip
        }
        await self._safe_broadcast(self.alerts_clients, payload)

    async def _safe_broadcast(self, clients: Set[WebSocket], message: dict):
        """Sends JSON messages to a set of sockets, discarding dead sockets gracefully."""
        if not clients:
            return
            
        json_msg = json.dumps(message)
        disconnected = []
        for client in clients:
            try:
                await client.send_text(json_msg)
            except Exception:
                disconnected.append(client)
                
        for client in disconnected:
            clients.discard(client)

    def _start_stats_loop_if_needed(self):
        """Start the background statistics broadcaster if it is not currently active."""
        if self._stats_task is None or self._stats_task.done():
            self._stats_task = asyncio.create_task(self._stats_broadcaster())
            logger.info("Background WebSocket statistics broadcaster loop started.")

    async def _stats_broadcaster(self):
        """Broadcasts real-time statistics aggregated by the StatsEngine once per second."""
        try:
            while self.statistics_clients:
                stats = global_stats_engine.get_stats()
                await self._safe_broadcast(self.statistics_clients, stats)
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("WebSocket statistics broadcaster loop stopped.")
            self._stats_task = None
