import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from scapy.config import conf
from app.domain.entities import TrafficRecord, Alert, Session, InterfaceInfo
from app.domain.interfaces import ITrafficRepository, IAlertRepository, ISessionRepository
from app.infrastructure.capture.engine import CaptureEngine
from app.infrastructure.services.stats import global_stats_engine, StatisticsEngine
from app.infrastructure.services.db_writer import BatchDatabaseWriter
from app.infrastructure.services.ids import IDSEngine
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.database.repositories import TrafficRepository, AlertRepository, SessionRepository
from app.core.logging import logger

import psutil
import socket
from typing import List
from app.domain.entities import InterfaceInfo


class TrafficCoordinator:
    """
    Core orchestrator that coordinates between capture engine, database queues, 
    statistics counter, threat engine, and websocket broadcasters.
    """
    def __init__(self, capture_engine: CaptureEngine, stats_engine: StatisticsEngine, db_writer: BatchDatabaseWriter):
        self.capture_engine = capture_engine
        self.stats_engine = stats_engine
        self.db_writer = db_writer
        self.ids_engine = IDSEngine(alert_callback=self.handle_alert)
        self.websocket_manager = None  # Wires up in interfaces layer
        self._active_db_session_id: Optional[int] = None

    def handle_packet(self, record: TrafficRecord):
        """
        Callback executed by capture threads for every parsed packet.
        """

        self.stats_engine.update(record)

        self.ids_engine.detect(record)

        self.db_writer.enqueue(record)

        if self.websocket_manager:
            loop = self.db_writer._loop

            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.websocket_manager.broadcast_live_traffic(record),
                    loop
                )         
    def handle_alert(self, alert: Alert):
        """Callback from IDS when threat rules trigger."""
        loop = self.db_writer._loop
        if loop and loop.is_running():
            # Safely schedule the async save/broadcast from the sniffing OS thread to the async event loop
            asyncio.run_coroutine_threadsafe(self._persist_and_broadcast_alert(alert), loop)
        else:
            # Fallback if loop is stopped
            logger.warning(f"Could not persist alert asynchronously. Event loop is not running.")

    async def _persist_and_broadcast_alert(self, alert: Alert):
        try:
            # Persist alert
            async with async_session_factory() as session:
                repo = AlertRepository(session)
                saved_alert = await repo.save(alert)

            # Broadcast alert to /ws/alerts
            if self.websocket_manager:
                await self.websocket_manager.broadcast_alert(saved_alert)
        except Exception as e:
            logger.error(f"Error handling threat alert callback: {e}")

    async def cleanup_stale_sessions(self) -> None:
        """Resets any active sessions left over in the database from a crash or abrupt termination."""
        try:
            from sqlalchemy import update
            from app.infrastructure.database.models import SessionModel
            async with async_session_factory() as db:
                stmt = (
                    update(SessionModel)
                    .where(SessionModel.status == "active")
                    .values(status="stopped", stopped_at=datetime.utcnow())
                )
                await db.execute(stmt)
                await db.commit()
            logger.info("Stale database capture sessions cleaned successfully.")
        except Exception as e:
            logger.error(f"Failed to cleanup stale sessions: {e}")
    
    def list_interfaces(self) -> List[InterfaceInfo]:
        interfaces = []

        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()

            for name, addr_list in addrs.items():
                ips = []
                mac = None

                for addr in addr_list:
                    if addr.family == socket.AF_INET:
                        ips.append(addr.address)

                    elif addr.family == socket.AF_INET6:
                        ips.append(addr.address.split("%")[0])

                    elif str(addr.family) in ("-1", "17", "23"):
                        mac = addr.address

                iface_stat = stats.get(name)

                interfaces.append(
                    InterfaceInfo(
                        name=name,
                        description=name,
                        ip_addresses=ips,
                        mac_address=mac,
                        is_loopback=(
                            name.lower() == "lo"
                            or "loop" in name.lower()
                            or any(ip.startswith("127.") for ip in ips)
                        ),
                        is_up=iface_stat.isup if iface_stat else True
                    )
                )

        except Exception as e:
            logger.error(f"Interface detection failed: {e}")

        return interfaces
        interfaces: List[InterfaceInfo] = []
        seen_names: set = set()

        # Primary: Scapy conf.ifaces
        try:
            for iface_key, iface in conf.ifaces.items():
                name = iface.name
                if name in seen_names:
                    continue
                seen_names.add(name)
                description = getattr(iface, "description", None) or name
                mac = getattr(iface, "mac", None)
                ips = []
                if getattr(iface, "ip", None):
                    ips.append(str(iface.ip))
                if hasattr(iface, "ips") and iface.ips:
                    for family, ip_list in iface.ips.items():
                        for ip in ip_list:
                            ip_str = str(ip)
                            if ip_str not in ips:
                                ips.append(ip_str)
                is_loopback = (
                    "loop" in name.lower()
                    or name.lower() == "lo"
                    or any(isinstance(ip, str) and ip.startswith("127.") for ip in ips)
                )
                interfaces.append(InterfaceInfo(
                    name=name,
                    description=description,
                    ip_addresses=ips,
                    mac_address=mac,
                    is_loopback=is_loopback,
                    is_up=True
                ))
        except Exception as e:
            logger.warning(f"Scapy iface enumeration failed: {e}")

        # Fallback: psutil (always available since it's in requirements)
        if not interfaces:
            try:
                import psutil
                addrs = psutil.net_if_addrs()
                stats = psutil.net_if_stats()
                for name, addr_list in addrs.items():
                    if name in seen_names:
                        continue
                    seen_names.add(name)
                    ips = []
                    mac = None
                    import socket as _socket
                    for addr in addr_list:
                        if addr.family == _socket.AF_INET:
                            ips.append(addr.address)
                        elif addr.family == _socket.AF_INET6:
                            ips.append(addr.address.split("%")[0])
                        elif hasattr(_socket, "AF_PACKET") and addr.family == _socket.AF_PACKET:
                            mac = addr.address
                        elif addr.family == 23:  # AF_LINK on macOS/Windows
                            mac = addr.address
                    iface_stat = stats.get(name)
                    is_up = iface_stat.isup if iface_stat else True
                    is_loopback = (
                        name.lower() == "lo"
                        or "loop" in name.lower()
                        or any(ip.startswith("127.") for ip in ips)
                    )
                    interfaces.append(InterfaceInfo(
                        name=name,
                        description=name,
                        ip_addresses=ips,
                        mac_address=mac,
                        is_loopback=is_loopback,
                        is_up=is_up
                    ))
            except Exception as e:
                logger.error(f"psutil iface fallback also failed: {e}")

        if not interfaces:
            logger.error("No network interfaces detected by any method.")

        return interfaces

    async def start_capture(self, interface: str) -> dict:
        """Starts capture sessions, saving session metadata to the database."""
        # Check if already active in DB
        async with async_session_factory() as db:
            session_repo = SessionRepository(db)
            active_session = await session_repo.get_active()
            if active_session:
                logger.info(f"An active session {active_session.id} on {active_session.interface} already exists in DB.")
                # Ensure sniffing is running in engine
                session_id = self.capture_engine.start_session(active_session.interface, self.handle_packet)
                return {"message": "Sniffing already active", "session_id": session_id, "interface": active_session.interface}

        # Create session record in DB
        session_entity = Session(interface=interface, status="active")
        async with async_session_factory() as db:
            session_repo = SessionRepository(db)
            saved_session = await session_repo.create(session_entity)
            self._active_db_session_id = saved_session.id

        # Clear stats on new session start
        self.stats_engine.reset()

        # Start Scapy Sniffer
        session_id = self.capture_engine.start_session(interface, self.handle_packet)
        logger.info(f"Capture started on {interface}. Session ID: {session_id}")

        return {
            "message": "Sniffing started successfully",
            "session_id": session_id,
            "interface": interface
        }

    async def stop_capture(self) -> dict:
        """Stops all active capture threads and updates DB session states."""
        # Stop threads in the capture engine
        self.capture_engine.stop_all_sessions()

        # Update database session
        db_updated = False
        async with async_session_factory() as db:
            session_repo = SessionRepository(db)
            db_session = await session_repo.get_active()
            if db_session:
                db_session.status = "stopped"
                db_session.stopped_at = datetime.utcnow()
                await session_repo.update(db_session)
                self._active_db_session_id = None
                logger.info(f"Active DB session {db_session.id} marked stopped.")
                db_updated = True

        if db_updated:
            return {"message": "All capture sessions stopped and DB sessions finalized"}

        return {"message": "All capture sessions stopped successfully"}

    async def get_traffic_history(self, page: int, limit: int) -> dict:
        async with async_session_factory() as db:
            repo = TrafficRepository(db)
            records = await repo.get_history(page, limit)
            total = await repo.get_total_count()
            return {
                "total": total,
                "page": page,
                "limit": limit,
                "records": records
            }

    async def get_alerts_history(self, limit: int = 100) -> List[Alert]:
        async with async_session_factory() as db:
            repo = AlertRepository(db)
            return await repo.get_all(limit)


# Global coordinator instance
global_db_writer = BatchDatabaseWriter()
global_capture_engine = CaptureEngine()
global_coordinator = TrafficCoordinator(global_capture_engine, global_stats_engine, global_db_writer)
