import ProvenanceBadge from "./ProvenanceBadge";
import type { ScoreInvoiceResponse, ThresholdDecision } from "../types";

function pct(value?: number | null): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "n/a";
  return `${value.toFixed(1)}%`;
}

function normalizeDecision(score: ScoreInvoiceResponse): ThresholdDecision | null {
  return score.threshold_decision ?? score.thresholdDecision ?? null;
}

function situationDecision(score: ScoreInvoiceResponse): string {
  return score.action ?? score.recommended_action ?? score.recommendedAction ?? "review";
}

export default function RuleVsReasoningPanel({ score }: { score: ScoreInvoiceResponse }) {
  const rule = normalizeDecision(score);
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
        <ProvenanceBadge source="context" />
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
            <p className="mt-3 text-sm font-semibold text-slate-900">Est. cost: {rule.cost_of_error ?? rule.costOfError}</p>
          ) : null}
        </section>

        <section className="bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-950">Situation-Aware</h3>
          <p className="mt-3 text-sm leading-6 text-slate-700">
            Price variance {pct(variance)}. Commodity context and contract allowance are evaluated before action.
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            Contract pass-through can allow the move when market input supports it.
          </p>
          <div className={`mt-4 text-2xl font-bold ${accepts ? "text-emerald-700" : "text-amber-700"}`}>
            {accepts ? "ACCEPT" : situationAction.toUpperCase()}
          </div>
          <p className="mt-2 text-sm text-slate-600">Confidence: {pct(score.confidence * 100)}</p>
          <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
            verified
            <ProvenanceBadge source="context" />
          </div>
        </section>
      </div>
    </article>
  );
}
