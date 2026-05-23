import { motion } from "framer-motion";
import { Activity, Play, Square, Settings, User, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { getHealth, startCapture, stopCapture } from "@/services/api";
import { InterfaceDTO, SystemHealthDTO } from "@/services/types";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export function Navbar() {
  const [health, setHealth] = useState<SystemHealthDTO | null>(null);
  const [interfaces, setInterfaces] = useState<InterfaceDTO[]>([]);
  const [loadingIfaces, setLoadingIfaces] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const fetchHealth = async () => {
    try {
      const res = await fetch("http://localhost:8000/");
      if (!res.ok) return;
      const data: SystemHealthDTO = await res.json();
      setHealth(data);
    } catch (err) {
      console.error("Failed to fetch health", err);
    }
  };

  useEffect(() => {
    fetchHealth();
    const id = setInterval(fetchHealth, 5000);
    return () => clearInterval(id);
  }, []);

  // Load interfaces whenever dialog opens
  useEffect(() => {
    if (!open) return;
    let cancelled = false;

    const load = async () => {
      setLoadingIfaces(true);
      setInterfaces([]);
      try {
        const res = await fetch("http://localhost:8000/capture/interfaces");
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`${res.status}: ${text}`);
        }
        const data: InterfaceDTO[] = await res.json();
        if (!cancelled) {
          setInterfaces(data);
          if (data.length === 0) {
            toast.error("No interfaces found. Run backend with admin/root privileges.");
          }
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : String(err);
          toast.error(`Failed to load interfaces: ${msg}`);
        }
      } finally {
        if (!cancelled) setLoadingIfaces(false);
      }
    };

    load();
    return () => { cancelled = true; };
  }, [open]);

  const isActive = health?.active_captures.some((c) => c.is_active) ?? false;
  const activeInterface = health?.active_captures.find((c) => c.is_active)?.interface;

  const handleStart = async (iface: string) => {
    setActionLoading(true);
    try {
      const res = await fetch("http://localhost:8000/capture/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interface: iface }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`${res.status}: ${text}`);
      }
      toast.success(`Started capture on ${iface}`);
      setOpen(false);
      fetchHealth();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error(`Failed to start capture: ${msg}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    setActionLoading(true);
    try {
      const res = await fetch("http://localhost:8000/capture/stop", { method: "POST" });
      if (!res.ok) throw new Error(`${res.status}`);
      toast.success("Stopped all captures");
      fetchHealth();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error(`Failed to stop capture: ${msg}`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="sticky top-0 z-40 w-full"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 md:px-10">
        <div className="flex items-center gap-3">
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl glass-panel">
            <div className="absolute inset-0 rounded-xl bg-primary/20 blur-xl" />
            <Activity className="relative h-4 w-4 text-primary" strokeWidth={2.5} />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold tracking-tight">Strata</span>
            <span className="text-[11px] text-muted-foreground">Network Traffic Analyzer</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden items-center gap-2 rounded-full border border-border/60 bg-card/40 px-3 py-1.5 text-xs text-muted-foreground sm:flex">
            <span className="relative flex h-2 w-2">
              <span
                className={`absolute inline-flex h-full w-full ${isActive ? "animate-ping" : ""} rounded-full ${isActive ? "bg-success" : "bg-muted"} opacity-60`}
              />
              <span
                className={`relative inline-flex h-2 w-2 rounded-full ${isActive ? "bg-success" : "bg-muted"}`}
              />
            </span>
            <span className="text-foreground/80">{isActive ? "Live" : "Idle"}</span>
            <span>· {isActive ? `Monitoring ${activeInterface}` : "System Ready"}</span>
          </div>

          {isActive ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleStop}
              disabled={actionLoading}
              className="h-9 gap-2 border-destructive/20 bg-destructive/5 text-destructive hover:bg-destructive/10"
            >
              <Square className="h-3.5 w-3.5 fill-current" />
              Stop
            </Button>
          ) : (
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-9 gap-2 border-primary/20 bg-primary/5 text-primary hover:bg-primary/10"
                >
                  <Play className="h-3.5 w-3.5 fill-current" />
                  Start Capture
                </Button>
              </DialogTrigger>
              <DialogContent className="glass-panel sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Select Interface</DialogTitle>
                  <DialogDescription>
                    Choose a network interface to begin monitoring traffic.
                  </DialogDescription>
                </DialogHeader>
                <div className="mt-4 grid gap-3">
                  {loadingIfaces ? (
                    <div className="flex items-center justify-center py-8">
                      <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                  ) : interfaces.length === 0 ? (
                    <div className="py-8 text-center text-sm text-muted-foreground">
                      No interfaces found.{" "}
                      <button
                        className="underline hover:text-foreground"
                        onClick={() => { setOpen(false); setTimeout(() => setOpen(true), 0); }}
                      >
                        Retry
                      </button>
                    </div>
                  ) : (
                    interfaces.map((iface) => (
                      <button
                        key={iface.name}
                        onClick={() => handleStart(iface.name)}
                        disabled={actionLoading}
                        className="flex flex-col items-start gap-1 rounded-xl border border-border/60 bg-card/40 p-4 text-left transition hover:border-primary/40 hover:bg-primary/5 disabled:opacity-50"
                      >
                        <div className="flex w-full items-center justify-between">
                          <span className="font-semibold text-foreground">{iface.name}</span>
                          <span
                            className={`text-[10px] rounded-full px-2 py-0.5 ${
                              iface.is_up
                                ? "bg-success/10 text-success"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {iface.is_up ? "UP" : "DOWN"}
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {iface.description || "No description"}
                        </span>
                        <div className="mt-1 flex flex-wrap gap-2">
                          {iface.ip_addresses.map((ip) => (
                            <span key={ip} className="text-[10px] font-mono text-muted-foreground/70">
                              {ip}
                            </span>
                          ))}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </DialogContent>
            </Dialog>
          )}

          <button className="grid h-9 w-9 place-items-center rounded-xl border border-border/60 bg-card/40 text-muted-foreground transition hover:text-foreground hover:bg-card/70">
            <Settings className="h-4 w-4" />
          </button>
          <button className="grid h-9 w-9 place-items-center rounded-xl border border-border/60 bg-card/40 text-muted-foreground transition hover:text-foreground hover:bg-card/70">
            <User className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.header>
  );
}