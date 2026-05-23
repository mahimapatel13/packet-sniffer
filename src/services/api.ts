import { 
  AlertDTO, 
  CaptureStartRequest, 
  InterfaceDTO, 
  ProtocolStatItem, 
  StatsSummaryDTO, 
  TrafficRecordDTO,
  SystemHealthDTO,
  GeoPointDTO
} from "./types";

const BASE_URL = "http://localhost:8000";
const WS_BASE_URL = "ws://localhost:8000";

// --- Existing Types (kept for compatibility where possible) ---
export type Statistics = {
  totalPackets: number;
  activeConnections: number;
  bandwidthMbps: number;
  threatAlerts: number;
  trend: { packets: number; connections: number; bandwidth: number; threats: number };
  series: { t: string; v: number }[];
};

export type Protocol = { name: string; share: number };
export type SourceIp = { ip: string; packets: number };
export type Alert = {
  id: string;
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  timestamp: number;
};

export type Packet = {
  id: string;
  time: number;
  src: string;
  dst: string;
  protocol: string;
  size: number;
  port: number;
  domain: string;
  status: "ok" | "suspicious" | "blocked";
};

// --- API Implementation ---
async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error ${res.status}: ${errorText}`);
  }
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<SystemHealthDTO> {
  return apiFetch<SystemHealthDTO>(`${BASE_URL}/`);
}

export async function getInterfaces(): Promise<InterfaceDTO[]> {
  return apiFetch<InterfaceDTO[]>(`${BASE_URL}/capture/interfaces`);
}

export async function startCapture(config: CaptureStartRequest): Promise<{ message: string; session_id: string; interface: string }> {
  return apiFetch(`${BASE_URL}/capture/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
}

export async function stopCapture(): Promise<{ message: string }> {
  return apiFetch(`${BASE_URL}/capture/stop`, { method: "POST" });
}

export async function getStatistics(): Promise<StatsSummaryDTO> {
  return apiFetch<StatsSummaryDTO>(`${BASE_URL}/statistics`);
}

export async function getProtocols(): Promise<Record<string, ProtocolStatItem>> {
  return apiFetch<Record<string, ProtocolStatItem>>(`${BASE_URL}/protocols`);
}



export async function getAlerts(limit = 100): Promise<AlertDTO[]> {
  return apiFetch<AlertDTO[]>(`${BASE_URL}/alerts?limit=${limit}`);
}

export async function getLiveTraffic(limit = 50): Promise<TrafficRecordDTO[]> {
  return apiFetch<TrafficRecordDTO[]>(`${BASE_URL}/traffic/live?limit=${limit}`);
}

export async function getTopIps(limit = 5): Promise<{ sources: any[]; destinations: any[] }> {
  const res = await fetch(`${BASE_URL}/top-ips?limit=${limit}`);
  return res.json();
}

export async function getTopDomains(limit = 5): Promise<any[]> {
  const res = await fetch(`${BASE_URL}/top-domains?limit=${limit}`);
  return res.json();
}

export async function getGeoPoints(limit = 100): Promise<GeoPointDTO[]> {
  return apiFetch<GeoPointDTO[]>(`${BASE_URL}/geo-points?limit=${limit}`);
}

// ---- WebSocket Subscriptions ----

function createWebSocket<T>(
  path: string,
  onMessage: (data: T) => void,
  onClose?: () => void
) {
  const socket = new WebSocket(`${WS_BASE_URL}${path}`);

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as T;
      onMessage(data);
    } catch (err) {
      console.error(`Error parsing WS message from ${path}:`, err);
    }
  };

  socket.onerror = (err) => {
    console.error(`WS error on ${path}:`, err);
  };

  socket.onclose = () => {
    onClose?.();
  };

  return () => {
    socket.onclose = null; // prevent reconnect on intentional close
    if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
      socket.close();
    }
  };
}

export function subscribeLivePackets(cb: (p: Packet) => void, onClose?: () => void) {
  return createWebSocket<TrafficRecordDTO>("/ws/live-traffic", (record) => {
    cb({
      id: `${record.timestamp}-${Math.random()}`,
      time: new Date(record.timestamp).getTime(),
      src: record.source_ip,
      dst: record.destination_ip,
      protocol: record.protocol,
      size: record.packet_size,
      port: record.destination_port || 0,
      domain: record.domain || "",
      status: "ok",
    });
  }, onClose);
}

export function subscribeStatistics(cb: (stats: StatsSummaryDTO) => void) {
  return createWebSocket<StatsSummaryDTO>("/ws/statistics", cb);
}

export function subscribeAlerts(cb: (alert: AlertDTO) => void) {
  return createWebSocket<AlertDTO>("/ws/alerts", cb);
}

// ---- Legacy/Compatibility Stubs (to be replaced in components) ----

export type GraphNode = {
  id: string;
  label: string;
  kind: "source" | "destination" | "domain" | "host";
  protocol: string;
  packets: number;
  bandwidthMbps: number;
};
export type GraphEdge = { source: string; target: string; weight: number };
export type GraphData = { nodes: GraphNode[]; edges: GraphEdge[] };

export async function getGraph(): Promise<GraphData> {
  const stats = await getStatistics();

  const nodes: GraphNode[] = [
    {
      id: "host",
      label: "Host",
      kind: "host",
      protocol: "",
      packets: 0,
      bandwidthMbps: 0,
    },
  ];

  const edges: GraphEdge[] = [];

  // Source IPs
  stats.top_source_ips.forEach((item) => {
    nodes.push({
      id: `src-${item.ip}`,
      label: item.ip,
      kind: "source",
      protocol: "TCP",
      packets: item.count,
      bandwidthMbps: item.count / 100,
    });

    edges.push({
      source: `src-${item.ip}`,
      target: "host",
      weight: item.count,
    });
  });

  // Destination domains
  stats.top_domains.forEach((item) => {
    nodes.push({
      id: `dom-${item.domain}`,
      label: item.domain,
      kind: "domain",
      protocol: "DNS",
      packets: item.count,
      bandwidthMbps: item.count / 100,
    });

    edges.push({
      source: "host",
      target: `dom-${item.domain}`,
      weight: item.count,
    });
  });

  return {
    nodes,
    edges,
  };
}


export async function getLivePackets(): Promise<Packet[]> {
  const records = await getLiveTraffic(20);
  return records.map(record => ({
    id: `${record.timestamp}-${Math.random()}`,
    time: new Date(record.timestamp).getTime(),
    src: record.source_ip,
    dst: record.destination_ip,
    protocol: record.protocol,
    size: record.packet_size,
    port: record.destination_port || 0,
    domain: record.domain || "",
    status: "ok",
  }));
}
