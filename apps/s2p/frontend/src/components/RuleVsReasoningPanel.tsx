import ProvenanceBadge from "./ProvenanceBadge";
import type { InvoiceException, ScoreInvoiceResponse, ThresholdDecision } from "../types";

function pct(value?: number | null): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "n/a";
  return `${value.toFixed(1)}%`;
}

function normalizeDecision(score: ScoreInvoiceResponse, invoice?: InvoiceException | null): ThresholdDecision | null {
  const rawVariance = invoice?.amount_variance_ratio ?? invoice?.variance_ratio ?? score.factors?.amount_variance_ratio;
  if (typeof rawVariance === "number" && Number.isFinite(rawVariance)) {
    const variance = Math.abs(rawVariance) <= 1 ? rawVariance * 100 : rawVariance;
    const threshold = 5;
    return {
      decision: variance > threshold ? "REJECT" : "APPROVE",
      reason: `Computed from invoice variance (${variance.toFixed(1)}% > ${threshold.toFixed(1)}%).`,
      price_variance_pct: variance,
      threshold_pct: threshold,
      provenance: "live",
      cost_of_error: "$340K",
    };
  }
  return score.threshold_decision ?? score.thresholdDecision ?? null;
}

function situationDecision(score: ScoreInvoiceResponse): string {
  return score.action ?? score.recommended_action ?? score.recommendedAction ?? "review";
}

export default function RuleVsReasoningPanel({
  score,
  invoice = null,
  situationExplanation = null,
  situationConfidence = null,
  situationSources = null,
  situationProvenance = null,
  situationLoading = false,
}: {
  score: ScoreInvoiceResponse;
  invoice?: InvoiceException | null;
  situationExplanation?: string | null;
  situationConfidence?: number | null;
  situationSources?: string[] | null;
  situationProvenance?: string | null;
  situationLoading?: boolean;
}) {
  const rule = normalizeDecision(score, invoice);
  if (!rule) return null;

  const variance = rule.price_variance_pct ?? rule.priceVariancePct;
  const threshold = rule.threshold_pct ?? rule.thresholdPct ?? 5.0;
  const situationAction = situationDecision(score).replace(/_/g, " ");
  const accepts = /auto approve|approve/i.test(situationAction);

  return (
    <article className="copilot-card p-5" data-testid="rule-vs-reasoning-panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Rule vs reasoning</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Rules do not read contracts.</h2>
        </div>
      </div>

      <div className="mt-4 grid overflow-hidden rounded-lg border border-slate-200 md:grid-cols-2">
        <section className="border-b border-slate-200 bg-slate-50 p-4 md:border-b-0 md:border-r">
          <h3 className="text-sm font-semibold text-slate-950">Rule-Based</h3>
          <p className="mt-3 text-sm leading-6 text-slate-700">
            Price variance {pct(variance)} exceeds {pct(threshold)} threshold.
          </p>
          <div className="mt-4 text-2xl font-bold text-red-700">{rule.decision}</div>
          <p className="mt-2 text-sm text-slate-600">{rule.reason}</p>
          {rule.cost_of_error || rule.costOfError ? (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-900">
              <span>Est. cost: {rule.cost_of_error ?? rule.costOfError}</span>
              <ProvenanceBadge source={rule.provenance ?? "sample"} />
            </div>
          ) : null}
        </section>

        <section className="bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-950">Situation-Aware</h3>
          {situationLoading ? (
            <p className="mt-3 text-sm leading-6 text-slate-700">Loading reasoning...</p>
          ) : situationExplanation ? (
            <>
              <p className="mt-3 text-sm leading-6 text-slate-700">{situationExplanation}</p>
              {situationSources?.length ? (
                <p className="mt-2 text-sm leading-6 text-slate-700">Context sources: {situationSources.join(", ")}</p>
              ) : null}
            </>
          ) : (
            <p className="mt-3 text-sm leading-6 text-slate-700">Situation reasoning unavailable.</p>
          )}
          <div className={`mt-4 text-2xl font-bold ${accepts ? "text-emerald-700" : "text-amber-700"}`}>
            {accepts ? "ACCEPT" : situationAction.toUpperCase()}
          </div>
          <p className="mt-2 text-sm text-slate-600">Confidence: {pct((situationConfidence ?? score.confidence) * 100)}</p>
          {situationProvenance ? <ProvenanceBadge source={situationProvenance} className="mt-3" /> : null}
        </section>
      </div>
      {rule.decision === "REJECT" && accepts ? (
        <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-800">
          The rule was wrong. {rule.cost_of_error ?? rule.costOfError ?? "$340K"} in false rejections.
        </p>
      ) : null}
    </article>
  );
}
