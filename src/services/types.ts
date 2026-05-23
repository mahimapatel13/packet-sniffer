export interface CaptureStartRequest {
  interface: string;
}

export interface GeoPointDTO {
  ip: string;
  country_code: string;
  country_name: string;
  city: string | null;
  latitude: number;
  longitude: number;
  count: number;
  direction: 'source' | 'destination';
}

export interface InterfaceDTO {
  name: string;
  description: string | null;
  ip_addresses: string[];
  mac_address: string | null;
  is_loopback: boolean;
  is_up: boolean;
}

export interface TrafficRecordDTO {
  id: number | null;
  timestamp: string; // ISO datetime string
  source_ip: string;
  destination_ip: string;
  source_port: number | null;
  destination_port: number | null;
  protocol: string;
  packet_size: number;
  ttl: number | null;
  mac_src: string | null;
  mac_dst: string | null;
  domain: string | null;
  payload_len: number | null;
}

export interface PagedTrafficHistory {
  total: number;
  page: number;
  limit: number;
  records: TrafficRecordDTO[];
}

export interface AlertDTO {
  id: number | null;
  timestamp: string; // ISO datetime string
  severity: "CRITICAL" | "WARNING" | "INFO";
  message: string;
  source_ip: string | null;
}

export interface SessionDTO {
  id: number;
  interface: string;
  status: "active" | "stopped";
  started_at: string;
  stopped_at: string | null;
}

export interface ProtocolStatItem {
  count: number;
  percentage: number;
}

export interface TopIPItem {
  ip: string;
  count: number;
}

export interface TopDomainItem {
  domain: string;
  count: number;
}

export interface StatsSummaryDTO {
  total_packets: number;
  total_bytes: number;
  packets_per_second: number;
  bandwidth_bytes_per_second: number;
  protocol_distribution: { [protocol: string]: ProtocolStatItem };
  top_source_ips: TopIPItem[];
  top_destination_ips: TopIPItem[];
  top_domains: TopDomainItem[];
  active_connections_count: number;
  timestamp: string;
  geo_points?: GeoPointDTO[];
}

export interface SystemHealthDTO {
  status: string;
  project: string;
  active_captures: {
    session_id: string;
    interface: string;
    is_active: boolean;
  }[];
}
