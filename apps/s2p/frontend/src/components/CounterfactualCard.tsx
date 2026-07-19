import { useEffect, useState } from "react";
import { API_URL } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

// NOTE: This component is duplicated in copilot-sdk/apps/trading/frontend/src/components/CounterfactualCard.tsx.
// If you modify this file, update the counterpart.
// Duplication exists because SDK apps and S2P have separate frontend build pipelines.
// A shared component library would eliminate this but is out of scope for this batch.

const BASE_FACTORS = {
  match_status: 0.7,
  amount_variance_ratio: 0.8,
  duplicate_score: 0.4,
  supplier_exception_history: 0.5,
  payment_terms_impact: 0.6,
  commodity_index_correlation: 0.5,
  tax_regulatory_compliance: 0.8,
  environmental_risk: 0.3
};

const PERTURBED_FACTORS = {
  ...BASE_FACTORS,
  amount_variance_ratio: 0.2
};

interface CounterfactualResponse {
  base_score?: number;
  perturbed_score?: number;
  delta?: number;
  perturbed_factor?: string;
  provenance?: string;
  error?: string;
  rejected?: boolean;
}

async function postCounterfactual(payload: unknown): Promise<CounterfactualResponse> {
  const response = await fetch(`${API_URL}/api/s2p/score/counterfactual`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = (await response.json()) as CounterfactualResponse;
  if (!response.ok && !body.rejected) {
    throw new Error(body.error || `Counterfactual failed with ${response.status}`);
  }
  return body;
}

function value(n?: number): string {
  return typeof n === "number" ? n.toFixed(2) : "n/a";
}

function delta(n?: number): string {
  if (typeof n !== "number") return "n/a";
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}`;
}

export default function CounterfactualCard() {
  const [result, setResult] = useState<CounterfactualResponse | null>(null);
  const [sampleRefusal, setSampleRefusal] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!expanded) return;
    let cancelled = false;
    setLoading(true);
    setError(false);
    postCounterfactual({
      base_factors: BASE_FACTORS,
      perturbed_factors: PERTURBED_FACTORS,
      category: "price_variance"
    })
      .then((payload) => {
        if (!cancelled) setResult(payload);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [expanded]);

  async function trySample() {
    const payload = await postCounterfactual({
      base_factors: {
        ...BASE_FACTORS,
        amount_variance_ratio: { value: 0.8, provenance: "sample" }
      },
      perturbed_factors: PERTURBED_FACTORS,
      category: "price_variance"
    });
    setSampleRefusal(payload.error || "F-22: sample-provenance value cannot enter scoring");
  }

  return (
    <article className="copilot-card p-5" data-testid="counterfactual-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Counterfactual</p>
          <h2 className="text-lg font-semibold text-slate-950">What If?</h2>
        </div>
        {result ? <ProvenanceBadge source={result.provenance || "learned"} /> : null}
      </div>
      {!expanded ? (
        <button
          type="button"
          className="mt-4 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-900"
          onClick={() => setExpanded(true)}
        >
          View counterfactual
        </button>
      ) : loading ? (
        <p className="mt-3 text-sm text-slate-500">Calculating counterfactual...</p>
      ) : error ? (
        <p className="mt-3 text-sm text-slate-500">Counterfactual unavailable.</p>
      ) : (
        <div className="mt-4 space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <Metric label="Original score" value={value(result?.base_score)} />
            <Metric label="Perturbed score" value={value(result?.perturbed_score)} />
            <Metric label="Delta" value={delta(result?.delta)} />
          </div>
          <p className="text-sm text-slate-600">Changed: amount variance ratio (0.8 to 0.2)</p>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-slate-600">
                {sampleRefusal ? `Refused: ${sampleRefusal}` : "Try sample data to verify the F-22 gate."}
              </p>
              <button type="button" className="rounded-md bg-slate-950 px-3 py-2 text-sm font-semibold text-white" onClick={() => void trySample()}>
                Try sample
              </button>
            </div>
          </div>
        </div>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}
