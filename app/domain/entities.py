from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TrafficRecord(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    source_ip: str
    destination_ip: str
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: str
    packet_size: int
    ttl: Optional[int] = None
    mac_src: Optional[str] = None
    mac_dst: Optional[str] = None
    domain: Optional[str] = None
    payload_len: Optional[int] = None

    model_config = {
        "from_attributes": True
    }

class Alert(BaseModel):
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: str  # "low", "medium", "high"
    message: str
    source_ip: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class Session(BaseModel):
    id: Optional[int] = None
    interface: str
    status: str  # "active", "stopped"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    stopped_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class InterfaceInfo(BaseModel):
    name: str
    description: Optional[str] = None
    ip_addresses: list[str] = []
    mac_address: Optional[str] = None
    is_loopback: bool = False
    is_up: bool = True
