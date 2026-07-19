import { useEffect, useMemo, useState } from "react";
import { fetchCentroidHistory } from "../api";
import type { CentroidCheckpoint, SelfCentroidHistoryResponse } from "../types";

export default function CentroidTimeline() {
  const [data, setData] = useState<SelfCentroidHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkpoints = Array.isArray(data?.checkpoints) ? data.checkpoints : [];
  const rows = useMemo(() => buildRows(checkpoints), [checkpoints]);

  useEffect(() => {
    let cancelled = false;
    fetchCentroidHistory(50)
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((loadError) => {
        console.debug("centroid timeline unavailable", loadError);
        if (!cancelled) setError("Centroid timeline unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-11
          </p>
          <h2 className="mt-1 text-xl font-semibold">Centroid Timeline</h2>
          <p className="mt-1 text-sm trading-muted">{data?.total ?? checkpoints.length} checkpoints from trading GraphStore decisions.</p>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm trading-muted">Centroid timeline unavailable.</p> : null}
      {!error && loading ? <p className="mt-4 text-sm trading-muted">Loading centroid timeline...</p> : null}
      {!error && !loading && rows.length === 0 ? (
        <p className="mt-4 text-sm trading-muted">No centroid history yet. Score more trades to see learning.</p>
      ) : null}
      {!error && !loading && rows.length > 0 ? (
        <div className="mt-4 grid gap-3">
          {rows.map((row) => (
            <div key={row.key}>
              <div className="mb-1 flex items-center justify-between gap-3 text-sm">
                <span className="font-medium">{humanize(row.key)}</span>
                <span className="trading-muted">{Math.round(row.value * 100)}%</span>
              </div>
              <div className="trading-bar-track">
                <div className="trading-bar-fill" style={{ width: `${Math.round(row.value * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function buildRows(checkpoints: CentroidCheckpoint[]) {
  const latest = checkpoints[checkpoints.length - 1];
  return Object.entries(latest?.centroids || {})
    .map(([key, value]) => ({ key, value: centroidValue(value) }))
    .filter((row): row is { key: string; value: number } => row.value !== null)
    .sort((left, right) => right.value - left.value);
}

function centroidValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return clamp(value);
  if (Array.isArray(value)) {
    const numbers = value.map(Number).filter(Number.isFinite);
    if (numbers.length === 0) return null;
    return clamp(numbers.reduce((sum, item) => sum + item, 0) / numbers.length);
  }
  return null;
}

function clamp(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}
