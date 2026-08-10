import { useEffect, useState } from "react";
import { getDIPerturbationStatus, getTrust, perturbDI, revertDIPerturbation } from "../api";
import type { TrustFactor, TrustResponse } from "../types";

interface TrustCardProps {
  trust: TrustResponse | null;
}

const BAR_COLORS: Record<string, string> = {
  reliable: "#35b779",
  moderate: "#e5a93d",
  noisy: "#d95d6a",
};

export default function TrustCard({ trust }: TrustCardProps) {
  const [displayTrust, setDisplayTrust] = useState(trust);
  const [demoEnabled, setDemoEnabled] = useState(false);
  const [active, setActive] = useState(false);
  const [sourceName, setSourceName] = useState("snowflake");
  const [magnitude, setMagnitude] = useState(0.5);
  const [busy, setBusy] = useState(false);
  const [statusText, setStatusText] = useState("");

  useEffect(() => {
    setDisplayTrust(trust);
  }, [trust]);

  useEffect(() => {
    void getDIPerturbationStatus().then((status) => {
      setDemoEnabled(status.enabled);
      setActive(status.active);
    }).catch(() => setDemoEnabled(false));
  }, []);

  async function runPerturbation() {
    setBusy(true);
    try {
      const result = await perturbDI({ sourceName, perturbation: "degrade", magnitude, decisions: 20 });
      const refreshed = await getTrust();
      setDisplayTrust(refreshed);
      setActive(true);
      setStatusText(`Perturbation active — ${result.decisionsInjected} synthetic decisions injected`);
    } catch (error) {
      setStatusText(error instanceof Error ? error.message : "Perturbation failed");
    } finally {
      setBusy(false);
    }
  }

  async function revertPerturbation() {
    setBusy(true);
    try {
      await revertDIPerturbation();
      setDisplayTrust(await getTrust());
      setActive(false);
      setStatusText("Perturbation reverted — trust restored");
    } catch (error) {
      setStatusText(error instanceof Error ? error.message : "Revert failed");
    } finally {
      setBusy(false);
    }
  }

  const shownTrust = displayTrust;
  return (
    <section className="copilot-card p-4" data-testid="trust-card" aria-label="Source reliability trust profile">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em]" style={{ color: "#9b7cff" }}>
            SC-TRUST
          </p>
          <h2 className="mt-1 dataops-section-title">Source reliability</h2>
        </div>
        {shownTrust ? <TrustScore value={shownTrust.overallTrust} /> : null}
      </div>

      {shownTrust ? (
        <>
          <div className="mt-4 grid gap-3" role="list" aria-label="Learned source reliability factors">
            {shownTrust.factors.map((factor) => (
              <TrustFactorBar factor={factor} key={factor.name} />
            ))}
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full px-2 py-1 font-semibold" style={conservationStyle(shownTrust.conservationStatus)}>
              Conservation {shownTrust.conservationStatus}
            </span>
            <span className="dataops-muted">{shownTrust.verifiedDecisions} verified decisions</span>
            {shownTrust.iks !== null ? <span className="dataops-muted">IKS {shownTrust.iks.toFixed(1)}</span> : null}
          </div>
          <p className="mt-4 text-sm leading-6 dataops-muted">{shownTrust.narrative}</p>
          {demoEnabled ? (
            <div className="mt-5 rounded-md border border-purple-300/20 bg-purple-500/[0.05] p-3" data-testid="trust-perturbation">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-purple-200/75">DI-PROOF · What-if</p>
                {active ? <span className="rounded-full bg-red-500/15 px-2 py-1 text-xs font-semibold text-red-200">Active</span> : null}
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <label className="text-xs dataops-muted" htmlFor="trust-perturb-source">Source</label>
                <select id="trust-perturb-source" data-testid="trust-perturb-source" value={sourceName} onChange={(event) => setSourceName(event.target.value)} disabled={busy || active} className="rounded border px-2 py-1 text-sm">
                  <option value="snowflake">Snowflake</option>
                  <option value="airflow">Airflow</option>
                  <option value="dbt">dbt</option>
                </select>
                <label className="text-xs dataops-muted" htmlFor="trust-perturb-magnitude">Magnitude {magnitude.toFixed(1)}</label>
                <input id="trust-perturb-magnitude" data-testid="trust-perturb-magnitude" type="range" min="0.1" max="0.9" step="0.1" value={magnitude} onChange={(event) => setMagnitude(Number(event.target.value))} disabled={busy || active} />
                {!active ? <button type="button" data-testid="trust-perturb-button" className="copilot-button px-3 py-1 text-xs" disabled={busy} onClick={() => void runPerturbation()}>Perturb</button> : <button type="button" data-testid="trust-revert-button" className="copilot-button-secondary px-3 py-1 text-xs" disabled={busy} onClick={() => void revertPerturbation()}>Revert</button>}
              </div>
              {statusText ? <p className="mt-2 text-xs dataops-muted" data-testid="trust-perturbation-status">{statusText}</p> : null}
            </div>
          ) : null}
        </>
      ) : (
        <p className="mt-4 text-sm dataops-muted">Trust profile unavailable.</p>
      )}
    </section>
  );
}

function TrustScore({ value }: { value: number }) {
  return (
    <div className="text-right">
      <div className="text-3xl font-bold" style={{ color: "#9b7cff" }}>{value.toFixed(2)}</div>
      <div className="text-[0.65rem] uppercase tracking-[0.12em] dataops-muted">overall trust</div>
    </div>
  );
}

function TrustFactorBar({ factor }: { factor: TrustFactor }) {
  const width = `${Math.round(Math.max(0, Math.min(1, factor.dkWeight)) * 100)}%`;
  const color = BAR_COLORS[factor.label] || "#9b7cff";
  return (
    <div data-testid="trust-factor" role="listitem">
      <div className="mb-1 flex items-center justify-between gap-3 text-xs">
        <span className="font-medium" style={{ color: "var(--copilot-text)" }}>{factor.name}</span>
        <span style={{ color }}>{factor.dkWeight.toFixed(2)} · {factor.label}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full" style={{ background: "var(--copilot-border)" }}>
        <div className="h-full rounded-full" style={{ width, background: color }} aria-label={`${factor.name} reliability ${factor.dkWeight.toFixed(2)}`} />
      </div>
    </div>
  );
}

function conservationStyle(status: string): React.CSSProperties {
  const normalized = status.toUpperCase();
  if (normalized === "GREEN") {
    return { background: "rgba(53, 183, 121, 0.16)", color: "#35b779" };
  }
  if (normalized === "RED") {
    return { background: "rgba(217, 93, 106, 0.16)", color: "#d95d6a" };
  }
  return { background: "rgba(229, 169, 61, 0.16)", color: "#e5a93d" };
}
