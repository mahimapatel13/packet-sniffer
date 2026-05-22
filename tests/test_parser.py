import pytest
from scapy.all import IP, TCP, UDP, ARP, DNS, Ether
from app.infrastructure.capture.parser import PacketParser
from app.domain.entities import TrafficRecord

def test_parse_tcp_http_packet():
    parser = PacketParser()
    
    # Construct an in-memory Scapy TCP packet to simulate HTTP GET
    packet = (
        Ether(src="00:11:22:33:44:55", dst="66:77:88:99:aa:bb") /
        IP(src="192.168.1.100", dst="142.250.190.46", ttl=64) /
        TCP(sport=54321, dport=80) /
        b"GET /index.html HTTP/1.1\r\nHost: google.com\r\n\r\n"
    )
    
    record = parser.parse(packet)
    
    assert record is not None
    assert record.source_ip == "192.168.1.100"
    assert record.destination_ip == "142.250.190.46"
    assert record.source_port == 54321
    assert record.destination_port == 80
    assert record.protocol == "HTTP"  # Should identify HTTP from payload
    assert record.mac_src == "00:11:22:33:44:55"
    assert record.mac_dst == "66:77:88:99:aa:bb"
    assert record.ttl == 64
    assert record.payload_len > 0

def test_parse_udp_dns_packet():
    parser = PacketParser()
    
    # Construct an in-memory Scapy DNS packet
    packet = (
        Ether() /
        IP(src="8.8.8.8", dst="192.168.1.100") /
        UDP(sport=53, dport=54321) /
        DNS(qr=1, ancount=0)
    )
    
    record = parser.parse(packet)
    
    assert record is not None
    assert record.source_ip == "8.8.8.8"
    assert record.destination_ip == "192.168.1.100"
    assert record.source_port == 53
    assert record.destination_port == 54321
    assert record.protocol == "DNS"

def test_parse_arp_packet():
    parser = PacketParser()
    
    # Construct an in-memory Scapy ARP packet
    packet = (
        Ether() /
        ARP(psrc="192.168.1.1", pdst="192.168.1.5")
    )
    
    record = parser.parse(packet)
    
    assert record is not None
    assert record.source_ip == "192.168.1.1"
    assert record.destination_ip == "192.168.1.5"
    assert record.protocol == "ARP"
