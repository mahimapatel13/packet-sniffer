import { motion } from "framer-motion";
import type { AlertDTO } from "@/services/types";

const severityColor: Record<string, string> = {
  CRITICAL: "bg-destructive",
  WARNING: "bg-warning",
  INFO: "bg-primary",
};

const severityLabel: Record<string, string> = {
  CRITICAL: "Critical",
  WARNING: "Warning",
  INFO: "Info",
};

function timeAgo(timestamp: string) {
  const t = new Date(timestamp).getTime();
  const diff = Math.floor((Date.now() - t) / 1000);
  if (diff < 60) return `${Math.max(1, diff)}s ago`;
  const m = Math.floor(diff / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return `${h}h ago`;
}

export function AlertFeed({ alerts }: { alerts: AlertDTO[] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.25, ease: "easeOut" }}
      className="rounded-2xl glass-panel p-6"
    >
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-tight">Recent Alerts</h2>
        <button className="text-xs text-muted-foreground transition hover:text-foreground">
          View all
        </button>
      </div>

      <ul className="space-y-2">
        {alerts.map((a, i) => (
          <motion.li
            key={a.id || i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.05 * i }}
            className="group flex items-center gap-4 rounded-xl border border-transparent px-3 py-3 transition hover:border-border/60 hover:bg-card/40"
          >
            <span className="relative flex h-2.5 w-2.5 shrink-0">
              <span
                className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-60 ${severityColor[a.severity] || 'bg-muted'}`}
              />
              <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${severityColor[a.severity] || 'bg-muted'}`} />
            </span>
            <div className="flex min-w-0 flex-1 items-center justify-between gap-4">
              <div className="min-w-0">
                <p className="truncate text-sm text-foreground">{a.message}</p>
                <div className="mt-0.5 flex items-center gap-2">
                  <span className="text-[11px] uppercase tracking-wider text-muted-foreground">
                    {severityLabel[a.severity] || a.severity}
                  </span>
                  {a.source_ip && (
                    <span className="text-[10px] font-mono text-muted-foreground/60 italic">
                      · {a.source_ip}
                    </span>
                  )}
                </div>
              </div>
              <span className="shrink-0 text-xs text-muted-foreground">{timeAgo(a.timestamp)}</span>
            </div>
          </motion.li>
        ))}
        {alerts.length === 0 && (
          <div className="py-8 text-center text-xs text-muted-foreground italic">
            No alerts detected.
          </div>
        )}
      </ul>
    </motion.div>
  );
}
