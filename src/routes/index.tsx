import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Activity, Network, Wifi, ShieldAlert } from "lucide-react";
import { Navbar } from "@/components/dashboard/Navbar";
import { StatCard } from "@/components/dashboard/StatCard";
import { TrafficChart } from "@/components/dashboard/TrafficChart";
import { ProtocolList } from "@/components/dashboard/ProtocolList";
import { AlertFeed } from "@/components/dashboard/AlertFeed";
import { NetworkGraph } from "@/components/dashboard/NetworkGraph";
import { PacketLogs } from "@/components/dashboard/PacketLogs";
import { GlobeMap } from '@/components/dashboard/GlobeMap';
import { GlobeStats } from '@/components/dashboard/GlobeStats';
import {
  getStatistics,
  getProtocols,
  getTopIps,
  getAlerts,
  getGraph,
  getLivePackets,
  getGeoPoints,
  subscribeStatistics,
} from "@/services/api";
import { useEffect, useState } from "react";
import { StatsSummaryDTO, GeoPointDTO } from "@/services/types";

export const Route = createFileRoute("/")({
  component: Dashboard,
  head: () => ({
    meta: [
      { title: "Strata — Network Traffic Analyzer" },
      {
        name: "description",
        content:
          "Minimal, premium real-time network traffic and threat monitoring dashboard.",
      },
    ],
  }),
});

function Dashboard() {
  const statsQuery = useQuery({ queryKey: ["statistics"], queryFn: getStatistics,
  staleTime: 5000,
  refetchInterval:52000,
  refetchOnWindowFocus: false,
  retry: false,});
  const protocolsQuery = useQuery({ queryKey: ["protocols"], queryFn: getProtocols ,
  staleTime: 5000,
  refetchInterval: 5000,
  refetchOnWindowFocus: false,
  retry: false,
});
  const ipsQuery = useQuery({ queryKey: ["top-ips"], queryFn: () => getTopIps() });
  const alertsQuery = useQuery({ queryKey: ["alerts"], queryFn: () => getAlerts() ,
  staleTime: 5000,
  refetchInterval: 15000,
  refetchOnWindowFocus: false,
  retry: false,
});
  const graphQuery = useQuery({ queryKey: ["graph"], queryFn: getGraph,
  staleTime: 5000,
  refetchInterval: 10000,
  refetchOnWindowFocus: false,
  retry: false,
 });
  const packetsQuery = useQuery({ queryKey: ["packets"], queryFn: getLivePackets ,
  enabled:false,
});
  const geoQuery = useQuery({
    queryKey: ['geo-points'],
    queryFn: () => getGeoPoints(100),

  staleTime: 5000,
  refetchInterval: 15000,
  refetchOnWindowFocus: false,
  retry: false,

  });

  const [liveStats, setLiveStats] = useState<StatsSummaryDTO | null>(null);
  const [series, setSeries] = useState<{ t: string; v: number }[]>([]);
  const [liveGeoPoints, setLiveGeoPoints] = useState<GeoPointDTO[]>([]);

  useEffect(() => {
    if (statsQuery.data) {
      setLiveStats(statsQuery.data);
    }
  }, [statsQuery.data]);

  useEffect(() => {
    if (geoQuery.data) {
      setLiveGeoPoints(geoQuery.data);
    }
  }, [geoQuery.data]);

  useEffect(() => {
    const off = subscribeStatistics((newStats) => {
      setLiveStats(newStats);
      if (newStats.geo_points && newStats.geo_points.length > 0) {
        setLiveGeoPoints(newStats.geo_points);
      }
      setSeries((prev) => {
        const next = [...prev, { t: new Date(newStats.timestamp).toLocaleTimeString(), v: newStats.packets_per_second }];
        return next.slice(-30);
      });
    });
    return off;
  }, []);

  const s = liveStats;

  // Format protocols for ProtocolList
  const protocols = Object.entries(s?.protocol_distribution || {}).map(([name, stat]) => ({
    name,
    share: Math.round(stat.percentage),
  })).sort((a, b) => b.share - a.share);

  // Format sources for ProtocolList
  const sources = (s?.top_source_ips || []).map(item => ({
    ip: item.ip,
    packets: item.count,
  }));

  return (
    <div className="min-h-screen">
      <Navbar />

      <main className="mx-auto max-w-7xl px-6 pb-24 pt-6 md:px-10">
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10 flex flex-col gap-2"
        >
          <span className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Overview
          </span>
          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
            Network at a glance
          </h1>
          <p className="max-w-xl text-sm text-muted-foreground">
            Real-time traffic, protocol distribution, and security signals across
            your monitored infrastructure.
          </p>
        </motion.section>

        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            index={0}
            label="Total Packets"
            value={s ? s.total_packets.toLocaleString() : "—"}
            trend={0}
            icon={Activity}
          />
          <StatCard
            index={1}
            label="Active Connections"
            value={s ? s.active_connections_count.toLocaleString() : "—"}
            trend={0}
            icon={Network}
          />
          <StatCard
            index={2}
            label="Bandwidth"
            value={s ? `${(s.bandwidth_bytes_per_second / 1024 / 1024 * 8).toFixed(1)} Mbps` : "—"}
            trend={0}
            icon={Wifi}
          />
          <StatCard
            index={3}
            label="PPS"
            value={s ? `${s.packets_per_second.toLocaleString()}` : "—"}
            trend={0}
            icon={ShieldAlert}
          />
        </section>

        <section className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-8">
            <TrafficChart data={series} />
          </div>
          <div className="lg:col-span-4">
            <ProtocolList
              protocols={protocols}
              sources={sources}
            />
          </div>
        </section>

        <section className="mt-8">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1, ease: 'easeOut' }}
          >
            <div className="mb-4">
              <span className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Geo intelligence
              </span>
              <h2 className="mt-1 text-lg font-semibold tracking-tight">
                Traffic origins
              </h2>
              <p className="text-sm text-muted-foreground">
                Live geo-resolved source and destination IPs
              </p>
            </div>
            <GlobeMap points={liveGeoPoints} />
            <GlobeStats points={liveGeoPoints} />
          </motion.div>
        </section>

        <section className="mt-12">
          {graphQuery.data && <NetworkGraph
            data={graphQuery.data ?? { nodes: [], edges: [] }}
          />}
        </section>

        <section className="mt-12">
          <AlertFeed alerts={alertsQuery.data || []} />
        </section>

        <section className="mt-12">
          <PacketLogs initial={packetsQuery.data || []} />
        </section>
      </main>
    </div>
  );
}
