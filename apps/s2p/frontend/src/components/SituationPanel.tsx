import { useEffect, useMemo, useState } from "react";
import { fetchSituation } from "../api";
import type { ContextChainNode, SituationResponse } from "../types";
import { ProvenanceBadge } from "./ProvenanceBadge";

function ensureArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value as T[] : [];
}

// SituationPanel provenance declaration:
// - surfaced values: nl_explanation, confidence, context chain nodes
// - provenance per value: API-driven (single-source rule A2)
// - renders ProvenanceBadge on every surfaced value
// - no value hardcodes a tier -- all from API response

function label(value: string): string {
  return value.replace(/_/g, " ");
}

function confidenceText(value?: number): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "n/a";
  return `${Math.round(value * 100)}%`;
}

function confidenceClass(value?: number): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "text-slate-700";
  if (value >= 0.85) return "text-emerald-700";
  if (value >= 0.65) return "text-amber-700";
  return "text-red-700";
}

function nodeText(node: ContextChainNode): string {
  return label(node.node || node.id || "node");
}

function factorList(data: SituationResponse): string {
  const factors = ensureArray<string>(data.factors_used);
  return factors.length > 0 ? factors.map(label).join(", ") : "none";
}

export function SituationPanel({
  decisionId,
  hasSelection = false,
  onSituationChange,
}: {
  decisionId: string | null;
  hasSelection?: boolean;
  onSituationChange?: (data: SituationResponse | null, loading: boolean) => void;
}) {
  const [data, setData] = useState<SituationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!decisionId) {
      setData(null);
      setError(false);
      setLoading(false);
      onSituationChange?.(null, false);
      return;
    }
    let cancelled = false;
    const controller = new AbortController();
    setLoading(true);
    setError(false);
    onSituationChange?.(null, true);
    fetchSituation(decisionId, 3, controller.signal)
      .then((response) => {
        if (cancelled) return;
        setData(response);
        setError(!response);
        onSituationChange?.(response, false);
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setError(true);
          onSituationChange?.(null, false);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [decisionId, onSituationChange]);

  const chain = useMemo(() => data?.context_chain ?? [], [data]);

  return (
    <article className="copilot-card p-5" data-testid="situation-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Situation context</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Situation Analysis</h2>
        </div>
        {data && !data.status ? <ProvenanceBadge source={data.provenance.overall} /> : null}
      </div>

      {!decisionId ? (
        <p className="mt-4 text-sm text-slate-500">
          {hasSelection ? "Score the exception to see situation analysis." : "Select an exception to begin."}
        </p>
      ) : loading ? (
        <p className="mt-4 text-sm text-slate-500">Analyzing situation...</p>
      ) : data?.status === "unavailable" || data?.status === "timeout" ? (
        <div className="mt-4 space-y-3">
          <blockquote className="rounded-md border-l-4 border-amber-500 bg-amber-50 p-4 text-sm leading-6 text-slate-800">
            <p>{data.nl_explanation}</p>
          </blockquote>
          <p className="text-sm text-slate-500">
            Situation analysis {data.status === "timeout" ? "timed out" : "unavailable"}.
            Factor-based scoring was used.
          </p>
        </div>
      ) : error || !data ? (
        <p className="mt-4 text-sm text-slate-500">Situation analysis unavailable.</p>
      ) : (
        <div className="mt-4 space-y-4">
          <blockquote className="rounded-md border-l-4 border-amber-500 bg-amber-50 p-4 text-sm leading-6 text-slate-800">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <p className="max-w-3xl">{data.nl_explanation}</p>
              <ProvenanceBadge source={data.provenance.nl_explanation} />
            </div>
          </blockquote>

          {!data.context_available ? (
            <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              Some context unavailable.
            </p>
          ) : null}

          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Confidence</span>
                <ProvenanceBadge source={data.provenance.confidence} />
              </div>
              <div className={`mt-2 text-2xl font-semibold ${confidenceClass(data.confidence)}`}>
                {confidenceText(data.confidence)}
              </div>
            </div>
            <div className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Category</span>
                <ProvenanceBadge source={data.provenance.overall} />
              </div>
              <div className="mt-2 text-sm font-semibold capitalize text-slate-900">{label(data.category)}</div>
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-slate-900">Context</h3>
              <ProvenanceBadge source={data.provenance.overall} />
            </div>
            {chain.length > 0 ? (
              <div className="flex flex-wrap items-center gap-2">
                {chain.map((node, index) => (
                  <div key={`${node.node}-${node.id}-${index}`} className="flex items-center gap-2">
                    {index > 0 ? <span className="text-slate-400">-&gt;</span> : null}
                    <span className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800">
                      {nodeText(node)}
                    </span>
                    <ProvenanceBadge source={node.provenance} />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">No context chain returned.</p>
            )}
          </div>

          <div className="grid gap-3 text-sm md:grid-cols-2">
            <div className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium text-slate-700">Traversal</span>
                <ProvenanceBadge source={data.provenance.overall} />
              </div>
              <p className="mt-1 text-slate-600">{data.traversal_depth} hops</p>
            </div>
            <div className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium text-slate-700">Factors</span>
                <ProvenanceBadge source={data.provenance.overall} />
              </div>
              <p className="mt-1 text-slate-600">{factorList(data)}</p>
            </div>
          </div>

          {data.warnings.length > 0 || data.missing_variables.length > 0 ? (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
              <span className="mr-2 font-semibold uppercase tracking-wide text-slate-500">System</span>
              {[...data.warnings, ...data.missing_variables.map((item) => `Missing: ${item}`)].join(" | ")}
            </div>
          ) : null}
        </div>
      )}
    </article>
  );
}
