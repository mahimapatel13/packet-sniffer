import socket
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict
from scapy.all import Packet, IP, IPv6, TCP, UDP, ICMP, ARP, DNS, Ether
from domain.entities import TrafficRecord
from core.logging import logger

class DNSResolver:

    def __init__(self,max_workers:int=10):
        self._cache={}
        self._executor=ThreadPoolExecutor(
            max_workers=max_workers
        )
        self._pending_ips=set()

    def shutdown(self):
        self._executor.shutdown(
            wait=False,
            cancel_futures=True
        )
class PacketParser:
    def __init__(self):
        self.resolver = DNSResolver()

    def parse(self, packet: Packet) -> Optional[TrafficRecord]:
        """
        Parses a Scapy packet into a Domain TrafficRecord entity.
        Returns None if the packet is not relevant or unparseable.
        """
        try:
            timestamp = datetime.fromtimestamp(packet.time) if hasattr(packet, "time") else datetime.utcnow()
            packet_size = len(packet)

            # Initialize base fields
            src_ip = "0.0.0.0"
            dst_ip = "0.0.0.0"
            src_port = None
            dst_port = None
            proto_str = "Unknown"
            ttl = None
            mac_src = None
            mac_dst = None
            payload_len = 0

            # 1. Parse MAC Addresses if Ether layer exists
            if packet.haslayer(Ether):
                mac_src = packet[Ether].src
                mac_dst = packet[Ether].dst

            # 2. Parse Network Layer (L3)
            if packet.haslayer(IP):
                ip_layer = packet[IP]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
                ttl = ip_layer.ttl
                proto_num = ip_layer.proto
                proto_str = self._resolve_proto_num(proto_num)
            elif packet.haslayer(IPv6):
                ipv6_layer = packet[IPv6]
                src_ip = ipv6_layer.src
                dst_ip = ipv6_layer.dst
                ttl = ipv6_layer.hlim
                # IPv6 Next Header
                proto_str = self._resolve_proto_num(ipv6_layer.nh)
            elif packet.haslayer(ARP):
                arp_layer = packet[ARP]
                src_ip = arp_layer.psrc
                dst_ip = arp_layer.pdst
                proto_str = "ARP"
            else:
                # Non-IP packet (e.g. Layer 2 frames)
                return None

            # 3. Parse Transport Layer (L4)
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                proto_str = "TCP"
                if tcp_layer.payload:
                    payload_len = len(tcp_layer.payload)
                
                # Check for HTTP or HTTPS application layers
                payload_raw = bytes(tcp_layer.payload)
                if dst_port == 80 or src_port == 80 or payload_raw.startswith((b"GET ", b"POST ", b"HTTP/")):
                    proto_str = "HTTP"
                elif dst_port == 443 or src_port == 443 or payload_raw.startswith(b"\x16\x03"): # 0x16 0x03 is SSL/TLS Handshake
                    proto_str = "HTTPS"

            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
                proto_str = "UDP"
                if udp_layer.payload:
                    payload_len = len(udp_layer.payload)

                # Check for DNS
                if packet.haslayer(DNS):
                    proto_str = "DNS"
                    self._extract_dns_mapping(packet[DNS])

            elif packet.haslayer(ICMP):
                proto_str = "ICMP"

            # 4. Resolve domain name for destination IP using async resolver
            domain = self.resolver.get_domain(dst_ip)

            return TrafficRecord(
                timestamp=timestamp,
                source_ip=src_ip,
                destination_ip=dst_ip,
                source_port=src_port,
                destination_port=dst_port,
                protocol=proto_str,
                packet_size=packet_size,
                ttl=ttl,
                mac_src=mac_src,
                mac_dst=mac_dst,
                domain=domain,
                payload_len=payload_len
            )

        except Exception as e:
            # Silently catch anomalies to avoid crashing the sniffer loop
            return None

    def _resolve_proto_num(self, proto_num: int) -> str:
        """Converts raw IP protocol numbers to string representation"""
        protocols = {
            1: "ICMP",
            2: "IGMP",
            6: "TCP",
            17: "UDP",
            41: "IPv6-Route",
            58: "ICMPv6",
            112: "VRRP"
        }
        return protocols.get(proto_num, f"Proto-{proto_num}")

    def _extract_dns_mapping(self, dns_layer: DNS):
        """Optimizes resolving by extracting IP-to-Domain mappings directly from sniffed DNS responses"""
        try:
            # Query type response (qr == 1 is response)
            if dns_layer.qr == 1 and dns_layer.an:
                for i in range(dns_layer.ancount):
                    answer = dns_layer.an[i]
                    # Check if standard A or AAAA type records (type 1 = A, type 28 = AAAA)
                    if answer.type in (1, 28):
                        domain = answer.rrname.decode("utf-8", errors="ignore")
                        ip = answer.rdata
                        if isinstance(ip, str):
                            self.resolver.add_to_cache(ip, domain)
        except Exception:
            pass
