import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Search, Circle } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { subscribeLivePackets, type Packet } from "@/services/api";

const protoColor: Record<Packet["protocol"], string> = {
  HTTPS: "oklch(0.68 0.18 275)",
  DNS: "oklch(0.78 0.14 220)",
  QUIC: "oklch(0.72 0.16 155)",
  SSH: "oklch(0.78 0.16 75)",
  SMTP: "oklch(0.7 0.14 320)",
  TCP: "oklch(0.7 0.02 270)",
};

function timeAgo(ts: number) {
  const s = Math.max(1, Math.floor((Date.now() - ts) / 1000));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return `${m}m`;
}

export function PacketLogs({ initial }: { initial: Packet[] }) {
  const [packets, setPackets] = useState<Packet[]>(initial);
  const [query, setQuery] = useState("");
  const [proto, setProto] = useState<string>("all");

  useEffect(() => setPackets(initial), [initial]);

  useEffect(() => {
    const off = subscribeLivePackets((p) => {
      setPackets((prev) => [p, ...prev].slice(0, 15));
    });
    return off;
  }, []);

  const filtered = useMemo(() => {
    return packets.filter((p) => {
      if (proto !== "all" && p.protocol !== proto) return false;
      if (!query) return true;
      const q = query.toLowerCase();
      return (
        p.src.toLowerCase().includes(q) ||
        p.dst.toLowerCase().includes(q) ||
        p.domain.toLowerCase().includes(q)
      );
    });
  }, [packets, query, proto]);

  return (
    <div className="glass-panel overflow-hidden rounded-2xl">
      <div className="flex flex-col gap-4 border-b border-[var(--glass-border)] p-6 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Live packets
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--glass-border)] bg-background/30 px-2 py-0.5 text-[10px] font-medium text-success">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-60" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-success" />
              </span>
              live
            </span>
          </div>
          <h2 className="mt-1 text-lg font-semibold tracking-tight">
            Packet stream
          </h2>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search IP or domain"
              className="h-9 w-full pl-9 sm:w-64"
            />
          </div>
          <Select value={proto} onValueChange={setProto}>
            <SelectTrigger className="h-9 w-full sm:w-36">
              <SelectValue placeholder="Protocol" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All protocols</SelectItem>
              {Object.keys(protoColor).map((p) => (
                <SelectItem key={p} value={p}>{p}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="max-h-[460px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-[oklch(0.18_0.012_270)]/90 backdrop-blur">
            <tr className="text-left text-[11px] uppercase tracking-wider text-muted-foreground">
              <th className="px-6 py-3 font-medium">Time</th>
              <th className="px-3 py-3 font-medium">Source</th>
              <th className="px-3 py-3 font-medium">Destination</th>
              <th className="px-3 py-3 font-medium">Proto</th>
              <th className="px-3 py-3 font-medium">Size</th>
              <th className="px-3 py-3 font-medium">Port</th>
              <th className="px-3 py-3 font-medium">Domain</th>
              <th className="px-6 py-3 text-right font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            <AnimatePresence initial={false}>
              {filtered.map((p) => (
                <motion.tr
                  key={p.id}
                  layout
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.25 }}
                  className="border-t border-[var(--glass-border)] transition-colors hover:bg-white/[0.025]"
                >
                  <td className="px-6 py-2.5 text-muted-foreground">{timeAgo(p.time)} ago</td>
                  <td className="px-3 py-2.5 font-mono text-xs">{p.src}</td>
                  <td className="px-3 py-2.5 font-mono text-xs">{p.dst}</td>
                  <td className="px-3 py-2.5">
                    <span
                      className="inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-medium"
                      style={{
                        color: protoColor[p.protocol] || "oklch(0.7 0.02 270)",
                        borderColor: `${(protoColor[p.protocol] || "oklch(0.7 0.02 270)").replace(")", " / 0.3)")}`,
                        background: `${(protoColor[p.protocol] || "oklch(0.7 0.02 270)").replace(")", " / 0.08)")}`,
                      }}
                    >
                      {p.protocol}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-muted-foreground">{p.size} B</td>
                  <td className="px-3 py-2.5 font-mono text-xs text-muted-foreground">:{p.port}</td>
                  <td className="px-3 py-2.5 text-muted-foreground">{p.domain}</td>
                  <td className="px-6 py-2.5 text-right">
                    <StatusPill status={p.status} />
                  </td>
                </motion.tr>
              ))}
            </AnimatePresence>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-6 py-10 text-center text-sm text-muted-foreground">
                  No packets match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: Packet["status"] }) {
  const map = {
    ok: { c: "var(--success)", t: "OK" },
    suspicious: { c: "var(--warning)", t: "Suspicious" },
    blocked: { c: "var(--destructive)", t: "Blocked" },
  }[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] font-medium"
      style={{ color: map.c }}
    >
      <Circle className="h-2 w-2 fill-current" />
      {map.t}
    </span>
  );
}
