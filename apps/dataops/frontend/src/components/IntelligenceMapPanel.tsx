import { useEffect, useMemo, useState } from "react";
import { fetchDIProfiles } from "../api";
import type { DIProfileSummary, DIProfilesResponse, DISourceSummary } from "../types";

type LoadState = "loading" | "ready" | "error";

interface MapNode {
  id: string;
  sourceName: string;
  entityType: string;
  trustTier: number | null;
  cacheStatus: string;
  hasProfile: boolean;
  profile: DIProfileSummary | null;
  recordCount: number;
  quality: number | null;
  radius: number;
  opacity: number;
  status: "healthy" | "degraded" | "offline" | "pending";
  x: number;
  y: number;
}

const MAP_WIDTH = 720;
const MIN_RADIUS = 22;
const MAX_RADIUS = 46;

export function IntelligenceMapPanel() {
  const [state, setState] = useState<LoadState>("loading");
  const [data, setData] = useState<DIProfilesResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    fetchDIProfiles()
      .then((payload) => {
        if (cancelled) {
          return;
        }
        if (!payload) {
          setState("error");
          setData(null);
          return;
        }
        setData(payload);
        setState("ready");
      })
      .catch(() => {
        if (!cancelled) {
          setState("error");
          setData(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const sources = data?.sources || [];
  const nodes = useMemo(() => buildNodes(sources), [sources]);
  const mapHeight = Math.max(190, Math.ceil(Math.max(nodes.length, 1) / Math.min(4, Math.max(1, nodes.length))) * 112 + 80);

  if (state === "loading") {
    return (
      <section className="copilot-card p-5">
        <PanelHeader total={0} />
        <p className="mt-4 text-sm dataops-muted">Loading intelligence map...</p>
      </section>
    );
  }

  if (state === "error") {
    return (
      <section className="copilot-card p-5">
        <PanelHeader total={0} />
        <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>
          Could not load DI source profiles.
        </p>
      </section>
    );
  }

  if (nodes.length === 0) {
    return (
      <section className="copilot-card p-5">
        <PanelHeader total={data?.total ?? 0} />
        <div className="mt-5 rounded-md border border-dashed border-white/15 bg-white/[0.03] p-5">
          <p className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            No connected sources.
          </p>
          <p className="mt-1 text-sm dataops-muted">
            Add connectors to build your intelligence map.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="copilot-card p-5">
      <PanelHeader total={data?.total ?? nodes.length} />
      <div className="mt-5 overflow-hidden rounded-md border border-white/10 bg-slate-950/30">
        <svg
          role="img"
          aria-label={`Intelligence map with ${nodes.length} source${nodes.length === 1 ? "" : "s"}`}
          viewBox={`0 0 ${MAP_WIDTH} ${mapHeight}`}
          className="h-auto w-full"
        >
          <title>Data Intelligence Map</title>
          <rect width={MAP_WIDTH} height={mapHeight} fill="rgba(15, 23, 42, 0.35)" />
          {nodes.map((node) => (
            <g key={node.id} transform={`translate(${node.x}, ${node.y})`} aria-label={`${node.sourceName} source node`}>
              <title>{`${node.sourceName}: ${node.entityType}, ${node.status}, ${node.recordCount} records`}</title>
              <circle
                r={node.radius + 10}
                fill={statusColor(node.status)}
                opacity={0.12 * node.opacity}
              />
              <circle
                r={node.radius}
                fill={statusColor(node.status)}
                opacity={node.opacity}
                stroke="rgba(255,255,255,0.62)"
                strokeWidth="1.5"
              />
              <text
                y={node.radius + 24}
                textAnchor="middle"
                className="fill-white text-[13px] font-semibold"
              >
                {truncate(node.sourceName, 18)}
              </text>
              <text
                y={node.radius + 41}
                textAnchor="middle"
                className="fill-slate-300 text-[11px]"
              >
                {truncate(node.entityType, 20)}
              </text>
            </g>
          ))}
        </svg>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs dataops-muted">
        <span>Correlations pending connector data.</span>
        <span>IKS pending</span>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {nodes.map((node) => (
          <SourceCard key={node.id} node={node} />
        ))}
      </div>
    </section>
  );
}

function PanelHeader({ total }: { total: number }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
          Intelligence Map
        </p>
        <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
          Source trust and quality graph
        </h2>
        <p className="mt-1 text-sm dataops-muted">
          DI source profiles rendered from the shared profiler registry.
        </p>
      </div>
      <span className="rounded-md border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-slate-200">
        {total} sources
      </span>
    </div>
  );
}

function SourceCard({ node }: { node: MapNode }) {
  const qualityLabel = node.quality === null ? "pending" : `${Math.round(node.quality * 100)}%`;
  return (
    <div className="rounded-md border border-white/10 bg-white/[0.04] p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            {node.sourceName}
          </p>
          <p className="text-xs dataops-muted">{node.entityType}</p>
        </div>
        <span className={`rounded-md px-2 py-1 text-xs font-semibold ${statusClass(node.status)}`}>
          {node.status}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
        <Metric label="Quality" value={qualityLabel} />
        <Metric label="Records" value={formatNumber(node.recordCount)} />
        <Metric label="Trust" value={node.trustTier === null ? "n/a" : `T${node.trustTier}`} />
      </div>
      <p className="mt-3 text-xs dataops-muted">
        Cache: {node.cacheStatus || "unknown"} - IKS pending
      </p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-slate-950/30 px-2 py-2">
      <p className="uppercase tracking-[0.14em] text-slate-400">{label}</p>
      <p className="mt-1 font-semibold text-slate-100">{value}</p>
    </div>
  );
}

function buildNodes(sources: DISourceSummary[]): MapNode[] {
  const count = sources.length;
  const columns = Math.min(4, Math.max(1, Math.ceil(Math.sqrt(Math.max(count, 1)))));
  const cellWidth = MAP_WIDTH / (columns + 1);
  const cellHeight = 112;

  return sources.map((source, index) => {
    const profile = latestProfile(source);
    const sourceName = text(source.sourceName ?? source.source_name, `source-${index + 1}`);
    const entityType = text(source.entityType ?? source.entity_type, "unknown entity");
    const trustTier = optionalNumber(source.trustTier ?? source.trust_tier);
    const hasProfile = Boolean(source.hasProfile ?? source.has_profile ?? profile);
    const cacheStatus = text(source.cacheStatus ?? source.cache_status, hasProfile ? "unknown" : "not_profiled");
    const recordCount = Math.max(0, optionalNumber(profile?.recordCount ?? profile?.record_count) ?? 0);
    const quality = qualityScore(profile, source);
    const status = statusFor(hasProfile, quality, cacheStatus);
    const radius = radiusFor(recordCount);
    const opacity = opacityFor(quality, trustTier, cacheStatus, hasProfile);
    const column = index % columns;
    const row = Math.floor(index / columns);

    return {
      id: `${sourceName}-${index}`,
      sourceName,
      entityType,
      trustTier,
      cacheStatus,
      hasProfile,
      profile,
      recordCount,
      quality,
      radius,
      opacity,
      status,
      x: cellWidth * (column + 1),
      y: 70 + row * cellHeight,
    };
  });
}

function latestProfile(source: DISourceSummary): DIProfileSummary | null {
  return source.latestProfile || source.latest_profile || null;
}

function qualityScore(profile: DIProfileSummary | null, source: DISourceSummary): number | null {
  const value = optionalNumber(profile?.overallQuality ?? profile?.overall_quality);
  if (value !== null) {
    return clamp(value, 0, 1);
  }
  const hasProfile = Boolean(source.hasProfile ?? source.has_profile ?? profile);
  return hasProfile ? null : null;
}

function statusFor(hasProfile: boolean, quality: number | null, cacheStatus: string): MapNode["status"] {
  if (!hasProfile) {
    return "pending";
  }
  if (quality === null) {
    return cacheStatus === "stale" ? "degraded" : "pending";
  }
  if (quality > 0.8) {
    return "healthy";
  }
  if (quality > 0.5) {
    return "degraded";
  }
  return "offline";
}

function radiusFor(recordCount: number): number {
  if (recordCount <= 0) {
    return MIN_RADIUS;
  }
  return clamp(MIN_RADIUS + Math.log10(recordCount + 1) * 9, MIN_RADIUS, MAX_RADIUS);
}

function opacityFor(quality: number | null, trustTier: number | null, cacheStatus: string, hasProfile: boolean): number {
  if (quality !== null) {
    return clamp(0.35 + quality * 0.65, 0.35, 1);
  }
  if (!hasProfile) {
    return 0.42;
  }
  if (trustTier !== null) {
    return clamp(0.92 - Math.max(0, trustTier - 1) * 0.12, 0.45, 0.92);
  }
  return cacheStatus === "stale" ? 0.52 : 0.62;
}

function statusColor(status: MapNode["status"]): string {
  if (status === "healthy") {
    return "#34d399";
  }
  if (status === "degraded") {
    return "#fbbf24";
  }
  if (status === "offline") {
    return "#f87171";
  }
  return "#94a3b8";
}

function statusClass(status: MapNode["status"]): string {
  if (status === "healthy") {
    return "bg-emerald-500/15 text-emerald-100";
  }
  if (status === "degraded") {
    return "bg-amber-500/15 text-amber-100";
  }
  if (status === "offline") {
    return "bg-rose-500/15 text-rose-100";
  }
  return "bg-slate-500/15 text-slate-200";
}

function optionalNumber(value: unknown): number | null {
  const numberValue = typeof value === "number" ? value : typeof value === "string" ? Number(value) : NaN;
  return Number.isFinite(numberValue) ? numberValue : null;
}

function text(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function truncate(value: string, maxLength: number): string {
  return value.length > maxLength ? `${value.slice(0, maxLength - 1)}...` : value;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(value);
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
