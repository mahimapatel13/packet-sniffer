import time
import threading
from collections import deque, defaultdict
from typing import Dict, Set, List, Optional, Callable
from domain.entities import TrafficRecord, Alert
from core.config import settings
from core.logging import logger

class IDSEngine:
    """
    Intrusion Detection System (IDS) engine analyzing network flows in real-time.
    Provides rule-based heuristics for port scans, flooding, TCP SYN abuse, and spikes.
    """
    def __init__(self, alert_callback: Callable[[Alert], None]):
        self._lock = threading.Lock()
        self._alert_callback = alert_callback

        # 1. Port Scan Tracking: (src_ip, dst_ip) -> [(timestamp, port)]
        self._port_scans = defaultdict(deque)
        
        # 2. ICMP Flood Tracking: src_ip -> [timestamps]
        self._icmp_floods = defaultdict(deque)

        # 3. Excessive Request Tracking: src_ip -> [timestamps]
        self._ip_packet_rates = defaultdict(deque)

        # 4. TCP Half-Open / SYN Abuse: src_ip -> [timestamps of SYNs]
        # (Simplified: we track SYN-only packets to count half-open attempts)
        self._syn_attempts = defaultdict(deque)

        # 5. Traffic Spike Tracking: rolling window of global traffic sizes (timestamp, bytes)
        self._traffic_history = deque()
        self._last_spike_alert = 0.0

        # Rate-limiting alert triggers: (src_ip, alert_type) -> last_triggered_time
        # Prevents flooding the alert channel for the same issue
        self._alert_rate_limits = {}
        self._rate_limit_period = 30.0  # 30 seconds suppression per specific alert type/IP

    def detect(self, record: TrafficRecord) -> None:
        """
        Analyzes a network traffic record against security threat rules.
        """
        now = time.time()
        with self._lock:
            # Clean up ancient history periodically (every 100 packets processed)
            self._cleanup_outdated_data(now)

            # --- RULE 1: Global Bandwidth Traffic Spike ---
            self._traffic_history.append((now, record.packet_size))
            self._check_traffic_spikes(now)

            src_ip = record.source_ip
            dst_ip = record.destination_ip

            # --- RULE 2: Port Scanning ---
            if record.destination_port is not None:
                # Track this port access
                self._port_scans[(src_ip, dst_ip)].append((now, record.destination_port))
                self._check_port_scanning(src_ip, dst_ip, now)

            # --- RULE 3: ICMP Flood ---
            if record.protocol == "ICMP":
                self._icmp_floods[src_ip].append(now)
                self._check_icmp_flood(src_ip, now)

            # --- RULE 4: Excessive Requests / DDoS ---
            self._ip_packet_rates[src_ip].append(now)
            self._check_excessive_requests(src_ip, now)

            # --- RULE 5: Suspicious TCP SYN flood ---
            # Standard Scapy payload/flag checking or simplified based on TTL/protocol
            # Here we identify TCP SYN by checking if it's TCP with payload_len=0 (or check flags if raw,
            # but since we parse payload_len, we can also check if source_port is set)
            # In a robust scenario, we check standard packet flags. For simplicity and reliability:
            if record.protocol == "TCP" and record.payload_len == 0:
                # We assume empty TCP packets could be SYN/connection-probes
                self._syn_attempts[src_ip].append(now)
                self._check_syn_abuse(src_ip, now)

    def _cleanup_outdated_data(self, now: float) -> None:
        """Prunes historical data older than their respective inspection windows."""
        # 1. Port scan window (10 seconds)
        for key in list(self._port_scans.keys()):
            window = self._port_scans[key]
            while window and window[0][0] < now - settings.PORT_SCAN_WINDOW_SEC:
                window.popleft()
            if not window:
                del self._port_scans[key]

        # 2. ICMP window (1 second)
        for ip in list(self._icmp_floods.keys()):
            window = self._icmp_floods[ip]
            while window and window[0] < now - 1.0:
                window.popleft()
            if not window:
                del self._icmp_floods[ip]

        # 3. Excessive packet rates window (1 second)
        for ip in list(self._ip_packet_rates.keys()):
            window = self._ip_packet_rates[ip]
            while window and window[0] < now - 1.0:
                window.popleft()
            if not window:
                del self._ip_packet_rates[ip]

        # 4. SYN abuse window (10 seconds)
        for ip in list(self._syn_attempts.keys()):
            window = self._syn_attempts[ip]
            while window and window[0] < now - 10.0:
                window.popleft()
            if not window:
                del self._syn_attempts[ip]

        # 5. Global traffic window (60 seconds)
        while self._traffic_history and self._traffic_history[0][0] < now - 60.0:
            self._traffic_history.popleft()

    def _trigger_alert(self, severity: str, message: str, source_ip: Optional[str], alert_type: str, now: float):
        """Helper to rate-limit and broadcast alerts."""
        rate_key = (source_ip, alert_type)
        if rate_key in self._alert_rate_limits:
            if now - self._alert_rate_limits[rate_key] < self._rate_limit_period:
                return  # Suppressed

        self._alert_rate_limits[rate_key] = now
        alert = Alert(
            severity=severity,
            message=message,
            source_ip=source_ip
        )
        logger.warning(f"[IDS ALERT - {severity.upper()}]: {message} from {source_ip}")
        # Call the orchestrator callback (saves to DB + broadcasts to WS)
        self._alert_callback(alert)

    def _check_port_scanning(self, src_ip: str, dst_ip: str, now: float):
        window = self._port_scans[(src_ip, dst_ip)]
        # Count unique ports in the window
        unique_ports = {port for _, port in window}
        if len(unique_ports) >= settings.PORT_SCAN_THRESHOLD:
            self._trigger_alert(
                severity="high",
                message=f"Possible port scanning detected: scanned {len(unique_ports)} unique ports on host {dst_ip}",
                source_ip=src_ip,
                alert_type="PORT_SCAN",
                now=now
            )

    def _check_icmp_flood(self, src_ip: str, now: float):
        window = self._icmp_floods[src_ip]
        if len(window) >= settings.ICMP_FLOOD_THRESHOLD:
            self._trigger_alert(
                severity="high",
                message=f"ICMP flood detected: {len(window)} pings/sec",
                source_ip=src_ip,
                alert_type="ICMP_FLOOD",
                now=now
            )

    def _check_excessive_requests(self, src_ip: str, now: float):
        window = self._ip_packet_rates[src_ip]
        if len(window) >= settings.EXCESSIVE_REQUESTS_THRESHOLD:
            self._trigger_alert(
                severity="medium",
                message=f"Excessive requests: high packet rate ({len(window)} packets/sec)",
                source_ip=src_ip,
                alert_type="EXCESSIVE_REQUESTS",
                now=now
            )

    def _check_syn_abuse(self, src_ip: str, now: float):
        window = self._syn_attempts[src_ip]
        # > 50 SYN attempts in 10 seconds without payload (connection scanning or SYN flood)
        if len(window) >= 50:
            self._trigger_alert(
                severity="medium",
                message=f"Suspicious TCP SYN activity detected: {len(window)} connection handshakes attempted in 10s",
                source_ip=src_ip,
                alert_type="SYN_FLOOD",
                now=now
            )

    def _check_traffic_spikes(self, now: float):
        # We need a baseline of at least 5 seconds of data to detect a spike
        if not self._traffic_history or now - self._traffic_history[0][0] < 5.0:
            return

        # Calculate bandwidth in the last 2 seconds vs average bandwidth in the last 60 seconds
        recent_boundary = now - 2.0
        recent_bytes = sum(size for ts, size in self._traffic_history if ts >= recent_boundary)
        recent_rate = recent_bytes / 2.0

        total_bytes_60 = sum(size for _, size in self._traffic_history)
        total_time_60 = now - self._traffic_history[0][0]
        avg_rate = total_bytes_60 / total_time_60

        # Threshold check: Rate must be substantial (at least 50 KB/s to avoid alerting on tiny quiet networks)
        if avg_rate > 50000 and recent_rate > avg_rate * settings.SUSPICIOUS_SPIKE_MULTIPLE:
            # Spike detected
            if now - self._last_spike_alert > self._rate_limit_period:
                self._last_spike_alert = now
                alert = Alert(
                    severity="low",
                    message=f"Suspicious traffic spike: current rate ({round(recent_rate/1024, 1)} KB/s) is {round(recent_rate/avg_rate, 1)}x higher than average baseline",
                    source_ip=None
                )
                logger.warning(f"[IDS ALERT - LOW]: {alert.message}")
                self._alert_callback(alert)
