import { useEffect, useState } from "react";
import { apiGet, postCounterfactual, type CounterfactualResponse } from "../api";
import type { Analytics } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

// NOTE: This component is duplicated in copilot-sdk/apps/s2p/frontend/src/components/CounterfactualCard.tsx.
// If you modify this file, update the counterpart.
// Duplication exists because SDK apps and S2P have separate frontend build pipelines.
// A shared component library would eliminate this but is out of scope for this batch.

const BASE_FACTORS = {
  signal_alignment: 0.8,
  market_regime: 0.7,
  position_sizing: 0.6,
  timing_quality: 0.6,
  risk_reward_actual: 0.7,
  emotional_indicator: 0.5,
};

const PERTURBED_FACTORS = {
  ...BASE_FACTORS,
  signal_alignment: 0.2,
};

function score(value: number | undefined): string {
  return typeof value === "number" ? value.toFixed(2) : "-";
}

function delta(value: number | undefined): string {
  if (typeof value !== "number") return "-";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}

export default function CounterfactualCard(_props: { analytics?: Analytics }) {
  const [result, setResult] = useState<CounterfactualResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sampleRefusal, setSampleRefusal] = useState<string | null>(null);
  const [signalAlignment, setSignalAlignment] = useState(20);

  useEffect(() => {
    let cancelled = false;
    apiGet<CounterfactualResponse>("/api/trading/score/counterfactual/default")
      .then((payload) => {
        if (!cancelled) setResult(payload);
      })
      .catch((loadError) => {
        console.debug("counterfactual unavailable", loadError);
        if (!cancelled) setError("Counterfactual unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function trySample() {
    const payload = await postCounterfactual({
      base_factors: {
        ...BASE_FACTORS,
        signal_alignment: { value: 0.8, provenance: "sample" },
      },
      perturbed_factors: PERTURBED_FACTORS,
      category: "trend_following",
    });
    setSampleRefusal(payload.error || "F-22: sample-provenance value cannot enter scoring");
  }

  async function rescore() {
    setLoading(true);
    setError(null);
    try {
      const payload = await postCounterfactual({
        base_factors: BASE_FACTORS,
        perturbed_factors: { ...BASE_FACTORS, signal_alignment: signalAlignment / 100 },
        category: "trend_following",
      });
      setResult(payload);
    } catch (loadError) {
      console.debug("counterfactual re-score unavailable", loadError);
      setError("Counterfactual unavailable.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="copilot-card p-4" data-testid="counterfactual-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-base font-semibold">What If?</h2>
        {result && <ProvenanceBadge source={result.provenance || "learned"} />}
      </div>
      {loading && <p className="mt-3 text-sm trading-muted">Calculating counterfactual...</p>}
      {!loading && error && <p className="mt-3 text-sm trading-muted">Counterfactual unavailable.</p>}
      {!loading && !error && (
        <div className="mt-4 space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <Stat label="Original score" value={score(result?.baseScore)} testId="counterfactual-base-score" />
            <Stat label="Perturbed score" value={score(result?.perturbedScore)} testId="counterfactual-perturbed-score" />
            <Stat label="Delta" value={delta(result?.delta)} testId="counterfactual-delta" />
          </div>
          <p className="text-sm trading-muted">
            Signal alignment: {signalAlignment}%
          </p>
          <div className="rounded-md border px-3 py-3" style={{ borderColor: "var(--copilot-border)" }}>
            <label htmlFor="counterfactual-signal-alignment" className="text-sm font-semibold">Perturb signal alignment</label>
            <input
              id="counterfactual-signal-alignment"
              data-testid="counterfactual-factor-slider"
              className="mt-2 w-full"
              type="range"
              min="0"
              max="100"
              step="1"
              value={signalAlignment}
              onChange={(event) => setSignalAlignment(Number(event.target.value))}
            />
            <button type="button" className="trading-button mt-3" onClick={() => void rescore()}>
              Re-score
            </button>
          </div>
          <div className="rounded-md border px-3 py-3" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold">Try feeding sample data</div>
                <div className="text-sm trading-muted">
                  {sampleRefusal ? `REFUSED: ${sampleRefusal}` : "Sample values must be rejected before scoring."}
                </div>
              </div>
              <button type="button" className="trading-button" onClick={() => void trySample()}>
                Try sample
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function Stat({ label, value, testId }: { label: string; value: string; testId: string }) {
  return (
    <div className="rounded-md border px-3 py-2" data-testid={testId} style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
