import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Statistics } from "@/services/api";

export function TrafficChart({ data }: { data: Statistics["series"] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.15, ease: "easeOut" }}
      className="rounded-2xl glass-panel p-6"
    >
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold tracking-tight">Live Traffic</h2>
          <p className="text-xs text-muted-foreground">Packets per second · last 24m</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-primary" />
          inbound
        </div>
      </div>

      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="traffic" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="oklch(0.68 0.18 275)" stopOpacity={0.45} />
                <stop offset="100%" stopColor="oklch(0.68 0.18 275)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="oklch(1 0 0 / 0.05)" vertical={false} />
            <XAxis
              dataKey="t"
              tickLine={false}
              axisLine={false}
              tick={{ fill: "oklch(0.66 0.02 270)", fontSize: 11 }}
              interval={7}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tick={{ fill: "oklch(0.66 0.02 270)", fontSize: 11 }}
            />
            <Tooltip
              cursor={{ stroke: "oklch(1 0 0 / 0.1)" }}
              contentStyle={{
                background: "oklch(0.18 0.012 270)",
                border: "1px solid oklch(1 0 0 / 0.08)",
                borderRadius: 12,
                fontSize: 12,
              }}
              labelStyle={{ color: "oklch(0.7 0.02 270)" }}
            />
            <Area
              type="monotone"
              dataKey="v"
              stroke="oklch(0.72 0.16 275)"
              strokeWidth={2}
              fill="url(#traffic)"
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
