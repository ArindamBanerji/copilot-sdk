import { useEffect, useMemo, useState } from "react";

import { fetchCentroidHistory } from "../api";
import type { CentroidCheckpoint } from "../types";

function centroidValues(checkpoint?: CentroidCheckpoint): Record<string, number> {
  const raw = checkpoint?.centroids;
  if (!raw) return {};
  if (Array.isArray(raw)) {
    return Object.fromEntries(raw.slice(0, 6).map((value, index) => [`factor_${index + 1}`, Number(value) || 0]));
  }
  return Object.fromEntries(Object.entries(raw).map(([key, value]) => [key, Number(value) || 0]));
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export function CentroidTimelineChart() {
  const [checkpoints, setCheckpoints] = useState<CentroidCheckpoint[] | null>(null);

  useEffect(() => {
    let active = true;
    fetchCentroidHistory(50).then((response) => {
      if (active) setCheckpoints(response?.checkpoints ?? []);
    });
    return () => {
      active = false;
    };
  }, []);

  const latest = useMemo(() => centroidValues(checkpoints?.[checkpoints.length - 1]), [checkpoints]);
  const latestQuality = checkpoints?.[checkpoints.length - 1]?.quality;
  const entries = Object.entries(latest).slice(0, 8);

  return (
    <section className="purchase-card" data-panel-ready={String(checkpoints !== null)}>
      <p className="purchase-kicker">SC-11 Centroid History</p>
      <h3 className="purchase-title">Learning centroid timeline</h3>
      {!checkpoints ? (
        <p className="purchase-muted">Loading...</p>
      ) : checkpoints.length === 0 ? (
        <p className="purchase-muted">No centroid history yet. Score purchase orders to see learning.</p>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs uppercase tracking-[0.18em] text-slate-500">
            <span>{checkpoints.length} checkpoints</span>
            <span>factor weight</span>
          </div>
          {latestQuality?.rolling_accuracy != null ? (
            <p data-testid="centroid-quality" className="text-sm text-slate-600">
              Rolling accuracy: {(latestQuality.rolling_accuracy * 100).toFixed(1)}% ({latestQuality.correct_count}/{latestQuality.verified_count})
            </p>
          ) : null}
          {entries.map(([key, value]) => (
            <div key={key}>
              <div className="flex items-center justify-between text-sm">
                <span className="capitalize text-slate-700">{label(key)}</span>
                <span className="font-semibold text-slate-900">{Math.round(value * 100)}%</span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-slate-200">
                <div
                  className="h-2 rounded-full bg-emerald-500"
                  style={{ width: `${Math.max(4, Math.min(100, value * 100))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
