import time
from datetime import datetime
from infrastructure.services.ids import IDSEngine
from domain.entities import TrafficRecord, Alert
from core.config import settings

def test_ids_icmp_flood():
    alerts_triggered = []
    
    def mock_alert_callback(alert: Alert):
        alerts_triggered.append(alert)

    # Initialize IDS Engine with high-rate flood callback
    engine = IDSEngine(alert_callback=mock_alert_callback)
    
    # Configure threshold for speed (e.g. override to 10 for test simplicity or use default 100)
    # Let's override settings temporarily
    old_threshold = settings.ICMP_FLOOD_THRESHOLD
    settings.ICMP_FLOOD_THRESHOLD = 5
    
    try:
        now = datetime.utcnow()
        # Feed 6 ICMP packets from same source
        for _ in range(6):
            r = TrafficRecord(
                timestamp=now,
                source_ip="192.168.1.55",
                destination_ip="8.8.8.8",
                protocol="ICMP",
                packet_size=64
            )
            engine.detect(r)

        assert len(alerts_triggered) >= 1
        alert = alerts_triggered[0]
        assert alert.severity == "high"
        assert "ICMP flood" in alert.message
        assert alert.source_ip == "192.168.1.55"
        
    finally:
        # Restore settings
        settings.ICMP_FLOOD_THRESHOLD = old_threshold

def test_ids_port_scan():
    alerts_triggered = []
    
    def mock_alert_callback(alert: Alert):
        alerts_triggered.append(alert)

    engine = IDSEngine(alert_callback=mock_alert_callback)
    
    # Override settings
    old_threshold = settings.PORT_SCAN_THRESHOLD
    settings.PORT_SCAN_THRESHOLD = 5
    
    try:
        now = datetime.utcnow()
        # Feed TCP packets targeting 6 unique ports on the same host
        for port in range(1, 7):
            r = TrafficRecord(
                timestamp=now,
                source_ip="10.0.0.9",
                destination_ip="10.0.0.1",
                source_port=55555,
                destination_port=port,
                protocol="TCP",
                packet_size=40
            )
            engine.detect(r)

        assert len(alerts_triggered) >= 1
        alert = alerts_triggered[0]
        assert alert.severity == "high"
        assert "port scanning" in alert.message
        assert alert.source_ip == "10.0.0.9"

    finally:
        settings.PORT_SCAN_THRESHOLD = old_threshold
