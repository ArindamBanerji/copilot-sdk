import { useEffect, useState } from "react";
import { getNoveltyStatus, getNoveltyTriggeredDecisions } from "../api";
import type { NoveltyHistoryEntry, NoveltyStatusResponse } from "../types";

function percent(value?: number): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "0%";
}

function label(value?: string): string {
  return String(value || "unknown").replace(/_/g, " ");
}

function topCategory(status: NoveltyStatusResponse | null): string {
  const rows = Object.entries(status?.per_category || {});
  let selected = "";
  let selectedRate = -1;
  for (const [category, raw] of rows) {
    const rate = typeof raw === "number" ? raw : Number(raw.novelty_rate || 0);
    if (rate > selectedRate) {
      selected = category;
      selectedRate = rate;
    }
  }
  return selected || "category";
}

export default function NoveltyAlertBanner() {
  const [status, setStatus] = useState<NoveltyStatusResponse | null>(null);
  const [decisions, setDecisions] = useState<NoveltyHistoryEntry[]>([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getNoveltyStatus(), getNoveltyTriggeredDecisions(5)])
      .then(([nextStatus, nextDecisions]) => {
        if (cancelled) return;
        setStatus(nextStatus);
        setDecisions(nextDecisions?.decisions || []);
      })
      .catch(() => {
        if (!cancelled) {
          setStatus(null);
          setDecisions([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!status?.conservation_review && !status?.alert_active) {
    return null;
  }

  const category = topCategory(status);

  return (
    <article className="rounded-lg border border-amber-300 bg-amber-50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Novelty alert</p>
          <h2 className="mt-1 text-lg font-semibold text-amber-950">
            Novelty spike detected in {label(category)}
          </h2>
          <p className="mt-1 text-sm text-amber-900">
            {status.novelty_count} unusual decisions in the last {status.total_in_window} decisions.
            Conservation under review at {percent(status.novelty_rate)} novelty rate.
          </p>
        </div>
        <span className="rounded-full bg-amber-200 px-3 py-1 text-xs font-semibold text-amber-900">
          {status.status || "AMBER"}
        </span>
      </div>
      {status.recommendation ? <p className="mt-3 text-sm text-amber-900">{status.recommendation}</p> : null}
      <button
        type="button"
        className="mt-3 rounded-md border border-amber-400 bg-white px-3 py-2 text-sm font-semibold text-amber-900"
        onClick={() => setExpanded((value) => !value)}
      >
        What triggered this?
      </button>
      {expanded ? (
        <div className="mt-3 grid gap-2">
          {decisions.length === 0 ? (
            <p className="text-sm text-amber-900">No triggered decisions are currently available.</p>
          ) : (
            decisions.map((decision) => (
              <div key={decision.sequence} className="rounded-md bg-white p-3 text-sm text-slate-700">
                Decision {decision.sequence}: {label(decision.category)} distance {Number(decision.nearest_distance || 0).toFixed(2)}
              </div>
            ))
          )}
        </div>
      ) : null}
    </article>
  );
}
