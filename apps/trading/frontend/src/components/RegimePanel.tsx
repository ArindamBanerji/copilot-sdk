import { useEffect, useMemo, useState } from "react";
import {
  getRegimeCurrent,
  getRegimeHistory,
  getRegimePerformance,
  fetchSituationAbstention,
  fetchSituationConditionedStats,
  fetchSituationRegime,
  fetchSituationRejections,
  type RegimeCurrentResponse,
  type RegimeHistoryEntry,
  type RegimePerformanceCell,
  type RegimePerformanceResponse,
} from "../api";
import type {
  SituationAbstentionResponse,
  SituationConditionedStatsResponse,
  SituationRegimeResponse,
  SituationRejectionsResponse,
} from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

const regimes = ["trending", "ranging", "volatile"] as const;

function ensureArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function regimeLabel(regime: string | null | undefined): string {
  if (regime === "trending") return "Trending market";
  if (regime === "volatile") return "Volatile market";
  return "Ranging market";
}

function regimeClass(regime: string | null | undefined): string {
  if (regime === "trending") return "border-emerald-300/50 bg-emerald-500/15 text-emerald-100";
  if (regime === "volatile") return "border-red-300/50 bg-red-500/15 text-red-100";
  return "border-amber-300/50 bg-amber-500/15 text-amber-100";
}

function regimeDotClass(regime: string | null | undefined): string {
  if (regime === "trending") return "bg-emerald-400";
  if (regime === "volatile") return "bg-red-400";
  return "bg-amber-300";
}

function heatClass(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "border-white/10 bg-white/5 text-slate-300";
  if (value >= 0.65) return "border-emerald-300/50 bg-emerald-500/15 text-emerald-100";
  if (value >= 0.45) return "border-amber-300/50 bg-amber-500/15 text-amber-100";
  return "border-red-300/50 bg-red-500/15 text-red-100";
}

function percent(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "-";
}

function volatilityText(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  if (value < 15) return "Low volatility";
  if (value < 25) return "Moderate volatility";
  if (value < 35) return "High volatility";
  return "Extreme volatility";
}

function trendText(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  if (value > 35) return "Strong trend";
  if (value > 25) return "Developing trend";
  return "Choppy trend";
}

function hurstText(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "-";
}

function categoryLabel(category: string): string {
  return category.replace(/_/g, " ");
}

function cellFor(
  performance: RegimePerformanceResponse | null,
  category: string,
  regime: string,
): RegimePerformanceCell | undefined {
  return performance?.perRegimeAccuracy?.[category]?.[regime];
}

export default function RegimePanel() {
  const [current, setCurrent] = useState<RegimeCurrentResponse | null>(null);
  const [history, setHistory] = useState<RegimeHistoryEntry[]>([]);
  const [performance, setPerformance] = useState<RegimePerformanceResponse | null>(null);
  const [situation, setSituation] = useState<SituationRegimeResponse | null>(null);
  const [conditioned, setConditioned] = useState<SituationConditionedStatsResponse | null>(null);
  const [abstention, setAbstention] = useState<SituationAbstentionResponse | null>(null);
  const [rejections, setRejections] = useState<SituationRejectionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);

  const regime = String(current?.regime || performance?.currentRegime || "ranging").toLowerCase();
  const categories = useMemo(
    () => Object.keys(performance?.perRegimeAccuracy || {}).sort(),
    [performance],
  );
  const historyRows = ensureArray(history).slice(0, 30).reverse();
  const recommendation =
    performance?.recommendation || "Score more verified trades before changing regime sizing.";

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getRegimeCurrent(),
      getRegimeHistory(),
      getRegimePerformance(),
      fetchSituationRegime(),
      fetchSituationConditionedStats(),
      fetchSituationAbstention(),
      fetchSituationRejections(),
    ])
      .then(([nextCurrent, nextHistory, nextPerformance, nextSituation, nextConditioned, nextAbstention, nextRejections]) => {
        if (cancelled) return;
        setCurrent(nextCurrent);
        setHistory(nextHistory);
        setPerformance(nextPerformance);
        setSituation(nextSituation);
        setConditioned(nextConditioned);
        setAbstention(nextAbstention);
        setRejections(nextRejections);
        setLoadError(false);
      })
      .catch((error) => {
        console.debug("regime panel unavailable", error);
        if (!cancelled) setLoadError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section data-testid="regime-panel" className="copilot-card p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">Market context</p>
          <h2 className="mt-1 text-xl font-semibold">Market Regime</h2>
          <p className="mt-2 text-sm trading-muted">
            {loading ? "Loading market regime..." : loadError ? "Regime data partially unavailable." : current?.source || "market data"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span
            data-testid="regime-badge"
            className={`rounded-full border px-3 py-1 text-sm font-semibold ${regimeClass(regime)}`}
          >
            {regimeLabel(regime)}
          </span>
          {current?.nearBoundary ? (
            <span className="rounded-full border border-amber-300/50 bg-amber-500/10 px-3 py-1 text-sm text-amber-100">
              Regime may shift soon
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Confidence</div>
          <div data-testid="regime-confidence" className="mt-1 text-2xl font-semibold">
            {loading ? "-" : percent(current?.confidence)}
          </div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Volatility</div>
          <div className="mt-1 text-lg font-semibold">{loading ? "-" : volatilityText(current?.vix)}</div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Trend</div>
          <div className="mt-1 text-lg font-semibold">{loading ? "-" : trendText(current?.adx)}</div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Hurst persistence</div>
          <div data-testid="regime-hurst" className="mt-1 text-lg font-semibold">{loading ? "-" : hurstText(current?.hurst)}</div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Updated</div>
          <div className="mt-1 truncate text-sm font-semibold">{current?.timestamp || "-"}</div>
        </div>
      </div>

      <div data-testid="situation-conditioned" className="mt-5 rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide trading-muted">TRD-S1 / S2 / S3</p>
            <h3 className="mt-1 text-base font-semibold">Situation-conditioned discipline</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${situation?.conservationStatus === "AMBER" ? "border-amber-300/50 bg-amber-500/15 text-amber-100" : "border-emerald-300/50 bg-emerald-500/15 text-emerald-100"}`}>
              Conservation {situation?.conservationStatus || "-"}
            </span>
            <ProvenanceBadge source={situation?.provenance || "illustrative"} />
          </div>
        </div>
        <p className="mt-2 text-sm trading-muted">{situation?.message || conditioned?.mirrorMessage || "Loading situation context..."}</p>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {(["trending", "choppy", "volatile"] as const).map((item) => {
            const row = conditioned?.regimes?.[item];
            return <div key={item} data-testid={`situation-regime-${item}`} className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs uppercase tracking-wide trading-muted">{item}</div>
              <div className="mt-1 text-lg font-semibold">{typeof row?.accuracy === "number" ? `${Math.round(row.accuracy * 100)}% accuracy` : "Accumulating"}</div>
              <div className="text-xs trading-muted">{row?.decisionCount ?? 0} decisions · {row?.tradeFrequencyMultiplier ?? 1}x frequency</div>
            </div>;
          })}
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className={`rounded-md border p-3 ${abstention?.abstentionRecommended ? "border-amber-300/50 bg-amber-500/10" : "border-white/10"}`} data-testid="situation-abstention">
            <div className="text-xs uppercase tracking-wide trading-muted">TRD-S2 situational abstention</div>
            <p className="mt-1 text-sm">{abstention?.message || "Checking regime sufficiency..."}</p>
          </div>
          <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }} data-testid="situation-rejections">
            <div className="text-xs uppercase tracking-wide trading-muted">TRD-S4 regime-scoped rejection</div>
            <p className="mt-1 text-sm">{rejections?.message || "Checking rejected variants..."}</p>
          </div>
        </div>
      </div>

      <div data-testid="regime-history" className="mt-5 rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-base font-semibold">90-day regime history</h3>
          <span className="text-sm trading-muted">{history.length} records</span>
        </div>
        {historyRows.length ? (
          <div className="mt-4 flex h-12 items-end gap-1" aria-label="Regime history timeline">
            {historyRows.map((entry, index) => (
              <div
                key={`${entry.date || "entry"}-${index}`}
                className={`w-full min-w-1 rounded-sm ${regimeDotClass(entry.regime)}`}
                style={{ height: entry.regime === "volatile" ? "100%" : entry.regime === "trending" ? "70%" : "45%" }}
                title={`${regimeLabel(entry.regime)} ${entry.date || ""}`}
              />
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm trading-muted">History starts after the classifier records market conditions.</p>
        )}
      </div>

      <div data-testid="regime-performance" className="mt-5 rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold">Performance by regime</h3>
            <p className="mt-1 text-sm trading-muted">Verified outcomes grouped by category and market regime.</p>
          </div>
          <span className="rounded-full border px-2 py-0.5 text-xs trading-muted" style={{ borderColor: "var(--copilot-border)" }}>
            Current: {regimeLabel(regime)}
          </span>
        </div>

        {categories.length ? (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr>
                  <th className="p-2 text-left trading-muted">Category</th>
                  {regimes.map((item) => (
                    <th key={item} className="p-2 text-center trading-muted">
                      {regimeLabel(item)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {categories.map((category) => (
                  <tr key={category}>
                    <th className="p-2 text-left font-semibold">{categoryLabel(category)}</th>
                    {regimes.map((item) => {
                      const cell = cellFor(performance, category, item);
                      return (
                        <td key={`${category}-${item}`} className="p-1 text-center">
                          <div className={`rounded-md border px-3 py-2 ${heatClass(cell?.accuracy)}`}>
                            <div className="font-semibold">{percent(cell?.accuracy)}</div>
                            <div className="text-xs opacity-80">{cell?.nDecisions ?? 0} trades</div>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-3 text-sm trading-muted">Score more verified trades to build regime performance.</p>
        )}
      </div>

      <div data-testid="regime-recommendation" className="mt-5 rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="text-xs uppercase tracking-wide trading-muted">Regime observation</div>
        <p className="mt-2 text-sm font-semibold">{loading ? "Loading observation..." : recommendation}</p>
      </div>
    </section>
  );
}
