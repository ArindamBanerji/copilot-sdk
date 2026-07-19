import { useEffect, useMemo, useState } from "react";
import {
  getPromotionDashboard,
  promoteCategory,
  type PromotionDashboardResponse,
  type PromotionDetailResponse,
  type PromotionHistoryEntry,
} from "../api";

const categoryOrder = ["trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"];

function ensureArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function label(value: string | null | undefined): string {
  if (!value) return "-";
  return value.replace(/_/g, " ");
}

function stageLabel(stage: string | null | undefined, fallback?: string | null): string {
  if (fallback) return fallback.replace(/\b\w/g, (letter) => letter.toUpperCase());
  if (stage === "small_live") return "Small position";
  if (stage === "full_live") return "Full position";
  return "Paper trading";
}

function pct(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "-";
}

function stageClass(stage: string | null | undefined): string {
  if (stage === "full_live") return "border-emerald-400/40 bg-emerald-400/10 text-emerald-100";
  if (stage === "small_live") return "border-sky-400/40 bg-sky-400/10 text-sky-100";
  return "border-white/15 bg-white/10 text-slate-100";
}

function readyClass(ready: boolean | undefined): string {
  return ready ? "text-emerald-200" : "text-amber-200";
}

function sortRows(rows: PromotionDashboardResponse): PromotionDashboardResponse {
  return [...rows].sort((left, right) => {
    const leftIndex = categoryOrder.indexOf(String(left.category || ""));
    const rightIndex = categoryOrder.indexOf(String(right.category || ""));
    return (leftIndex === -1 ? 99 : leftIndex) - (rightIndex === -1 ? 99 : rightIndex);
  });
}

function HistoryList({ category, history }: { category: string; history: PromotionHistoryEntry[] }) {
  const items = ensureArray(history).slice(-3).reverse();
  return (
    <div data-testid={`promotion-history-${category}`} className="mt-4 rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs font-semibold uppercase tracking-wide trading-muted">Promotion history</div>
      {items.length ? (
        <ul className="mt-2 grid gap-2 text-sm">
          {items.map((event, index) => (
            <li key={`${event.timestamp || "event"}-${index}`} className="trading-muted">
              {label(event.action)} from {stageLabel(event.fromStage)} to {stageLabel(event.toStage)}
              {event.reason ? ` - ${event.reason}` : ""}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm trading-muted">No promotion events yet.</p>
      )}
    </div>
  );
}

export default function PromotionDashboard() {
  const [rows, setRows] = useState<PromotionDashboardResponse>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [promoting, setPromoting] = useState<string | null>(null);

  const categories = useMemo(() => sortRows(rows), [rows]);

  useEffect(() => {
    let cancelled = false;
    getPromotionDashboard()
      .then((payload) => {
        if (!cancelled) setRows(payload);
      })
      .catch((loadError) => {
        console.debug("promotion pipeline unavailable", loadError);
        if (!cancelled) setError("Promotion pipeline unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onPromote(row: PromotionDetailResponse) {
    const category = String(row.category || "");
    if (!category || !row.ready) return;
    setPromoting(category);
    setError(null);
    try {
      await promoteCategory(category);
      setRows(await getPromotionDashboard());
    } catch (promoteError) {
      console.debug("Promotion request rejected", promoteError);
      setError("Promotion is not ready yet.");
    } finally {
      setPromoting(null);
    }
  }

  return (
    <section data-testid="promotion-dashboard" className="copilot-card p-5">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">Promotion pipeline</p>
          <h2 className="mt-1 text-xl font-semibold">Strategy Promotion</h2>
          <p className="mt-2 text-sm trading-muted">
            Category stages use verified decisions, accuracy, and conservation status before increasing size.
          </p>
        </div>
      </div>

      {loading ? <div className="mt-4 text-sm trading-muted">Loading promotion pipeline...</div> : null}
      {error ? <div className="mt-4 rounded-md border border-amber-300/40 p-3 text-sm text-amber-100">{error}</div> : null}

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        {categories.map((row) => {
          const category = String(row.category || "unknown");
          const stage = String(row.currentStage || "paper");
          const evidence = row.evidence || {};
          const blockers = ensureArray(row.blockers);
          const history = ensureArray(row.state?.promotionHistory);
          return (
            <article
              key={category}
              data-testid={`promotion-category-${category}`}
              className="rounded-md border p-4"
              style={{ borderColor: "var(--copilot-border)" }}
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold">{label(category)}</h3>
                  <p data-testid={`promotion-ready-${category}`} className={`mt-1 text-sm ${readyClass(row.ready)}`}>
                    {row.ready ? "Ready to promote" : "Collecting evidence"}
                  </p>
                </div>
                <span
                  data-testid={`promotion-stage-${category}`}
                  className={`rounded-md border px-2 py-1 text-xs font-semibold ${stageClass(stage)}`}
                >
                  {stageLabel(stage, row.currentStageLabel)}
                </span>
              </div>

              <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                <div>
                  <p className="text-xs uppercase tracking-wide trading-muted">Decisions</p>
                  <p className="font-semibold">{evidence.decisionsInStage ?? 0}/{evidence.minDecisions ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide trading-muted">Accuracy</p>
                  <p className="font-semibold">{pct(evidence.accuracyInStage)} / {pct(evidence.minAccuracy)}</p>
                </div>
                <div data-testid={`promotion-sizing-${category}`}>
                  <p className="text-xs uppercase tracking-wide trading-muted">Sizing cap</p>
                  <p className="font-semibold">{row.maxSizingPct ?? evidence.maxSizingPct ?? 0}% max</p>
                </div>
              </div>

              <p className="mt-3 text-sm font-semibold">{row.recommendation || "Keep collecting verified decisions."}</p>

              <div data-testid={`promotion-blockers-${category}`} className="mt-3 text-sm trading-muted">
                {blockers.length ? blockers.join(" ") : "No blockers."}
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  data-testid={`promotion-promote-btn-${category}`}
                  className="copilot-button px-4 py-2 text-sm"
                  disabled={!row.ready || promoting === category}
                  onClick={() => void onPromote(row)}
                >
                  {promoting === category ? "Promoting..." : "Promote"}
                </button>
                <span className="text-sm trading-muted">
                  {row.nextStageLabel ? `Next: ${row.nextStageLabel}` : "Fully promoted"}
                </span>
              </div>

              <HistoryList category={category} history={history} />
            </article>
          );
        })}
      </div>

      {!loading && categories.length === 0 ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          Promotion categories are unavailable.
        </div>
      ) : null}
    </section>
  );
}
