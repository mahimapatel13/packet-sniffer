import { motion } from "framer-motion";
import type { Protocol, SourceIp } from "@/services/api";

export function ProtocolList({
  protocols,
  sources,
}: {
  protocols: Protocol[];
  sources: SourceIp[];
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
      className="flex h-full flex-col gap-6"
    >
      <div className="rounded-2xl glass-panel p-6">
        <h3 className="mb-5 text-sm font-semibold tracking-tight">Top Protocols</h3>
        <ul className="space-y-4">
          {protocols.map((p) => (
            <li key={p.name} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-foreground">{p.name}</span>
                <span className="text-muted-foreground">{p.share}%</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${p.share}%` }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  className="h-full rounded-full bg-primary/80"
                />
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-2xl glass-panel p-6">
        <h3 className="mb-5 text-sm font-semibold tracking-tight">Top Source IPs</h3>
        <ul className="divide-y divide-border/60">
          {sources.map((s) => (
            <li key={s.ip} className="flex items-center justify-between py-3 text-xs first:pt-0 last:pb-0">
              <span className="font-mono text-foreground">{s.ip}</span>
              <span className="text-muted-foreground">{s.packets.toLocaleString()} pkts</span>
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}
