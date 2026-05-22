import threading
import socket
import uuid
import time
from typing import Dict, List, Callable, Optional
from scapy.all import conf, sniff
from domain.entities import InterfaceInfo, TrafficRecord
from core.logging import logger
from infrastructure.capture.parser import PacketParser

def resolve_interface(interface_name: str):
    """
    Resolves interface name/identifier to a valid Scapy interface.
    Handles 'default' fallback and unmatched friendly names gracefully.
    """
    if not interface_name or interface_name.lower() in ("default", "default socket interface"):
        logger.info(f"Resolving '{interface_name}' interface to Scapy default: {conf.iface}")
        return conf.iface

    try:
        # Try to find a match in conf.ifaces
        for iface_key, iface in conf.ifaces.items():
            if interface_name in (iface_key, iface.name, getattr(iface, "description", "")):
                return iface
    except Exception as e:
        logger.warning(f"Error matching interface '{interface_name}': {e}")

    # If the specified interface was not found, log a warning and fall back to conf.iface to avoid crashes
    logger.warning(f"Interface '{interface_name}' not found on the system. Falling back to default: {conf.iface}")
    return conf.iface

class CaptureSessionThread:
    """
    Manages a single background sniffing thread for a specific interface.
    """
    def __init__(self, session_id: str, interface: str, packet_callback: Callable[[TrafficRecord], None]):
        self.session_id = session_id
        self.interface = interface
        self._packet_callback = packet_callback
        self._stop_event = threading.Event()
        self._parser = PacketParser()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True, name=f"sniffer-{self.interface}")
        self._thread.start()
        logger.info(f"Capture thread started for session {self.session_id} on interface {self.interface}")

    def stop(self):
        logger.info(f"Signaling capture thread to stop for session {self.session_id}...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info(f"Capture thread stopped for session {self.session_id}")

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self):
        try:
            last_sent = 0

            resolved_iface = resolve_interface(self.interface)

            logger.info(
                f"Sniffing on resolved interface: {resolved_iface}"
            )

            def process_packet(packet):
                nonlocal last_sent

                if self._stop_event.is_set():
                    return

                record = self._parser.parse(packet)

                if record is None:
                    return

                now = time.time()

                # throttle websocket traffic only
                if now - last_sent >= (1 / 30):
                    last_sent = now

                self._packet_callback(record)

            sniff(
                iface=resolved_iface,
                prn=process_packet,
                store=False,
                stop_filter=lambda _: self._stop_event.is_set()
            )

        except Exception as e:
            logger.error(
                f"Error in sniffing session {self.session_id}: {e}"
            )
class CaptureEngine:
    """
    Singleton-like manager for discoverable interfaces and active multi-session capture threads.
    """
    def __init__(self):
        self._active_sessions: Dict[str, CaptureSessionThread] = {}
        self._lock = threading.Lock()

    def list_interfaces(self) -> List[InterfaceInfo]:
        """
        Dynamically detects physical and virtual interfaces using Scapy's underlying architecture.
        """
        interfaces: List[InterfaceInfo] = []
        try:
            # conf.ifaces lists all detected system interfaces
            for iface_key, iface in conf.ifaces.items():
                name = iface.name
                description = getattr(iface, "description", None) or getattr(iface, "mac", None) or name
                mac = getattr(iface, "mac", None)
                
                # Extract IPs safely
                ips = []
                if getattr(iface, "ip", None):
                    ips.append(str(iface.ip))
                if hasattr(iface, "ips") and iface.ips:
                    for family, ip_list in iface.ips.items():
                        for ip in ip_list:
                            ip_str = str(ip)
                            if ip_str not in ips:
                                ips.append(ip_str)

                # Determine if loopback
                is_loopback = False
                if "loop" in name.lower() or name.lower() == "lo" or any(isinstance(ip, str) and ip.startswith("127.") for ip in ips):
                    is_loopback = True

                interfaces.append(InterfaceInfo(
                    name=name,
                    description=description,
                    ip_addresses=ips,
                    mac_address=mac,
                    is_loopback=is_loopback,
                    is_up=True
                ))
        except Exception as e:
            logger.error(f"Error listing network interfaces: {e}")
            
            # Simple fallback using socket
            try:
                hostname = socket.gethostname()
                ips = [socket.gethostbyname(hostname)]
                interfaces.append(InterfaceInfo(
                    name="default",
                    description="Default Socket Interface",
                    ip_addresses=ips,
                    is_loopback=False,
                    is_up=True
                ))
            except Exception:
                pass

        return interfaces

    def start_session(self, interface: str, packet_callback: Callable[[TrafficRecord], None]) -> str:
        """
        Starts a new background capture thread on the specified interface.
        Returns the unique session ID.
        """
        with self._lock:
            # Check if there is already an active session on this interface
            for s_id, session in self._active_sessions.items():
                if session.interface == interface and session.is_alive():
                    logger.info(f"Re-using active sniffing session {s_id} for interface {interface}")
                    return s_id

            session_id = str(uuid.uuid4())
            session = CaptureSessionThread(session_id, interface, packet_callback)
            session.start()
            self._active_sessions[session_id] = session
            return session_id

    def stop_session(self, session_id: str) -> bool:
        """
        Stops an active sniffing session by ID.
        """
        with self._lock:
            if session_id in self._active_sessions:
                session = self._active_sessions.pop(session_id)
                session.stop()
                return True
            return False

    def stop_all_sessions(self):
        with self._lock:
            sessions_to_stop = list(self._active_sessions.values())
            self._active_sessions.clear()

        for session in sessions_to_stop:
            session.stop()
    def get_active_sessions(self) -> List[dict]:
        """
        Returns info of active sessions.
        """
        with self._lock:
            return [
                {"session_id": s_id, "interface": s.interface, "is_active": s.is_alive()}
                for s_id, s in self._active_sessions.items() if s.is_alive()
            ]
