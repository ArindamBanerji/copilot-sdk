import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchCentroidHistory } from "../api";
import type { CentroidCheckpoint, SelfCentroidHistoryResponse } from "../types";

const colors = ["#7c3aed", "#2563eb", "#059669", "#d97706", "#dc2626", "#0891b2"];

type TimelineRow = {
  label: string;
  drift: number;
  iks: number | null;
  phase: string;
  [key: string]: string | number | null;
};

export default function CentroidTimelinePanel() {
  const [data, setData] = useState<SelfCentroidHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchCentroidHistory(50)
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const chart = useMemo(() => buildTimeline(data?.checkpoints || []), [data]);

  if (error) return null;
  if (loading) {
    return (
      <section data-testid="centroid-timeline" className="copilot-card p-5">
        <p className="text-sm dataops-muted">Loading centroid timeline...</p>
      </section>
    );
  }

  if (chart.rows.length === 0) {
    return (
      <section data-testid="centroid-timeline" className="copilot-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
          SC-11
        </p>
        <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
          Centroid Timeline
        </h2>
        <p className="mt-2 text-sm dataops-muted">No centroid history yet. Score some alerts to see learning.</p>
      </section>
    );
  }

  const current = chart.rows[chart.rows.length - 1];
  const currentDrift = typeof current.drift === "number" ? current.drift : 0;

  return (
    <section data-testid="centroid-timeline" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-11 · TRAJECTORY OF INTELLIGENCE
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Centroid Timeline
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            {data?.total ?? chart.rows.length} checkpoints from GraphStore. Centroid drift shows learning from the initial prior.
          </p>
        </div>
        <div data-testid="centroid-current-drift" className="rounded-md px-3 py-2" style={{ background: "rgba(124, 58, 237, 0.1)" }}>
          <p className="text-xs font-semibold uppercase tracking-wide dataops-muted">Current drift</p>
          <p className="mt-1 text-lg font-semibold" style={{ color: "var(--copilot-primary)" }}>{currentDrift.toFixed(3)}</p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-xs" data-testid="centroid-phases">
        {chart.phases.map((phase) => (
          <span key={phase} className="rounded-full border px-2 py-1 dataops-muted">{phase}</span>
        ))}
      </div>

      <div className="mt-4 h-80" data-testid="centroid-timeline-chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chart.rows} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.35)" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="drift" domain={[0, "auto"]} tick={{ fontSize: 12 }} label={{ value: "Drift", angle: -90, position: "insideLeft" }} />
            <YAxis yAxisId="iks" orientation="right" domain={[0, 1]} tick={{ fontSize: 12 }} label={{ value: "IKS", angle: 90, position: "insideRight" }} />
            <Tooltip />
            <Legend />
            {chart.keys.map((key, index) => (
              <Line key={key} yAxisId="drift" type="monotone" dataKey={key} name={formatCategory(key)} stroke={colors[index % colors.length]} strokeWidth={2} dot={{ r: 2 }} connectNulls />
            ))}
            <Line yAxisId="drift" type="monotone" dataKey="drift" name="Centroid drift" stroke="#111827" strokeWidth={3} dot={false} />
            <Line yAxisId="iks" type="monotone" dataKey="iks" name="IKS" stroke="#e11d48" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 2 }} connectNulls />
            {chart.phaseMarkers.map((marker) => (
              <ReferenceLine key={`${marker.phase}-${marker.index}`} x={marker.label} yAxisId="drift" stroke="#94a3b8" strokeDasharray="4 4" label={{ value: marker.phase, position: "insideTop", fontSize: 11 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function buildTimeline(checkpoints: CentroidCheckpoint[]) {
  const keys = new Set<string>();
  const initial: Record<string, number> = {};
  const rows: TimelineRow[] = checkpoints.map((checkpoint, index) => {
    const row: TimelineRow = {
      label: checkpoint.checkpointTime
        ? String(checkpoint.checkpointTime).slice(0, 10)
        : checkpoint.createdAt
          ? String(checkpoint.createdAt).slice(0, 10)
          : String(index + 1),
      drift: 0,
      iks: numericValue(checkpoint.iks ?? checkpoint.metadata?.iks ?? checkpoint.metadata?.IKS),
      phase: textValue(checkpoint.metadata?.phase) || phaseFor(index, checkpoints.length),
    };
    for (const [key, value] of Object.entries(checkpoint.centroids || {})) {
      const number = centroidValue(value);
      if (number === null) continue;
      keys.add(key);
      initial[key] ??= number;
      row[key] = number;
    }
    row.drift = Math.sqrt(Array.from(keys).reduce((sum, key) => {
      const value = typeof row[key] === "number" ? row[key] as number : initial[key];
      return sum + (value - initial[key]) ** 2;
    }, 0));
    return row;
  });
  const phases = Array.from(new Set(rows.map((row) => row.phase)));
  const phaseMarkers = rows.filter((row, index) => index === 0 || row.phase !== rows[index - 1]?.phase).map((row, index) => ({ phase: row.phase, label: row.label, index }));
  return { rows, keys: Array.from(keys).sort(), phases, phaseMarkers };
}

function centroidValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (Array.isArray(value)) {
    const numbers = value.map(Number).filter(Number.isFinite);
    return numbers.length ? numbers.reduce((sum, item) => sum + item, 0) / numbers.length : null;
  }
  return null;
}

function numericValue(value: unknown): number | null {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function textValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function phaseFor(index: number, total: number): string {
  if (index === 0) return "bootstrap";
  if (index >= Math.max(1, total - 2)) return "converged";
  return "learning";
}

function formatCategory(value: string): string {
  return value.replace(/[_-]/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
