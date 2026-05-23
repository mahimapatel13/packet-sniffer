import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Globe, Shield, MapPin, Navigation } from 'lucide-react';
import { GeoPointDTO } from '@/services/types';

interface GlobeStatsProps {
  points: GeoPointDTO[];
}

// Helper for flag emojis from ISO country code
function getFlagEmoji(countryCode: string) {
  if (!countryCode || countryCode.length !== 2) return '🌐';
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

export function GlobeStats({ points }: GlobeStatsProps) {
  const stats = useMemo(() => {
    const countries = new Set(points.map(p => p.country_code));
    const totalIPs = points.length;
    
    // Top source
    const sources = points.filter(p => p.direction === 'source');
    const topSource = sources.length > 0 
      ? sources.reduce((prev, curr) => (curr.count > prev.count ? curr : prev))
      : null;

    // Top destination
    const destinations = points.filter(p => p.direction === 'destination');
    const topDest = destinations.length > 0
      ? destinations.reduce((prev, curr) => (curr.count > prev.count ? curr : prev))
      : null;

    // Top 8 countries for list
    const countryMap: Record<string, { 
      name: string; 
      count: number; 
      code: string; 
      directions: Set<'source' | 'destination'> 
    }> = {};

    points.forEach(p => {
      if (!countryMap[p.country_code]) {
        countryMap[p.country_code] = { 
          name: p.country_name, 
          count: 0, 
          code: p.country_code,
          directions: new Set()
        };
      }
      countryMap[p.country_code].count += p.count;
      countryMap[p.country_code].directions.add(p.direction);
    });

    const topCountries = Object.values(countryMap)
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);

    const maxCount = topCountries.length > 0 ? topCountries[0].count : 1;

    return {
      countriesCount: countries.size,
      totalIPs,
      topSource,
      topDest,
      topCountries,
      maxCount
    };
  }, [points]);

  return (
    <div className="mt-6 space-y-6">
      {/* Stat Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatItem 
          label="Countries reached" 
          value={stats.countriesCount.toString()} 
          icon={Globe}
        />
        <StatItem 
          label="Geo-resolved IPs" 
          value={stats.totalIPs.toString()} 
          icon={Shield}
        />
        <StatItem 
          label="Top source" 
          value={stats.topSource ? `${getFlagEmoji(stats.topSource.country_code)} ${stats.topSource.country_name}` : '—'} 
          icon={MapPin}
          subValue={stats.topSource ? `${stats.topSource.count} packets` : undefined}
        />
        <StatItem 
          label="Top destination" 
          value={stats.topDest ? `${getFlagEmoji(stats.topDest.country_code)} ${stats.topDest.country_name}` : '—'} 
          icon={Navigation}
          subValue={stats.topDest ? `${stats.topDest.count} packets` : undefined}
        />
      </div>

      {/* Country List */}
      <div className="glass-panel overflow-hidden rounded-2xl p-6">
        <h3 className="mb-6 text-sm font-medium uppercase tracking-wider text-muted-foreground">
          Top traffic locations
        </h3>
        
        {stats.topCountries.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground opacity-50">
            No geographic data available yet
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-x-12 gap-y-6 md:grid-cols-2">
            {stats.topCountries.map((c, i) => (
              <motion.div 
                key={c.code}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="group relative flex flex-col gap-2"
              >
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{getFlagEmoji(c.code)}</span>
                    <span className="font-medium text-foreground">{c.name}</span>
                    <div className="flex gap-1 ml-2">
                      {Array.from(c.directions).map(dir => (
                        <span 
                          key={dir}
                          className={`h-1.5 w-1.5 rounded-full ${dir === 'source' ? 'bg-[#7c6fe0]' : 'bg-[#3dba8c]'}`}
                          title={dir}
                        />
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-muted-foreground">{c.count.toLocaleString()} pkts</span>
                  </div>
                </div>
                <div className="relative h-1 w-full overflow-hidden rounded-full bg-white/5">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${(c.count / stats.maxCount) * 100}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="absolute inset-y-0 left-0 bg-primary/40 group-hover:bg-primary/60 transition-colors"
                  />
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatItem({ label, value, icon: Icon, subValue }: { label: string; value: string; icon: any; subValue?: string }) {
  return (
    <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
      <div className="absolute -right-6 -top-6 h-20 w-20 rounded-full bg-primary/5 blur-2xl group-hover:bg-primary/10 transition-colors" />
      <div className="flex items-center gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-border/40 bg-card/40 text-primary">
          <Icon className="h-5 w-5" strokeWidth={1.5} />
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] font-medium uppercase tracking-[0.1em] text-muted-foreground">
            {label}
          </span>
          <span className="text-base font-semibold text-foreground truncate max-w-[150px]">
            {value}
          </span>
          {subValue && (
            <span className="text-[10px] text-muted-foreground/60 mt-0.5">
              {subValue}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
