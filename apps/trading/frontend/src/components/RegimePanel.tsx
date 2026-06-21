import { useEffect, useMemo, useState } from "react";
import { fetchRegime, fetchRegimeDetail } from "../api";
import type { RegimeDetailRecommendation, RegimeDetailResponse, RegimeRecommendation, RegimeResponse } from "../types";

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

function shiftText(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "0%";
  return `${value > 0 ? "+" : ""}${value}%`;
}

function actionClass(action: string | undefined): string {
  if (action === "avoid") return "border-red-300/50 bg-red-500/10 text-red-100";
  if (action === "reduce") return "border-amber-300/50 bg-amber-500/10 text-amber-100";
  if (action === "increase_small") return "border-emerald-300/50 bg-emerald-500/10 text-emerald-100";
  if (action === "increase") return "border-emerald-300/50 bg-emerald-500/10 text-emerald-100";
  return "border-white/20 bg-white/5 text-slate-100";
}

function recommendationDelta(recommendation?: RegimeRecommendation): number | null | undefined {
  return recommendation?.vsBaseline ?? recommendation?.delta;
}

function pp(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value >= 0 ? "+" : ""}${value.toFixed(1)}pp` : "-";
}

function multiplier(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(2)}x` : "-";
}

function RecommendationCard({ recommendation }: { recommendation: RegimeDetailRecommendation }) {
  return (
    <article className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold">{recommendation.category?.replace(/_/g, " ") || "Uncategorized"}</h3>
          <p className="mt-1 text-xs trading-muted">Regime context: {pct(recommendation.currentAccuracy)} vs {pct(recommendation.baselineAccuracy)} baseline</p>
        </div>
        <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${actionClass(recommendation.action)}`}>
          {actionLabel(recommendation.action)}
        </span>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
        <span className="font-semibold">Shift suggestion {shiftText(recommendation.shiftPct)}</span>
        <span className="rounded-full border px-2 py-0.5 text-xs trading-muted" style={{ borderColor: "var(--copilot-border)" }}>
          {recommendation.regimeNeutral ? "Regime-neutral" : "Regime-sensitive"}
        </span>
        <span className={Number(recommendation.deltaPp || 0) >= 0 ? "trading-positive" : "trading-negative"}>
          {typeof recommendation.deltaPp === "number" ? `${recommendation.deltaPp >= 0 ? "+" : ""}${recommendation.deltaPp.toFixed(1)}pp` : "0.0pp"}
        </span>
      </div>
      {recommendation.rationale ? <p className="mt-2 text-sm trading-muted">{recommendation.rationale}</p> : null}
    </article>
  );
}

export default function RegimePanel() {
  const [payload, setPayload] = useState<RegimeResponse | null>(null);
  const [detail, setDetail] = useState<RegimeDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(true);
  const [detailUnavailable, setDetailUnavailable] = useState(false);
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

  useEffect(() => {
    let cancelled = false;
    async function loadDetail() {
      setDetailLoading(true);
      const response = await fetchRegimeDetail();
      if (!cancelled) {
        setDetail(response);
        setDetailUnavailable(response === null);
        setDetailLoading(false);
      }
    }
    void loadDetail();
    return () => {
      cancelled = true;
    };
  }, []);

  const current = payload?.current;
  const regime = String(current?.regime || "ranging").toLowerCase();
  const recommendation = useMemo(() => payload?.recommendations?.[0], [payload]);
  const delta = recommendationDelta(recommendation);
  const detailRecommendations = detail?.recommendations || [];
  const transitions = detail?.regimeTransitions || [];
  const edgeSummary = detail?.regimeEdgeSummary;
  const sizing = detail?.sizingRecommendation;
  const transitionAlert = detail?.transitionAlert;
  const factorWeights = detail?.regimeFactorWeights;
  const factorInfluence = detail?.regimeFactorInfluence;
  const dataQuality = detail?.dataQuality;

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

      <div className="mt-4 rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-semibold">Detailed Recommendations</h3>
            <p className="mt-1 text-sm trading-muted">Allocation context by category and regime transition.</p>
          </div>
          {!detailLoading ? (
            <span
              className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${
                detail?.conservationSafe ? "border-emerald-300/50 bg-emerald-500/10 text-emerald-100" : "border-amber-300/50 bg-amber-500/10 text-amber-100"
              }`}
            >
              {detail?.conservationSafe ? "Conservation confirmed" : "Conservation not confirmed"}
            </span>
          ) : null}
        </div>

        {detailLoading ? <div className="mt-3 text-sm trading-muted">Loading detailed recommendations...</div> : null}

        {!detailLoading && detailUnavailable ? (
          <div className="mt-3 rounded-md border border-dashed border-white/15 p-3 text-sm trading-muted">
            Detailed regime recommendations unavailable.
          </div>
        ) : null}

        {!detailLoading && detail ? (
          <div className="mt-3 grid gap-3">
            {detail.summary ? <p className="text-sm trading-muted">{detail.summary}</p> : null}
            <div className="grid gap-3 lg:grid-cols-2">
              <article className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs uppercase tracking-wide trading-muted">Observed edge comparison</div>
                <h3 className="mt-1 text-sm font-semibold">
                  {edgeSummary?.category?.replace(/_/g, " ") || "Regime edge"}
                </h3>
                <p className="mt-2 text-sm trading-muted">
                  {edgeSummary?.message || "Score more trades to build sample-backed regime edge comparisons."}
                </p>
                <div className="mt-3 flex flex-wrap gap-2 text-xs trading-muted">
                  <span className="rounded-full border px-2 py-0.5" style={{ borderColor: "var(--copilot-border)" }}>
                    {edgeSummary?.status || "unavailable"}
                  </span>
                  <span>source {edgeSummary?.source || dataQuality?.source || "unknown"}</span>
                  <span>current n={edgeSummary?.sampleSizeCurrent ?? 0}</span>
                  <span>comparison n={edgeSummary?.sampleSizeComparison ?? 0}</span>
                  <span>{pp(edgeSummary?.edgeDeltaPp)}</span>
                </div>
                <p className="mt-2 text-xs trading-muted">Historical observed context only; not a guarantee of future profit.</p>
              </article>

              <article className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs uppercase tracking-wide trading-muted">Sizing advisory</div>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${actionClass(sizing?.action)}`}>
                    {actionLabel(sizing?.action || "normal")}
                  </span>
                  <span className="text-sm font-semibold">suggested {multiplier(sizing?.suggestedSizeMultiplier)}</span>
                  <span className="text-sm trading-muted">max {multiplier(sizing?.maxSizeMultiplier)}</span>
                </div>
                <p className="mt-2 text-sm trading-muted">{sizing?.reason || "Insufficient data; use conservative sizing."}</p>
                <div className="mt-2 text-xs trading-muted">
                  sample n={sizing?.sampleSize ?? 0} · {sizing?.confidenceStatus || "insufficient_data"} · advisory only
                </div>
              </article>
            </div>

            {transitionAlert?.active ? (
              <div className="rounded-md border border-amber-300/40 bg-amber-500/10 p-3 text-sm">
                <div className="font-semibold">{transitionAlert.message || "Regime changed; observed edge shifted."}</div>
                <div className="mt-1 trading-muted">
                  {transitionAlert.previousRegime} -&gt; {transitionAlert.currentRegime} · {pp(transitionAlert.edgeDeltaPp)} · {transitionAlert.oldRecommendation || "-"} to{" "}
                  {transitionAlert.newRecommendation || "-"}
                </div>
              </div>
            ) : null}

            <article className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h3 className="text-base font-semibold">Regime factor / DK context</h3>
                  <p className="mt-1 text-sm trading-muted">
                    {factorWeights?.status === "available"
                      ? "Per-regime factor weights are available."
                      : "Per-regime DK weights are unavailable; they are not fabricated."}
                  </p>
                </div>
                <span className="rounded-full border px-2 py-0.5 text-xs trading-muted" style={{ borderColor: "var(--copilot-border)" }}>
                  {factorWeights?.status || "unavailable"}
                </span>
              </div>
              {factorInfluence?.factors?.length ? (
                <div className="mt-3 grid gap-2 md:grid-cols-2">
                  {factorInfluence.factors.slice(0, 4).map((factor) => (
                    <div key={factor.factor} className="rounded-md bg-white/5 px-3 py-2 text-sm">
                      <span className="font-semibold">{factor.factor?.replace(/_/g, " ")}</span>
                      <span className={Number(factor.influencePp || 0) >= 0 ? "ml-2 trading-positive" : "ml-2 trading-negative"}>{pp(factor.influencePp)}</span>
                      <span className="ml-2 text-xs trading-muted">n={factor.sampleSize ?? 0}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm trading-muted">{factorWeights?.reason || factorInfluence?.warning || "Regime factor influence is still learning."}</p>
              )}
            </article>

            {detailRecommendations.length ? (
              <div className="grid gap-3 lg:grid-cols-2">
                {detailRecommendations.slice(0, 4).map((item) => (
                  <RecommendationCard key={`${item.category || "category"}-${item.action || "hold"}`} recommendation={item} />
                ))}
              </div>
            ) : (
              <div className="rounded-md border border-dashed border-white/15 p-3 text-sm trading-muted">
                No detailed regime recommendations available.
              </div>
            )}
            {transitions.length ? (
              <div>
                <div className="text-xs uppercase tracking-wide trading-muted">Regime transitions</div>
                <div className="mt-2 grid gap-2 md:grid-cols-3">
                  {transitions.map((transition) => (
                    <div key={`${transition.fromRegime}-${transition.toRegime}`} className="rounded-md border p-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
                      <div className="font-semibold">
                        {transition.fromRegime?.replace(/_/g, " ") || "-"} -&gt; {transition.toRegime?.replace(/_/g, " ") || "-"}
                      </div>
                      <div className={Number(transition.avgAccuracyDeltaPp || 0) >= 0 ? "trading-positive" : "trading-negative"}>
                        {typeof transition.avgAccuracyDeltaPp === "number" ? `${transition.avgAccuracyDeltaPp >= 0 ? "+" : ""}${transition.avgAccuracyDeltaPp.toFixed(1)}pp` : "0.0pp"}
                      </div>
                      <div className="text-xs trading-muted">{transition.count ?? transition.categoriesAffected?.length ?? 0} categories</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
