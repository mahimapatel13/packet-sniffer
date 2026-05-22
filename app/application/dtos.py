from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class CaptureStartRequest(BaseModel):
    interface: str = Field(..., description="Name of the interface to capture traffic from (e.g. 'Wi-Fi', 'Ethernet')")

class InterfaceDTO(BaseModel):
    name: str
    description: Optional[str] = None
    ip_addresses: List[str] = []
    mac_address: Optional[str] = None
    is_loopback: bool
    is_up: bool

class TrafficRecordDTO(BaseModel):
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

class PagedTrafficHistory(BaseModel):
    total: int
    page: int
    limit: int
    records: List[TrafficRecordDTO]

class AlertDTO(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    severity: str
    message: str
    source_ip: Optional[str] = None

class SessionDTO(BaseModel):
    id: int
    interface: str
    status: str
    started_at: datetime
    stopped_at: Optional[datetime] = None

class ProtocolStatItem(BaseModel):
    count: int
    percentage: float

class TopIPItem(BaseModel):
    ip: str
    count: int

class TopDomainItem(BaseModel):
    domain: str
    count: int

class StatsSummaryDTO(BaseModel):
    total_packets: int
    total_bytes: int
    packets_per_second: float
    bandwidth_bytes_per_second: float
    protocol_distribution: Dict[str, ProtocolStatItem]
    top_source_ips: List[TopIPItem]
    top_destination_ips: List[TopIPItem]
    top_domains: List[TopDomainItem]
    active_connections_count: int
    timestamp: str
