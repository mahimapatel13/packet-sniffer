# 🌐 Network Traffic Analyzer: Frontend Integration & Visual Design Specification

This document provides a comprehensive integration manual and UI/UX design blueprint for generating a modern, responsive, and visually stunning web frontend for the **Network Traffic Analyzer**.

---

## 🎨 1. Design System & Aesthetics (Cyber-Defense Command Center)

To create a premium-grade, high-fidelity security dashboard that immediately wows users, we recommend a **dark-theme glassmorphism design** with glowing neon accents. This aesthetic is highly readable for long monitoring sessions and matches the visual language of network monitoring tools.

### 🎨 Color Palette
Using HSL-based colors allows for easy translucency adjustments (`hsla`) for background glass containers.

| Color Name | Hex Code | HSL Representation | UI Purpose |
| :--- | :--- | :--- | :--- |
| **Dark Void (BG)** | `#07090e` | `hsl(225, 33%, 5%)` | Main app background |
| **Glass Base** | `#0f131c` | `hsl(220, 29%, 8%, 0.6)`| Translucent card panels |
| **Cyber Cyan** | `#00f0ff` | `hsl(184, 100%, 50%)` | Primary interactive elements, TCP, Active states |
| **Pulse Purple** | `#bd00ff` | `hsl(284, 100%, 50%)` | UDP traffic, statistics indicators |
| **Matrix Green** | `#39ff14` | `hsl(111, 100%, 54%)` | Safe traffic, DNS protocol, active sessions |
| **Threat Red** | `#ff0055` | `hsl(340, 100%, 50%)` | Critical Alerts, IDS triggers, ICMP protocol |
| **Muted Slate** | `#64748b` | `hsl(215, 16%, 47%)` | Border lines, secondary text, metadata labels |

### ✍️ Typography
* **Primary Fonts**: `Outfit` or `Inter` (via Google Fonts) for headlines, navigation elements, and dashboard statistics.
* **Monospace Font**: `JetBrains Mono` or `Fira Code` for IP addresses, MAC addresses, hex packet payloads, and log entries.

### ✨ Glassmorphism & UI Accent Classes
Apply these properties in your CSS (e.g. Tailwind or custom CSS rules) to give a polished glass finish:

```css
.glass-panel {
  background: rgba(15, 19, 28, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(100, 116, 139, 0.15);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  border-radius: 12px;
}

.glow-cyan {
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.45);
}

.glow-red {
  box-shadow: 0 0 20px rgba(255, 0, 85, 0.6);
  animation: pulse-red 2s infinite alternate;
}

@keyframes pulse-red {
  0% { transform: scale(1); box-shadow: 0 0 10px rgba(255, 0, 85, 0.4); }
  100% { transform: scale(1.02); box-shadow: 0 0 25px rgba(255, 0, 85, 0.85); }
}
```

---

## 📡 2. HTTP REST API Specifications

The FastAPI backend runs on `http://localhost:8000` (by default) and exposes the following endpoints. 

### 🏥 System Status

#### `GET /`
Returns backend health status and lists active sniffing sessions.
* **Response Body (`JSON`)**:
  ```json
  {
    "status": "healthy",
    "project": "Traffic Analyzer",
    "active_captures": []
  }
  ```

---

### 🕹️ Capture Session Management

#### `GET /capture/interfaces`
Fetches a list of available network interfaces detected on the host (e.g., Wi-Fi, Ethernet, loopback adapters).
* **Response Body (`Array[InterfaceDTO]`)**:
  ```json
  [
    {
      "name": "Wi-Fi",
      "description": "Intel(R) Wi-Fi 6 AX201 160MHz",
      "ip_addresses": ["192.168.1.15", "fe80::1c2e:4d5f:6a7b:8c9d"],
      "mac_address": "AA:BB:CC:DD:EE:FF",
      "is_loopback": false,
      "is_up": true
    }
  ]
  ```

#### `POST /capture/start`
Initiates real-time packet sniffing on a chosen network adapter and resets database analytics caches.
* **Request Body (`CaptureStartRequest`)**:
  ```json
  {
    "interface": "Wi-Fi"
  }
  ```
* **Response Body (`JSON`)**:
  ```json
  {
    "status": "started",
    "interface": "Wi-Fi",
    "session_id": 1,
    "timestamp": "2026-05-22T20:45:00.123456"
  }
  ```

#### `POST /capture/stop`
Gracefully terminates packet capture across all network interfaces and flushes remaining buffers to the database.
* **Response Body (`JSON`)**:
  ```json
  {
    "status": "stopped",
    "captured_packets": 2548,
    "duration_seconds": 45.2
  }
  ```

---

### 📋 Packet Logs & Database Records

#### `GET /traffic/live`
Fetches the most recently captured packet database logs. Excellent for instantly populating dashboards upon loading.
* **Query Parameters**:
  * `limit` (Optional, integer: `1-200`, default: `50`): Number of latest logs to fetch.
* **Response Body (`Array[TrafficRecordDTO]`)**:
  ```json
  [
    {
      "id": 1054,
      "timestamp": "2026-05-22T20:45:10.512000",
      "source_ip": "192.168.1.15",
      "destination_ip": "8.8.8.8",
      "source_port": 53556,
      "destination_port": 53,
      "protocol": "DNS",
      "packet_size": 74,
      "ttl": 128,
      "mac_src": "AA:BB:CC:DD:EE:FF",
      "mac_dst": "00:11:22:33:44:55",
      "domain": "dns.google",
      "payload_len": 32
    }
  ]
  ```

#### `GET /traffic/history`
Exposes the database history with cursor/offset pagination. Perfect for a detailed, filterable packet browser grid.
* **Query Parameters**:
  * `page` (Optional, integer `ge=1`, default: `1`): Page number to query.
  * `limit` (Optional, integer `ge=1, le=500`, default: `50`): Size of page records.
* **Response Body (`PagedTrafficHistory`)**:
  ```json
  {
    "total": 14502,
    "page": 1,
    "limit": 50,
    "records": [
      {
        "id": 1053,
        "timestamp": "2026-05-22T20:45:09.912000",
        "source_ip": "142.250.190.46",
        "destination_ip": "192.168.1.15",
        "source_port": 443,
        "destination_port": 53550,
        "protocol": "HTTPS",
        "packet_size": 1420,
        "ttl": 57,
        "mac_src": "00:11:22:33:44:55",
        "mac_dst": "AA:BB:CC:DD:EE:FF",
        "domain": "google.com",
        "payload_len": 1380
      }
    ]
  }
  ```

---

### 📊 Analytics & IDS Security Threat Intelligence

#### `GET /statistics`
Retrieves live aggregated traffic statistics, volume tracking, and counts from the global in-memory analytics engine.
* **Response Body (`StatsSummaryDTO`)**:
  ```json
  {
    "total_packets": 2548,
    "total_bytes": 1824902,
    "packets_per_second": 56.4,
    "bandwidth_bytes_per_second": 40373.8,
    "protocol_distribution": {
      "TCP": { "count": 1820, "percentage": 71.43 },
      "UDP": { "count": 620, "percentage": 24.33 },
      "DNS": { "count": 92, "percentage": 3.61 },
      "ICMP": { "count": 16, "percentage": 0.63 }
    },
    "top_source_ips": [
      { "ip": "192.168.1.15", "count": 1543 },
      { "ip": "142.250.190.46", "count": 312 }
    ],
    "top_destination_ips": [
      { "ip": "142.250.190.46", "count": 1204 },
      { "ip": "8.8.8.8", "count": 612 }
    ],
    "top_domains": [
      { "domain": "google.com", "count": 1516 },
      { "domain": "dns.google", "count": 704 }
    ],
    "active_connections_count": 42,
    "timestamp": "2026-05-22T20:45:12.443"
  }
  ```

#### `GET /protocols`
Returns immediate distribution breakdown per protocol.
* **Response Body**: Identical to `"protocol_distribution"` nested within `/statistics`.

#### `GET /top-ips`
Isolates top IP traffic nodes.
* **Response Body**:
  ```json
  {
    "sources": [
      { "ip": "192.168.1.15", "count": 1543 }
    ],
    "destinations": [
      { "ip": "8.8.8.8", "count": 612 }
    ]
  }
  ```

#### `GET /top-domains`
Isolates the most frequently contacted destination servers/web domains.
* **Response Body**:
  ```json
  [
    { "domain": "google.com", "count": 1516 }
  ]
  ```

#### `GET /alerts`
Fetches a list of historical threat logs flagged by the deep packet inspection (IDS) engine.
* **Response Body (`Array[AlertDTO]`)**:
  ```json
  [
    {
      "id": 14,
      "timestamp": "2026-05-22T20:45:02.102000",
      "severity": "CRITICAL",
      "message": "Potential Port Scan Activity Detected - 15 unique ports queried in under 2 seconds.",
      "source_ip": "192.168.1.80"
    },
    {
      "id": 13,
      "timestamp": "2026-05-22T20:44:30.400000",
      "severity": "WARNING",
      "message": "Suspicious Large ICMP Payload (Ping of Death Signature). Size: 1450 bytes",
      "source_ip": "10.0.0.4"
    }
  ]
  ```

---

## ⚡ 3. Real-Time WebSockets Integration

WebSockets provide low-latency streams for live packet updates and charts. All three WebSocket channels accept standard connections and push stringified JSON payloads.

| Channel | URL | Broadcast Frequency | Content Type / Description |
| :--- | :--- | :--- | :--- |
| **Live Traffic** | `ws://localhost:8000/ws/live-traffic` | 30 FPS maximum (throttled) | Emits details on individual packets as they hit the network interface. |
| **Statistics** | `ws://localhost:8000/ws/statistics` | Exactly 1 time per second | Emits fully consolidated metrics summary (`StatsSummaryDTO`) for instant charts updates. |
| **IDS Alerts** | `ws://localhost:8000/ws/alerts` | Instantly (event-triggered) | Emits structural alert details the exact microsecond a signature triggers. |

### 🛠️ Client-side WebSocket Connection Manager Snippet (ES6 JavaScript)
```javascript
class NetworkWSClient {
  constructor(baseURL = "ws://localhost:8000/ws") {
    this.baseURL = baseURL;
    this.sockets = {};
  }

  connect(channelName, onMessageCallback) {
    if (this.sockets[channelName]) {
      console.warn(`Already connected to ${channelName}`);
      return;
    }

    const url = `${this.baseURL}/${channelName}`;
    const ws = new WebSocket(url);

    ws.onopen = () => console.log(`🚀 Connected to WebSocket Channel: [${channelName}]`);
    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      onMessageCallback(payload);
    };
    ws.onerror = (err) => console.error(`❌ WebSocket [${channelName}] Error:`, err);
    ws.onclose = () => {
      console.log(`🔌 Disconnected from [${channelName}]. Attempting reconnect in 3s...`);
      delete this.sockets[channelName];
      setTimeout(() => this.connect(channelName, onMessageCallback), 3000);
    };

    this.sockets[channelName] = ws;
  }

  disconnectAll() {
    Object.keys(this.sockets).forEach((chan) => {
      this.sockets[chan].close();
      delete this.sockets[chan];
    });
  }
}

// Usage Example
// const client = new NetworkWSClient();
// client.connect("live-traffic", (packet) => console.log("New Packet:", packet.protocol, packet.size));
// client.connect("statistics", (stats) => updateDashboardMetrics(stats));
// client.connect("alerts", (alert) => triggerIntrusionOverlay(alert));
```

---

## 🟢 4. Network Topology & Packet Flow Animation Engine

To build the dynamic animation where data packets move between source and destination IP nodes, you can implement an HTML5 Canvas drawing loop. It is highly lightweight and can render hundreds of packet particles concurrently at 60 FPS without UI bottlenecks.

### 🌐 The Layout Strategy: Topology Graph
1. **Nodes**: Keep track of the active IP addresses in a Map. Place them on a circular coordinates system or a simple force-directed layout (D3.js).
   * Put your local machine (e.g. `192.168.1.15`) in the center of the Canvas.
   * Place external destination IPs (such as `8.8.8.8`, `142.250.190.46`) floating in a surrounding orbit.
2. **Edges**: Draw subtle, dark glowing lines connecting the local host in the center to the active external nodes.
3. **Particles (Packets)**: When a packet is received via the `/ws/live-traffic` WebSocket, spawn a moving "spark" particle that travels from the Source Node's coordinates to the Destination Node's coordinates.

### 💻 Canvas Particle Animation Engine (Clean Canvas API Implementation)

Save this JavaScript code in your frontend application to power the main visual console:

```javascript
class NetworkCanvasVisualizer {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext("2d");
    this.nodes = new Map(); // Key: IP address -> { x, y, label, isLocal, lastActive }
    this.particles = [];    // List of active packet animations
    
    // Protocol styling rules
    this.protocolStyles = {
      TCP:   { color: "#00f0ff", size: 4, speed: 2.5 }, // Cyan
      UDP:   { color: "#bd00ff", size: 3.5, speed: 3.0 }, // Purple
      DNS:   { color: "#39ff14", size: 3.0, speed: 2.8 }, // Matrix Green
      ICMP:  { color: "#ff0055", size: 5.0, speed: 1.5 }, // Threat Red
      OTHER: { color: "#64748b", size: 3, speed: 2.0 }   // Slate Gray
    };

    this.resizeCanvas();
    window.addEventListener("resize", () => this.resizeCanvas());
    this.animate();
  }

  resizeCanvas() {
    this.canvas.width = this.canvas.parentElement.clientWidth;
    this.canvas.height = this.canvas.parentElement.clientHeight || 500;
    this.initializeLocalNode();
  }

  initializeLocalNode() {
    // Put Local host at the absolute center
    const cx = this.canvas.width / 2;
    const cy = this.canvas.height / 2;
    this.nodes.set("LOCALHOST", {
      x: cx,
      y: cy,
      label: "MY MACHINE (sniffing)",
      isLocal: true,
      lastActive: Date.now()
    });
  }

  // Inject or update node positions when packets flow
  getOrCreateNode(ip, isSource) {
    if (!ip) return this.nodes.get("LOCALHOST");
    
    // Check if it's our local address range (or simplified: mapping local source to localhost node)
    if (ip.startsWith("192.168.") || ip === "127.0.0.1") {
      return this.nodes.get("LOCALHOST");
    }

    if (this.nodes.has(ip)) {
      const node = this.nodes.get(ip);
      node.lastActive = Date.now();
      return node;
    }

    // Place external IP nodes on a random orbital path around center
    const cx = this.canvas.width / 2;
    const cy = this.canvas.height / 2;
    const minDim = Math.min(this.canvas.width, this.canvas.height);
    const radius = (minDim / 2.8) * (0.6 + Math.random() * 0.4); // Random orbital ring distance
    const angle = Math.random() * Math.PI * 2;                 // Random orbital angle

    const newNode = {
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius,
      label: ip,
      isLocal: false,
      lastActive: Date.now()
    };

    this.nodes.set(ip, newNode);
    return newNode;
  }

  // Call this function whenever a new packet record arrives over ws/live-traffic
  spawnPacket(packet) {
    const srcNode = this.getOrCreateNode(packet.source_ip, true);
    const dstNode = this.getOrCreateNode(packet.destination_ip, false);

    // Skip self-loop animations for clean visuals unless desired
    if (srcNode === dstNode) return;

    const protoStyle = this.protocolStyles[packet.protocol] || this.protocolStyles.OTHER;

    // Scale packet size display based on actual captured size
    const particleSize = protoStyle.size + Math.min(packet.size / 500, 6);

    this.particles.push({
      startX: srcNode.x,
      startY: srcNode.y,
      endX: dstNode.x,
      endY: dstNode.y,
      x: srcNode.x,
      y: srcNode.y,
      progress: 0.0,
      speed: protoStyle.speed * (0.8 + Math.random() * 0.4),
      color: protoStyle.color,
      size: particleSize,
      protocol: packet.protocol
    });
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    // Clear Canvas with subtle trail effect (alpha blends older frame for motion blur)
    this.ctx.fillStyle = "rgba(7, 9, 14, 0.25)";
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // 1. Draw glowing structural topology connection cables
    this.nodes.forEach((node) => {
      if (node.isLocal) return; // Draw from center outwards
      
      const local = this.nodes.get("LOCALHOST");
      this.ctx.strokeStyle = "rgba(100, 116, 139, 0.08)";
      this.ctx.lineWidth = 1;
      this.ctx.beginPath();
      this.ctx.moveTo(local.x, local.y);
      this.ctx.lineTo(node.x, node.y);
      this.ctx.stroke();

      // Clean up stale nodes that haven't had packet traffic for 20 seconds
      if (Date.now() - node.lastActive > 20000) {
        this.nodes.delete(node.label);
      }
    });

    // 2. Animate and update active packet particles
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.progress += 0.005 * p.speed;

      // Linear interpolation between source and destination
      p.x = p.startX + (p.endX - p.startX) * p.progress;
      p.y = p.startY + (p.endY - p.startY) * p.progress;

      // Draw particle spark
      this.ctx.shadowBlur = p.size * 2.5;
      this.ctx.shadowColor = p.color;
      this.ctx.fillStyle = p.color;
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      this.ctx.fill();

      // Reset shadow blur for optimization
      this.ctx.shadowBlur = 0;

      // Remove particles once they reach their destination
      if (p.progress >= 1.0) {
        this.particles.splice(i, 1);
      }
    }

    // 3. Draw central and orbital nodes on top
    this.nodes.forEach((node) => {
      this.ctx.fillStyle = node.isLocal ? "#00f0ff" : "#bd00ff";
      
      // Node Pulse indicator based on activity recency
      const timeSinceActive = Date.now() - node.lastActive;
      const sizePulse = node.isLocal ? 16 : 8;
      const pulseMultiplier = Math.max(0, 1 - (timeSinceActive / 1500)); // fade pulse over 1.5s
      const currentRadius = sizePulse + (pulseMultiplier * 8);

      // Node base circle
      this.ctx.shadowBlur = currentRadius * 0.8;
      this.ctx.shadowColor = node.isLocal ? "#00f0ff" : "#bd00ff";
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, currentRadius, 0, Math.PI * 2);
      this.ctx.fill();
      this.ctx.shadowBlur = 0;

      // Text Labels
      this.ctx.fillStyle = "#ffffff";
      this.ctx.font = node.isLocal ? "bold 13px JetBrains Mono" : "10px JetBrains Mono";
      this.ctx.textAlign = "center";
      this.ctx.fillText(node.label, node.x, node.y - currentRadius - 6);
    });
  }
}
```

---

## 🛠️ 5. Key Frontend Components & Features List

To make this network analyzer highly useful, modular, and extremely appealing to users, we recommend organizing your React/Vue/Svelte/Vanilla HTML frontend into these five sections:

```
+-----------------------------------------------------------------------------+
|  [⚡ COMMAND CONTROL] Start/Stop Capture | Selection: adapter dropdown       |
+-----------------------------------------------------------------------------+
|                                  |                                          |
|  [🌐 NETWORK TOPOLOGY MAP]       |  [📊 REAL-TIME TELEMETRY]                |
|  Interactive circular canvas     |  - Bandwidth: Bytes/sec & Packets/sec    |
|  showing node-to-node packets.   |  - Pie chart: Protocol breakdown         |
|  Sparks moving in real-time.     |  - Bar chart: Top IPs & Top Domains      |
|                                  |                                          |
+-----------------------------------------------------------------------------+
|                                                                             |
|  [⚠️ IDS THREAT ALERTS FEED]                                                 |
|  Instant sliding banners for CRITICAL scans, invalid handshakes (red glows)  |
|                                                                             |
+-----------------------------------------------------------------------------+
|                                                                             |
|  [📋 PACKET LOG SHEET] Virtualized list grid, color-coded records           |
|  Shows details on hover, hex viewer for binary/ASCII payloads               |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### 🎯 Component Specifications

1. **Top Bar Command Control**:
   * Dropdown selector calling `GET /capture/interfaces` on initial boot.
   * Glow-in-the-dark **START** button calling `POST /capture/start` with the selected interface. Turns vibrant neon cyan and flashes slightly when capturing.
   * **STOP** button calling `POST /capture/stop` to safely close down channels.
2. **Interactive 2D Topology Canvas**:
   * Uses the `NetworkCanvasVisualizer` module. 
   * Interactive hover: hovering over a node displays its full address, vendor prefix (resolved from MAC), and current transmission load.
3. **Real-time Telemetry Dashboard**:
   * **Bandwidth Area Chart**: Renders bytes-per-second and packets-per-second, updating smoothly every 1 second by subscribing to `ws://localhost:8000/ws/statistics`.
   * **Protocol Distribution Pie**: Renders using standard libraries like `Chart.js`, `ApexCharts`, or `Recharts`. Direct live binding to WebSocket statistics.
4. **Intrusion Detection System (IDS) alerts**:
   * Connected directly to `ws://localhost:8000/ws/alerts`.
   * Displays immediate toaster notifications or a high-contrast sliding side-drawer. 
   * If severity is `CRITICAL`, triggers an overlay with a radar scanning grid effect to emphasize the alert.
5. **Virtualized Log Table**:
   * Packet rows color-coded by protocol (TCP = subtle cyan tint, UDP = violet tint, ICMP = light crimson).
   * To prevent DOM degradation when hundreds of packets flow by, use a virtual list container (like `react-window` or custom offset sliders) which only renders the rows visible on the viewport.
   * **Deep Inspector Dialog**: Clicking on a log row displays a side-panel inspecting the raw packet data (including TCP flags, TTL, MAC addresses, and a beautiful split Hexadecimal / ASCII payload representation).

---

## 📈 6. Advanced Technical Recommendations for a World-Class App

* **Avoid DOM Bloat**: Never append raw `<tr>` or `<div>` elements directly for every incoming packet on the live feed. Maintain a circular array (buffer) of maximum `500` items in your frontend state, dropping the oldest items when new ones arrive.
* **Responsive Layout Grid**: Use CSS Grid with dynamic media queries:
  ```css
  .dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
  }
  ```
* **Offline / Connection Interruption Shield**: Implement a overlay modal that appears if the WebSocket disconnects (e.g. if the user stops the backend process). Show a sleek glass screen stating `"Reconnecting to Network Analyzer Core..."` with a spinning radar icon.
