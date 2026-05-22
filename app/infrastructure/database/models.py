from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TrafficRecordModel(Base):
    __tablename__ = "traffic_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    source_ip = Column(String(45), nullable=False, index=True)
    destination_ip = Column(String(45), nullable=False, index=True)
    source_port = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String(15), nullable=False, index=True)
    packet_size = Column(Integer, nullable=False)
    ttl = Column(Integer, nullable=True)
    mac_src = Column(String(17), nullable=True)
    mac_dst = Column(String(17), nullable=True)
    domain = Column(String(255), nullable=True, index=True)
    payload_len = Column(Integer, nullable=True)

    # Composite indexes for high frequency dashboard queries
    __table_args__ = (
        Index("idx_src_dst_proto", "source_ip", "destination_ip", "protocol"),
    )

class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    severity = Column(String(20), nullable=False)
    message = Column(String(500), nullable=False)
    source_ip = Column(String(45), nullable=True, index=True)

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interface = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # "active", "stopped"
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)
