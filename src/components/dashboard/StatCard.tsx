import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, type LucideIcon } from "lucide-react";

type Props = {
  label: string;
  value: string;
  trend: number;
  icon: LucideIcon;
  index?: number;
};

export function StatCard({ label, value, trend, icon: Icon, index = 0 }: Props) {
  const positive = trend >= 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.05 * index, ease: "easeOut" }}
      whileHover={{ y: -3 }}
      className="group relative overflow-hidden rounded-2xl glass-panel p-6"
    >
      <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-primary/10 opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-100" />
      <div className="relative flex items-start justify-between">
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {label}
          </span>
          <span className="text-3xl font-semibold tracking-tight text-foreground">
            {value}
          </span>
        </div>
        <div className="grid h-10 w-10 place-items-center rounded-xl border border-border/60 bg-card/60 text-primary">
          <Icon className="h-4 w-4" strokeWidth={2.2} />
        </div>
      </div>
      <div className="relative mt-6 flex items-center gap-1.5 text-xs">
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-medium ${
            positive
              ? "bg-success/10 text-success"
              : "bg-destructive/10 text-destructive"
          }`}
        >
          {positive ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
          {Math.abs(trend).toFixed(1)}%
        </span>
        <span className="text-muted-foreground">vs last hour</span>
      </div>
    </motion.div>
  );
}
