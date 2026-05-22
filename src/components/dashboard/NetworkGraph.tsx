import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import type { GraphData, GraphNode } from "@/services/api";

type Pos = { x: number; y: number };

const W = 720;
const H = 360;

const kindColor: Record<GraphNode["kind"], string> = {
  host: "oklch(0.78 0.14 220)",
  source: "oklch(0.68 0.18 275)",
  destination: "oklch(0.72 0.16 155)",
  domain: "oklch(0.78 0.16 75)",
};

function layout(nodes: GraphNode[]): Record<string, Pos> {
  const pos: Record<string, Pos> = {};

  const host = nodes.find((n) => n.kind === "host");
  const sources = nodes.filter((n) => n.kind === "source");
  const dests = nodes.filter(
    (n) => n.kind !== "host" && n.kind !== "source"
  );

  if (host) {
    pos[String(host.id)] = {
      x: W / 2,
      y: H / 2,
    };
  }

  sources.forEach((n, i) => {
    const t = (i + 1) / (sources.length + 1);

    pos[String(n.id)] = {
      x: 90,
      y: 50 + t * (H - 100),
    };
  });

  dests.forEach((n, i) => {
    const t = (i + 1) / (dests.length + 1);

    pos[String(n.id)] = {
      x: W - 90,
      y: 50 + t * (H - 100),
    };
  });

  return pos;
}

export function NetworkGraph({
  data,
}: {
  data: GraphData;
}) {
  const pos = useMemo(
    () => layout(data.nodes),
    [data.nodes]
  );

  const [hover, setHover] =
    useState<GraphNode | null>(null);

  return (
    <div className="glass-panel relative overflow-hidden rounded-2xl p-6">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <span className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Topology
          </span>

          <h2 className="mt-1 text-lg font-semibold tracking-tight">
            Live Network Graph
          </h2>
        </div>

        <div className="flex gap-3 text-xs text-muted-foreground">
          <Legend
            color={kindColor.source}
            label="Source"
          />
          <Legend
            color={kindColor.host}
            label="Host"
          />
          <Legend
            color={kindColor.domain}
            label="Domain"
          />
        </div>
      </div>

      <div className="relative">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="h-[360px] w-full"
        >
          <defs>
            <linearGradient
              id="edgeGrad"
              x1="0"
              x2="1"
            >
              <stop
                offset="0%"
                stopColor="oklch(0.68 0.18 275 / .1)"
              />

              <stop
                offset="50%"
                stopColor="oklch(0.78 0.14 230 / .7)"
              />

              <stop
                offset="100%"
                stopColor="oklch(0.68 0.18 275 /.1)"
              />
            </linearGradient>

            <filter id="glow">
              <feGaussianBlur
                stdDeviation="6"
                result="blur"
              />

              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {data.edges.map((e, i) => {
            const a = pos[String(e.source)];
            const b = pos[String(e.target)];

            if (!a || !b) {
              console.warn(
                "Missing edge:",
                e
              );

              return null;
            }

            const mx =
              (a.x + b.x) / 2;

            const my =
              (a.y + b.y) / 2 - 30;

            const d = `M ${a.x} ${a.y}
                       Q ${mx} ${my}
                       ${b.x} ${b.y}`;

            const weight =
              e.weight || 1;

            return (
              <g
                key={`${e.source}-${e.target}-${i}`}
              >
                <path
                  d={d}
                  fill="none"
                  stroke="url(#edgeGrad)"
                  strokeWidth={Math.max(
                    1,
                    weight / 4
                  )}
                  opacity={0.7}
                />

                <motion.circle
                  r={Math.max(
                    2,
                    Math.min(
                      8,
                      weight / 5
                    )
                  )}
                  fill="oklch(0.85 0.12 230)"
                  initial={{
                    offsetDistance:
                      "0%",
                  }}
                  animate={{
                    offsetDistance:
                      "100%",
                  }}
                  transition={{
                    duration: Math.max(
                      1.5,
                      5 -
                        weight /
                          10
                    ),
                    repeat:
                      Infinity,
                    ease:
                      "linear",
                  }}
                  style={
                    {
                      offsetPath: `path("${d}")`,
                    } as React.CSSProperties
                  }
                />
              </g>
            );
          })}

          {data.nodes.map((n) => {
            const p =
              pos[String(n.id)];

            if (!p) return null;

            const c =
              kindColor[
                n.kind
              ];

            const r =
              n.kind ===
              "host"
                ? 16
                : 9;

            return (
              <g
                key={n.id}
                transform={`translate(${p.x} ${p.y})`}
                onMouseEnter={() =>
                  setHover(
                    n
                  )
                }
                onMouseLeave={() =>
                  setHover(
                    null
                  )
                }
                style={{
                  cursor:
                    "pointer",
                }}
              >
                <circle
                  r={r * 2.4}
                  fill={c}
                  opacity={0.15}
                  filter="url(#glow)"
                />

                <motion.circle
                  r={r}
                  fill={c}
                  fillOpacity={
                    0.2
                  }
                  stroke={c}
                  strokeWidth={
                    1.5
                  }
                  animate={{
                    scale: [
                      1,
                      1.15,
                      1,
                    ],
                  }}
                  transition={{
                    duration: 2,
                    repeat:
                      Infinity,
                  }}
                />

                <circle
                  r={
                    r *
                    0.45
                  }
                  fill={c}
                />

                <text
                  y={
                    r +
                    16
                  }
                  textAnchor="middle"
                  fontSize="10"
                  fill="white"
                >
                  {n.label}
                </text>
              </g>
            );
          })}
        </svg>

        {hover && (
          <motion.div
            initial={{
              opacity: 0,
              y: 4,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            className="glass-panel absolute right-4 top-4 rounded-xl p-4 text-xs"
          >
            <div className="mb-1 uppercase tracking-widest text-muted-foreground">
              {hover.kind}
            </div>

            <div className="font-semibold">
              {hover.label}
            </div>

            <div className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1">
              <span>
                Protocol
              </span>
              <span>
                {
                  hover.protocol
                }
              </span>

              <span>
                Packets
              </span>
              <span>
                {hover.packets.toLocaleString()}
              </span>

              <span>
                Bandwidth
              </span>
              <span>
                {hover.bandwidthMbps.toFixed(
                  1
                )}{" "}
                Mbps
              </span>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

function Legend({
  color,
  label,
}: {
  color: string;
  label: string;
}) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className="h-2 w-2 rounded-full"
        style={{
          background:
            color,
          boxShadow: `0 0 10px ${color}`,
        }}
      />
      {label}
    </span>
  );
}