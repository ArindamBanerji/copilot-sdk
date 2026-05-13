import { useEffect, useMemo, useState } from "react";
import { fetchPreviewQueue, learnDecision, scoreInvoice } from "../api";
import { ProcessContextPanel } from "../components/ProcessContextPanel";
import { S2PConservationProjection } from "../components/S2PConservationProjection";
import { S2PReasoningPanel } from "../components/S2PReasoningPanel";
import {
  S2P_ACTIONS,
  S2P_FACTORS,
  type FactorMap,
  type InvoiceException,
  type LearnDecisionResponse,
  type PreviewQueueResponse,
  type ProcessContext,
  type S2PAction,
  type ScoreInvoiceResponse
} from "../types";

function invoiceId(invoice?: InvoiceException | null): string {
  return invoice?.invoice_id ?? invoice?.invoiceId ?? invoice?.event_id ?? invoice?.eventId ?? "";
}

function supplierName(invoice?: InvoiceException | null): string {
  return invoice?.supplier_name ?? invoice?.supplierName ?? invoice?.supplier ?? "Unknown supplier";
}

function supplierId(invoice?: InvoiceException | null): string {
  return invoice?.supplier_id ?? invoice?.supplierId ?? supplierName(invoice);
}

function money(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function percent(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

function actionLabel(action?: string): string {
  if (!action) return "n/a";
  return action.replace(/_/g, " ");
}

function recommendedAction(score?: ScoreInvoiceResponse | null, invoice?: InvoiceException | null): string {
  return (
    score?.recommended_action ??
    score?.recommendedAction ??
    score?.action ??
    score?.scored_action ??
    score?.scoredAction ??
    invoice?.recommended_action ??
    invoice?.recommendedAction ??
    invoice?.scored_action ??
    invoice?.scoredAction ??
    "hold_for_review"
  );
}

function factorMap(score?: ScoreInvoiceResponse | null, invoice?: InvoiceException | null): FactorMap {
  if (score?.factors) return score.factors;
  const vector = score?.factor_vector ?? score?.factorVector ?? invoice?.factor_vector ?? invoice?.factorVector;
  const fromVector = vector?.reduce<FactorMap>((acc, value, index) => {
    const name = S2P_FACTORS[index];
    if (name) acc[name] = value;
    return acc;
  }, {});
  if (fromVector && Object.keys(fromVector).length > 0) return fromVector;
  return invoice?.factors ?? {};
}

function processContext(score?: ScoreInvoiceResponse | null, invoice?: InvoiceException | null): ProcessContext | null {
  return score?.process_context ?? score?.processContext ?? invoice?.process_context ?? invoice?.processContext ?? null;
}

export function TriageScreen() {
  const [queue, setQueue] = useState<PreviewQueueResponse | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [score, setScore] = useState<ScoreInvoiceResponse | null>(null);
  const [learnResult, setLearnResult] = useState<LearnDecisionResponse | null>(null);
  const [overrideAction, setOverrideAction] = useState<S2PAction>("hold_for_review");
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [learning, setLearning] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchPreviewQueue()
      .then((data) => {
        if (cancelled) return;
        setQueue(data);
        const first = data.exceptions?.[0];
        if (first) setSelectedId(invoiceId(first));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const invoices = queue?.exceptions ?? [];
  const selected = useMemo(
    () => invoices.find((invoice) => invoiceId(invoice) === selectedId) ?? invoices[0] ?? null,
    [invoices, selectedId],
  );
  const action = recommendedAction(score, selected);
  const factors = factorMap(score, selected);
  const context = processContext(score, selected);
  const decisionId = score?.decision_id ?? score?.decisionId ?? "";

  async function handleScore() {
    if (!selected) return;
    setScoring(true);
    setLearnResult(null);
    const result = await scoreInvoice({
      event_id: invoiceId(selected),
      category: String(selected.category ?? "price_variance"),
      amount: Number(selected.amount ?? 0),
      supplier_id: supplierId(selected),
    });
    setScore(result);
    const nextAction = recommendedAction(result, selected);
    setOverrideAction(S2P_ACTIONS.includes(nextAction as S2PAction) ? (nextAction as S2PAction) : "hold_for_review");
    setScoring(false);
  }

  async function handleLearn(actualAction: string, outcome: "confirm" | "override") {
    if (!score || !selected || !decisionId) return;
    setLearning(true);
    const result = await learnDecision({
      decision_id: decisionId,
      actual_action: actualAction,
      outcome: outcome === "confirm" ? "confirmed" : "override",
      context: {
        amount: Number(selected.amount ?? 0),
        at_risk: outcome === "override" ? Number(selected.amount ?? 0) : 0,
        recovery_pct: outcome === "confirm" ? 100 : 0,
      },
    });
    setLearnResult(result);
    setLearning(false);
  }

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Invoice exception workflow</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">Exception Triage</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Select an invoice, score the exception, inspect factors and process context, then confirm
          or override the recommendation so S2P can record reward.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(260px,360px)_1fr]">
        <article className="copilot-card p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-slate-950">Invoice Selector</h2>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
              {queue?.total ?? 0} queued
            </span>
          </div>
          {loading ? (
            <p className="mt-4 text-sm text-slate-500">Loading invoice queue...</p>
          ) : invoices.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">No invoice exceptions available.</p>
          ) : (
            <div className="mt-4 space-y-2">
              {invoices.slice(0, 10).map((invoice) => {
                const id = invoiceId(invoice);
                const selectedRow = id === invoiceId(selected);
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      setSelectedId(id);
                      setScore(null);
                      setLearnResult(null);
                    }}
                    className={`w-full rounded-md border p-3 text-left transition ${
                      selectedRow ? "border-amber-500 bg-amber-50" : "border-slate-200 bg-white hover:border-amber-300"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-mono text-xs font-semibold text-slate-700">{id}</span>
                      <span className="text-xs font-semibold text-amber-700">{percent(invoice.confidence)}</span>
                    </div>
                    <p className="mt-1 text-sm font-medium text-slate-950">{supplierName(invoice)}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {String(invoice.category ?? "uncategorized")} · {money(invoice.amount)}
                    </p>
                  </button>
                );
              })}
            </div>
          )}
        </article>

        <div className="space-y-4">
          <article className="copilot-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-950">Selected Invoice</h2>
                {selected ? (
                  <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <Metric label="Invoice" value={invoiceId(selected)} />
                    <Metric label="Supplier" value={supplierName(selected)} />
                    <Metric label="Amount" value={money(selected.amount)} />
                    <Metric label="Category" value={String(selected.category ?? "n/a")} />
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">Choose an invoice to begin triage.</p>
                )}
              </div>
              <button
                type="button"
                onClick={handleScore}
                disabled={!selected || scoring}
                className="rounded-md bg-amber-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {scoring ? "Scoring..." : "Score"}
              </button>
            </div>
          </article>

          {score ? (
            <>
              <article className="copilot-card p-5">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Recommendation</p>
                    <h2 className="mt-1 text-2xl font-semibold text-slate-950">{actionLabel(action)}</h2>
                    <p className="mt-1 text-sm text-slate-500">Decision {decisionId}</p>
                  </div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-right">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Confidence</p>
                    <p className="mt-1 text-2xl font-semibold text-slate-950">{percent(score.confidence)}</p>
                  </div>
                </div>

                <div className="mt-5 flex flex-wrap items-end gap-3">
                  <button
                    type="button"
                    onClick={() => handleLearn(action, "confirm")}
                    disabled={learning}
                    className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    Confirm recommendation
                  </button>
                  <label className="text-sm font-medium text-slate-700">
                    Override action
                    <select
                      value={overrideAction}
                      onChange={(event) => setOverrideAction(event.target.value as S2PAction)}
                      className="mt-1 block rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                    >
                      {S2P_ACTIONS.map((item) => (
                        <option key={item} value={item}>
                          {actionLabel(item)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    onClick={() => handleLearn(overrideAction, "override")}
                    disabled={learning}
                    className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    Override and learn
                  </button>
                </div>
              </article>

              <div className="grid gap-4 xl:grid-cols-2">
                <S2PReasoningPanel factors={factors} title="7-Factor Reasoning" />
                <ProcessContextPanel processContext={context} />
              </div>
            </>
          ) : null}

          {learnResult ? (
            <article className="copilot-card border-emerald-200 bg-emerald-50 p-5">
              <h2 className="text-lg font-semibold text-emerald-950">Learning Result</h2>
              <div className="mt-4 grid gap-3 sm:grid-cols-4">
                <Metric label="Outcome" value={learnResult.outcome ?? "recorded"} />
                <Metric label="Reward" value={formatReward(learnResult.reward)} />
                <Metric label="Reward raw" value={formatReward(learnResult.reward_raw ?? learnResult.rewardRaw)} />
                <Metric
                  label="Learned"
                  value={String(learnResult.learning_applied ?? learnResult.learningApplied ?? learnResult.learned ?? false)}
                />
              </div>
            </article>
          ) : null}

          <S2PConservationProjection />
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 break-words text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function formatReward(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2);
}
