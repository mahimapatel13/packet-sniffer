import time
from datetime import datetime
from app.infrastructure.services.stats import StatisticsEngine
from app.domain.entities import TrafficRecord

def test_stats_aggregation():
    engine = StatisticsEngine(window_size_sec=5.0)
    
    # Create mock packet records
    r1 = TrafficRecord(
        timestamp=datetime.utcnow(),
        source_ip="192.168.1.10",
        destination_ip="8.8.8.8",
        source_port=55555,
        destination_port=53,
        protocol="DNS",
        packet_size=100
    )
    
    r2 = TrafficRecord(
        timestamp=datetime.utcnow(),
        source_ip="192.168.1.10",
        destination_ip="142.250.190.46",
        source_port=55556,
        destination_port=443,
        protocol="HTTPS",
        packet_size=1500
    )
    
    r3 = TrafficRecord(
        timestamp=datetime.utcnow(),
        source_ip="10.0.0.1",
        destination_ip="8.8.8.8",
        source_port=55555,
        destination_port=53,
        protocol="DNS",
        packet_size=100
    )

    # Feed packets
    engine.update(r1)
    engine.update(r2)
    engine.update(r3)

    # Assert aggregations
    assert engine.total_packets == 3
    assert engine.total_bytes == 1700
    
    dist = engine.get_protocol_distribution()
    assert dist["DNS"]["count"] == 2
    assert dist["DNS"]["percentage"] == 66.67
    assert dist["HTTPS"]["count"] == 1
    assert dist["HTTPS"]["percentage"] == 33.33

    # Assert Top IPs
    top_ips = engine.get_top_ips()
    assert top_ips["sources"][0]["ip"] == "192.168.1.10"
    assert top_ips["sources"][0]["count"] == 2
    assert top_ips["destinations"][0]["ip"] == "8.8.8.8"
    assert top_ips["destinations"][0]["count"] == 2

    # Assert Active connections count
    assert engine.get_active_connections_count() == 3

    # Fetch total stats summary
    stats = engine.get_stats()
    assert stats["total_packets"] == 3
    assert stats["total_bytes"] == 1700
