import { 
  AlertDTO, 
  CaptureStartRequest, 
  InterfaceDTO, 
  ProtocolStatItem, 
  StatsSummaryDTO, 
  TrafficRecordDTO,
  SystemHealthDTO
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

export async function getHealth(): Promise<SystemHealthDTO> {
  const res = await fetch(`${BASE_URL}/`);
  return res.json();
}

export async function getInterfaces(): Promise<InterfaceDTO[]> {
  const res = await fetch(`${BASE_URL}/capture/interfaces`);
  return res.json();
}

export async function startCapture(config: CaptureStartRequest): Promise<{ message: string; session_id: string; interface: string }> {
  const res = await fetch(`${BASE_URL}/capture/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  return res.json();
}

export async function stopCapture(): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/capture/stop`, { method: "POST" });
  return res.json();
}

export async function getStatistics(): Promise<StatsSummaryDTO> {
  const res = await fetch(`${BASE_URL}/statistics`);
  return res.json();
}

export async function getProtocols(): Promise<Record<string, ProtocolStatItem>> {
  const res = await fetch(`${BASE_URL}/protocols`);
  return res.json();
}

export async function getTopIps(limit = 5): Promise<{ sources: any[]; destinations: any[] }> {
  const res = await fetch(`${BASE_URL}/top-ips?limit=${limit}`);
  return res.json();
}

export async function getTopDomains(limit = 5): Promise<any[]> {
  const res = await fetch(`${BASE_URL}/top-domains?limit=${limit}`);
  return res.json();
}

export async function getAlerts(limit = 100): Promise<AlertDTO[]> {
  const res = await fetch(`${BASE_URL}/alerts?limit=${limit}`);
  return res.json();
}

export async function getLiveTraffic(limit = 50): Promise<TrafficRecordDTO[]> {
  const res = await fetch(`${BASE_URL}/traffic/live?limit=${limit}`);
  return res.json();
}

// ---- WebSocket Subscriptions ----

function createWebSocket<T>(path: string, onMessage: (data: T) => void) {
  const socket = new WebSocket(`${WS_BASE_URL}${path}`);
  
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (err) {
      console.error(`Error parsing WS message from ${path}:`, err);
    }
  };

  socket.onerror = (err) => {
    console.error(`WS error on ${path}:`, err);
  };

  return () => {
    if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
      socket.close();
    }
  };
}

export function subscribeLivePackets(cb: (p: Packet) => void) {
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
      status: "ok", // Backend doesn't provide status directly in live feed yet
    });
  });
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
