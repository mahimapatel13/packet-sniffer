# 📡 Network Traffic Analyzer: API Routes & DTO Specifications

This document defines the raw HTTP REST endpoints, WebSocket channels, and data transfer object (DTO) models exposed by the FastAPI backend.

**Base URL**: `http://localhost:8000` (or `ws://localhost:8000` for WebSockets)

---

## 🧭 1. HTTP REST API Reference

### 🏥 System Health & active captures
#### `GET /`
* **Description**: Returns server health status and dynamic capture engine sessions.
* **Response Body**:
  ```json
  {
    "status": "string",
    "project": "string",
    "active_captures": [
      {
        "session_id": "string (UUID)",
        "interface": "string",
        "is_active": "boolean"
      }
    ]
  }
  ```

---

### 🕹️ Sniffing & Capture Management
#### `GET /capture/interfaces`
* **Description**: Returns all physical/virtual network interfaces detected on the host machine.
* **Response Body**: `Array<InterfaceDTO>`

#### `POST /capture/start`
* **Description**: Initiates live packet capture on a chosen interface. Resets in-memory telemetry stats.
* **Request Body**: `CaptureStartRequest`
* **Response Body**:
  ```json
  {
    "message": "string",
    "session_id": "string (UUID)",
    "interface": "string"
  }
  ```

#### `POST /capture/stop`
* **Description**: Safely stops packet capturing threads across all adapters. Saves session states to the database.
* **Response Body**:
  ```json
  {
    "message": "string"
  }
  ```

---

### 📋 Database Traffic Logs
#### `GET /traffic/live`
* **Description**: Fetches the most recently captured packet database logs.
* **Query Parameters**:
  * `limit` (Optional, default `50`): Size limit (`1` to `200`) of logs to fetch.
* **Response Body**: `Array<TrafficRecordDTO>`

#### `GET /traffic/history`
* **Description**: Fetches the historical log database using cursor offset pagination.
* **Query Parameters**:
  * `page` (Optional, default `1`): Page number to query.
  * `limit` (Optional, default `50`): Number of logs per page (`1` to `500`).
* **Response Body**: `PagedTrafficHistory`

---

### 📊 Real-time Analytics & Intrusion Alerts
#### `GET /statistics`
* **Description**: Returns aggregated metrics, bandwidth, active connection counts, and protocol breakdowns.
* **Response Body**: `StatsSummaryDTO`

#### `GET /protocols`
* **Description**: Returns count and percentage of packets parsed per protocol.
* **Response Body**: `{ [protocolName: string]: ProtocolStatItem }`

#### `GET /top-ips`
* **Description**: Returns lists of top active source and destination IP addresses.
* **Query Parameters**:
  * `limit` (Optional, default `5`): Max items to return.
* **Response Body**:
  ```json
  {
    "sources": "Array<TopIPItem>",
    "destinations": "Array<TopIPItem>"
  }
  ```

#### `GET /top-domains`
* **Description**: Returns the most active destination domains resolved.
* **Query Parameters**:
  * `limit` (Optional, default `5`): Max items to return.
* **Response Body**: `Array<TopDomainItem>`

#### `GET /alerts`
* **Description**: Fetches historical threat detection alerts flagged by the IDS engine.
* **Query Parameters**:
  * `limit` (Optional, default `100`): Max logs to fetch.
* **Response Body**: `Array<AlertDTO>`

---

## ⚡ 2. WebSocket Channels Reference

All WebSockets are standard channels that accept incoming client connections, push continuous stringified JSON messages, and handle connection lifecycles.

### 🔌 `WS /ws/live-traffic`
* **Description**: Low-latency, throttled feed of individual packets parsed by the capture engine.
* **Broadcast Frequency**: Maximum 30 FPS.
* **Payload Structure**:
  ```json
  {
    "timestamp": "ISO-8601 string",
    "source_ip": "string",
    "destination_ip": "string",
    "source_port": "number | null",
    "destination_port": "number | null",
    "protocol": "string",
    "size": "number",
    "ttl": "number | null",
    "mac_src": "string | null",
    "mac_dst": "string | null",
    "domain": "string | null"
  }
  ```

### 🔌 `WS /ws/statistics`
* **Description**: Consolidated statistics report for rendering live telemetry charts.
* **Broadcast Frequency**: Exactly once per second (1 Hz).
* **Payload Structure**: Identical to the `StatsSummaryDTO` schema.

### 🔌 `WS /ws/alerts`
* **Description**: Event-driven broadcast system. Instantly fires threat details as they are flagged.
* **Broadcast Frequency**: Instantaneous (upon IDS trigger).
* **Payload Structure**:
  ```json
  {
    "id": "number | null",
    "timestamp": "ISO-8601 string",
    "severity": "string",
    "message": "string",
    "source_ip": "string | null"
  }
  ```

---

## 🛠️ 3. Frontend Data Models (TypeScript Types)

To quickly construct your frontend state management and API clients, use these corresponding TypeScript interface definitions matching the backend Pydantic DTO definitions.

```typescript
export interface CaptureStartRequest {
  interface: string;
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
}
```
