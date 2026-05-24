import { useEffect, useMemo, useState } from "react";
import { fetchRegime } from "../api";
import type { RegimeRecommendation, RegimeResponse } from "../types";

function numberText(value: number | null | undefined, digits = 1): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "-";
}

function pct(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(0)}%` : "-";
}

function regimeClass(regime: string): string {
  if (regime === "trending") return "bg-emerald-100 text-emerald-800";
  if (regime === "volatile") return "bg-red-100 text-red-800";
  return "bg-amber-100 text-amber-800";
}

function regimeLabel(regime: string): string {
  return regime.replace(/_/g, " ").toUpperCase();
}

function actionLabel(action: string | undefined): string {
  if (!action) return "Hold";
  return action.replace(/_/g, " ");
}

function recommendationDelta(recommendation?: RegimeRecommendation): number | null | undefined {
  return recommendation?.vsBaseline ?? recommendation?.delta;
}

export default function RegimePanel() {
  const [payload, setPayload] = useState<RegimeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const response = await fetchRegime();
      if (!cancelled) {
        setPayload(response);
        setUnavailable(response === null);
        setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const current = payload?.current;
  const regime = String(current?.regime || "ranging").toLowerCase();
  const recommendation = useMemo(() => payload?.recommendations?.[0], [payload]);
  const delta = recommendationDelta(recommendation);

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Market Regime</h2>
          <p className="text-sm trading-muted">
            {loading ? "Loading regime context..." : unavailable ? "Default regime context" : current?.source || "default"}
          </p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${regimeClass(regime)}`}>{regimeLabel(regime)}</span>
      </div>

      <div className="trading-grid trading-grid-3">
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs trading-muted">VIX</div>
          <div className="trading-stat-value">{loading ? "-" : numberText(current?.vix)}</div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs trading-muted">ADX</div>
          <div className="trading-stat-value">{loading ? "-" : numberText(current?.adx)}</div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs trading-muted">Source</div>
          <div className="text-sm font-semibold">{loading ? "-" : current?.source || "default"}</div>
        </div>
      </div>

      <div className="mt-4 rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="text-xs trading-muted">Regime accuracy</div>
        {loading ? (
          <div className="mt-1 text-sm trading-muted">Loading recommendation...</div>
        ) : recommendation ? (
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm">
            <span className="font-semibold">{recommendation.category?.replace(/_/g, " ")}</span>
            <span className="rounded-full border px-2 py-0.5 text-xs" style={{ borderColor: "var(--copilot-border)" }}>
              {actionLabel(recommendation.action)}
            </span>
            <span>{pct(recommendation.accuracy)} accuracy</span>
            <span className={Number(delta || 0) >= 0 ? "trading-positive" : "trading-negative"}>
              {typeof delta === "number" ? `${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(0)}pp vs baseline` : "baseline pending"}
            </span>
          </div>
        ) : (
          <div className="mt-1 text-sm trading-muted">Score more trades to build regime accuracy.</div>
        )}
      </div>
    </section>
  );
}
