import { useEffect, useMemo, useState } from "react";
import { fetchCentroidHistory } from "../api";
import type { SelfCentroidHistoryResponse } from "../types";

export default function CentroidTimelineChart() {
  const [data, setData] = useState<SelfCentroidHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchCentroidHistory(50)
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const rows = useMemo(() => flatten(data), [data]);
  if (loading) return <section className="copilot-card p-4 text-sm trading-muted">Loading centroid history...</section>;
  if (rows.length === 0) return <section className="copilot-card p-4 text-sm trading-muted">No centroid history yet. Log trades to see learning.</section>;

  return (
    <section className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase" style={{ color: "var(--copilot-primary)" }}>SC-11</p>
      <h2 className="mt-1 text-xl font-semibold">Centroid History</h2>
      <p className="mt-1 text-sm trading-muted">{data?.total ?? 0} checkpoints from GraphStore.</p>
      <div className="mt-4 grid gap-3">
        {rows.map((row) => (
          <div key={row.key}>
            <div className="mb-1 flex justify-between text-sm">
              <span>{row.key.replace(/_/g, " ")}</span>
              <strong>{Math.round(row.value * 100)}%</strong>
            </div>
            <div className="trading-bar-track">
              <div className="trading-bar-fill" style={{ width: `${Math.round(row.value * 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function flatten(data: SelfCentroidHistoryResponse | null) {
  const latest = data?.checkpoints?.[data.checkpoints.length - 1];
  return Object.entries(latest?.centroids || {})
    .map(([key, value]) => ({ key, value: centroidValue(value) }))
    .filter((row): row is { key: string; value: number } => row.value !== null)
    .sort((a, b) => b.value - a.value);
}

function centroidValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return clamp(value);
  if (Array.isArray(value)) {
    const nums = value.map(Number).filter(Number.isFinite);
    if (nums.length === 0) return null;
    return clamp(nums.reduce((sum, item) => sum + item, 0) / nums.length);
  }
  return null;
}

function clamp(value: number) {
  return Math.max(0, Math.min(1, value));
}
