import time
import threading
from datetime import datetime
from collections import Counter, deque
from typing import Dict, Any, List, Tuple
from domain.entities import TrafficRecord
from core.logging import logger

class StatisticsEngine:
    """
    In-Memory, thread-safe statistics engine that aggregates traffic metrics.
    Operates with sliding windows for real-time traffic rate estimates.
    """
    def __init__(self, window_size_sec: float = 10.0):
        self._lock = threading.Lock()
        self._window_size_sec = window_size_sec

        # Core Accumulators
        self.total_packets = 0
        self.total_bytes = 0

        # Protocol Metrics
        self.protocol_counts = Counter()

        # IP and Domain Counters
        self.source_ip_counts = Counter()
        self.dest_ip_counts = Counter()
        self.domain_counts = Counter()

        # Sliding Window for Rates (timestamp, size_bytes)
        self._packet_window = deque()

        # Active Connections: (source_ip, source_port, dest_ip, dest_port, protocol) -> last_seen_timestamp
        self.active_connections: Dict[Tuple[str, int, str, int, str], float] = {}

    def update(self, record: TrafficRecord) -> None:
        """
        Updates internal metrics with a newly captured packet record.
        Designed to be thread-safe for sniffer callback invocation.
        """
        now = time.time()
        with self._lock:
            self.total_packets += 1
            self.total_bytes += record.packet_size

            # Update protocols
            self.protocol_counts[record.protocol] += 1

            # Update IP distribution
            self.source_ip_counts[record.source_ip] += 1
            self.dest_ip_counts[record.destination_ip] += 1
            if record.domain:
                self.domain_counts[record.domain] += 1

            # Push to sliding window for traffic rates
            self._packet_window.append((now, record.packet_size))

            # Maintain active connection tracking
            if record.source_port is not None and record.destination_port is not None:
                # Flow tuple (Src IP, Src Port, Dst IP, Dst Port, Protocol)
                flow = (record.source_ip, record.source_port, record.destination_ip, record.destination_port, record.protocol)
                self.active_connections[flow] = now

    def _cleanup_window_and_connections(self, now: float) -> None:
        """Cleans up expired sliding window records and inactive connections (older than 60s)."""
        # 1. Clean window for rates
        boundary = now - self._window_size_sec
        while self._packet_window and self._packet_window[0][0] < boundary:
            self._packet_window.popleft()

        # 2. Clean connections (inactive for more than 60 seconds)
        conn_expiry = now - 60.0
        expired_flows = [flow for flow, last_seen in self.active_connections.items() if last_seen < conn_expiry]
        for flow in expired_flows:
            self.active_connections.pop(flow, None)

    def get_packets_per_second(self) -> float:
        """Calculates current packets/sec using the sliding window."""
        now = time.time()
        with self._lock:
            self._cleanup_window_and_connections(now)
            count = len(self._packet_window)
            return round(count / self._window_size_sec, 2)

    def get_bytes_per_second(self) -> float:
        """Calculates current bandwidth bytes/sec using the sliding window."""
        now = time.time()
        with self._lock:
            self._cleanup_window_and_connections(now)
            total_window_bytes = sum(size for _, size in self._packet_window)
            return round(total_window_bytes / self._window_size_sec, 2)

    def get_top_ips(self, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Returns the most active source and destination IPs."""
        with self._lock:
            top_sources = [
                {"ip": ip, "count": count} for ip, count in self.source_ip_counts.most_common(limit)
            ]
            top_dests = [
                {"ip": ip, "count": count} for ip, count in self.dest_ip_counts.most_common(limit)
            ]
            return {
                "sources": top_sources,
                "destinations": top_dests
            }

    def get_top_domains(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns the most requested domain names."""
        with self._lock:
            return [
                {"domain": domain, "count": count}
                for domain, count in self.domain_counts.most_common(limit)
            ]

    def get_protocol_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Returns distribution count and percentage per protocol."""
        with self._lock:
            total = self.total_packets or 1
            dist = {}
            for proto, count in self.protocol_counts.items():
                dist[proto] = {
                    "count": count,
                    "percentage": round((count / total) * 100, 2)
                }
            return dist

    def get_active_connections_count(self) -> int:
        """Returns total active unique flows in the last 60 seconds."""
        now = time.time()
        with self._lock:
            self._cleanup_window_and_connections(now)
            return len(self.active_connections)

    def get_active_connections(self) -> List[Dict[str, Any]]:
        """Returns list of all active connection flows."""
        now = time.time()
        with self._lock:
            self._cleanup_window_and_connections(now)
            connections = []
            for flow, last_seen in self.active_connections.items():
                src_ip, src_port, dst_ip, dst_port, protocol = flow
                connections.append({
                    "source_ip": src_ip,
                    "source_port": src_port,
                    "destination_ip": dst_ip,
                    "destination_port": dst_port,
                    "protocol": protocol,
                    "last_active": round(now - last_seen, 1)
                })
            return connections

    def get_stats(self) -> Dict[str, Any]:
        """
        Compiles a comprehensive summary of all tracked real-time statistics.
        """
        now = time.time()
        with self._lock:
            self._cleanup_window_and_connections(now)
            
            # Protocols
            protocols = {}
            total = self.total_packets or 1
            for proto, count in self.protocol_counts.items():
                protocols[proto] = {
                    "count": count,
                    "percentage": round((count / total) * 100, 2)
                }

            # Top IPs and Domains
            top_src = [{"ip": ip, "count": count} for ip, count in self.source_ip_counts.most_common(5)]
            top_dst = [{"ip": ip, "count": count} for ip, count in self.dest_ip_counts.most_common(5)]
            top_dom = [{"domain": dom, "count": count} for dom, count in self.domain_counts.most_common(5)]

            # Bandwidth and rate estimation
            total_window_bytes = sum(size for _, size in self._packet_window)
            bytes_sec = round(total_window_bytes / self._window_size_sec, 2)
            packets_sec = round(len(self._packet_window) / self._window_size_sec, 2)

            return {
                "total_packets": self.total_packets,
                "total_bytes": self.total_bytes,
                "packets_per_second": packets_sec,
                "bandwidth_bytes_per_second": bytes_sec,
                "protocol_distribution": protocols,
                "top_source_ips": top_src,
                "top_destination_ips": top_dst,
                "top_domains": top_dom,
                "active_connections_count": len(self.active_connections),
                "timestamp": datetime.utcnow().isoformat()
            }

    def reset(self) -> None:
        """Resets all metrics (e.g., when dynamic capture is started fresh)."""
        with self._lock:
            self.total_packets = 0
            self.total_bytes = 0
            self.protocol_counts.clear()
            self.source_ip_counts.clear()
            self.dest_ip_counts.clear()
            self.domain_counts.clear()
            self._packet_window.clear()
            self.active_connections.clear()
            logger.info("Statistics engine has been reset.")
global_stats_engine = StatisticsEngine()
