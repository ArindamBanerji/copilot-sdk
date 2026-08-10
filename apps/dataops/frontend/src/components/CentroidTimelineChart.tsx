import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchCentroidHistory } from "../api";
import type { SelfCentroidHistoryResponse } from "../types";

const colors = ["#7c3aed", "#2563eb", "#059669", "#d97706", "#dc2626", "#0891b2", "#4f46e5"];

export default function CentroidTimelineChart() {
  const [data, setData] = useState<SelfCentroidHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    fetchCentroidHistory(50)
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const checkpoints = data?.checkpoints || [];
  const chart = useMemo(() => buildRows(checkpoints), [checkpoints]);
  const latestQuality = checkpoints[checkpoints.length - 1]?.quality;

  if (error) {
    return null;
  }
  if (loading) {
    return <section className="copilot-card p-4 text-sm dataops-muted">Loading...</section>;
  }
  if (chart.rows.length === 0 || chart.keys.length === 0) {
    return <section className="copilot-card p-4 text-sm dataops-muted">No centroid history yet. Score some alerts to see learning.</section>;
  }

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-11
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Centroid History
          </h2>
          <p className="mt-1 text-sm dataops-muted">{data?.total ?? checkpoints.length} checkpoints from GraphStore.</p>
          {latestQuality?.rolling_accuracy != null && (
            <p data-testid="centroid-quality" className="mt-1 text-sm dataops-muted">
              Rolling accuracy: {(latestQuality.rolling_accuracy * 100).toFixed(1)}% ({latestQuality.correct_count}/{latestQuality.verified_count})
            </p>
          )}
        </div>
      </div>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chart.rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.35)" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
            <Tooltip />
            {chart.keys.map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={{ r: 2 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function buildRows(checkpoints: NonNullable<SelfCentroidHistoryResponse["checkpoints"]>) {
  const keys = new Set<string>();
  const rows = checkpoints.map((checkpoint, index) => {
    const row: Record<string, number | string> = {
      label: checkpoint.createdAt ? String(checkpoint.createdAt).slice(0, 10) : String(index + 1),
    };
    for (const [key, value] of Object.entries(checkpoint.centroids || {})) {
      const numeric = centroidValue(value);
      if (numeric !== null) {
        keys.add(key);
        row[key] = numeric;
      }
    }
    return row;
  });
  return { rows, keys: Array.from(keys).sort() };
}

function centroidValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return clamp(value);
  }
  if (Array.isArray(value)) {
    const numbers = value.map(Number).filter(Number.isFinite);
    if (numbers.length === 0) {
      return null;
    }
    return clamp(numbers.reduce((sum, item) => sum + item, 0) / numbers.length);
  }
  return null;
}

function clamp(value: number): number {
  return Math.max(0, Math.min(1, value));
}
