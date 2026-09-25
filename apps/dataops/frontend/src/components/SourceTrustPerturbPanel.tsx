import { useMemo, useState } from "react";

import { BASE } from "../api";

type PerturbationType = "degrade" | "improve";

interface TrustPerturbationResult {
  source_id: string;
  trust_before: number;
  trust_after: number;
  decisions_injected: number;
  conservation_status: string;
}

const SOURCES = [
  { id: "sap_s4hana", label: "SAP S/4HANA" },
  { id: "celonis_p2p", label: "Celonis P2P" },
  { id: "snowflake", label: "Snowflake" },
  { id: "airflow", label: "Airflow" },
  { id: "dbt", label: "dbt" },
];

export default function SourceTrustPerturbPanel() {
  const [sourceId, setSourceId] = useState(SOURCES[0].id);
  const [magnitude, setMagnitude] = useState(0.15);
  const [result, setResult] = useState<TrustPerturbationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const displayedTrust = useMemo(() => result?.trust_after, [result]);

  async function request(path: string, payload: Record<string, unknown>) {
    const response = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json() as TrustPerturbationResult & { detail?: string; trust_reset_to?: number };
    if (!response.ok) throw new Error(data.detail || "Trust perturbation request failed.");
    return data;
  }

  async function perturb(perturbationType: PerturbationType) {
    setBusy(true);
    setMessage("");
    try {
      const next = await request("/api/dataops/trust/perturb", {
        source_id: sourceId,
        perturbation_type: perturbationType,
        magnitude,
        decisions: 5,
      });
      setResult(next);
      setMessage(`${next.decisions_injected} simulated verified outcomes applied.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Trust perturbation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function reset() {
    setBusy(true);
    setMessage("");
    try {
      const next = await request("/api/dataops/trust/reset", { source_id: sourceId });
      const resetTrust = Number(next.trust_reset_to ?? 0);
      setResult({
        source_id: sourceId,
        trust_before: displayedTrust ?? resetTrust,
        trust_after: resetTrust,
        decisions_injected: 0,
        conservation_status: next.conservation_status,
      });
      setMessage("Trust restored to its demo baseline.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Trust reset failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="copilot-card p-4" data-testid="source-trust-perturb-panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-purple-200/75">DEMO</p>
          <h2 className="mt-1 dataops-section-title">Live source trust</h2>
          <p className="mt-1 text-sm dataops-muted">Simulated perturbation for demonstration.</p>
        </div>
        {displayedTrust !== undefined ? (
          <div className="text-right" aria-live="polite">
            <div className="text-3xl font-bold text-purple-200 transition-all duration-500">{Math.round(displayedTrust * 100)}%</div>
            <div className="text-xs dataops-muted">source trust</div>
          </div>
        ) : null}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <label className="text-sm dataops-muted">
          Source
          <select className="mt-1 w-full rounded border px-3 py-2 text-sm" value={sourceId} disabled={busy} onChange={(event) => setSourceId(event.target.value)}>
            {SOURCES.map((source) => <option key={source.id} value={source.id}>{source.label}</option>)}
          </select>
        </label>
        <label className="text-sm dataops-muted">
          Magnitude {magnitude.toFixed(2)}
          <input className="mt-2 w-full" type="range" min="0.05" max="0.30" step="0.05" value={magnitude} disabled={busy} onChange={(event) => setMagnitude(Number(event.target.value))} />
        </label>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" className="rounded bg-red-500/80 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={busy} onClick={() => void perturb("degrade")}>Degrade Trust</button>
        <button type="button" className="rounded bg-emerald-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={busy} onClick={() => void perturb("improve")}>Improve Trust</button>
        <button type="button" className="copilot-button-secondary px-3 py-2 text-sm" disabled={busy} onClick={() => void reset()}>Reset</button>
      </div>

      {result ? (
        <div className="mt-4 flex flex-wrap items-center gap-2 text-sm" aria-live="polite">
          <span className="dataops-muted">{Math.round(result.trust_before * 100)}% → {Math.round(result.trust_after * 100)}%</span>
          <span className="rounded-full bg-purple-500/15 px-2 py-1 text-xs font-semibold text-purple-100">Conservation {result.conservation_status}</span>
        </div>
      ) : null}
      {message ? <p className="mt-3 text-sm dataops-muted" role="status">{message}</p> : null}
    </section>
  );
}
