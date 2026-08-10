import { useEffect, useState } from "react";
import { BASE, fetchEnterpriseHealth } from "../api";
import type { EnterpriseHealth, EnterpriseSystemHealth } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

function sourceLabel(system?: EnterpriseSystemHealth): "Connected" | "Sample" | "Offline" {
  if (!system) return "Offline";
  if (system.live === true || system.source?.endsWith("_live")) return "Connected";
  if (system.source?.includes("cache") || system.source === "fixture" || system.cached === true) return "Sample";
  return system.connected === true ? "Connected" : "Offline";
}

function statusClass(status: string): string {
  if (status === "Connected") return "border-emerald-300/30 bg-emerald-500/10 text-emerald-100";
  if (status === "Sample") return "border-amber-300/30 bg-amber-500/10 text-amber-100";
  return "border-slate-400/20 bg-slate-500/10 text-slate-300";
}

function SystemStatus({ label, system }: { label: string; system?: EnterpriseSystemHealth }) {
  const status = sourceLabel(system);
  return (
    <div className={`rounded-md border px-3 py-2 ${statusClass(status)}`}>
      <div className="text-xs font-semibold uppercase tracking-[0.16em]">{label}</div>
      <div className="mt-1 flex items-center gap-2 text-sm">
        <span aria-hidden="true">●</span>
        <span>{status}</span>
        <ProvenanceBadge source={status === "Connected" ? "live" : "sample"} />
      </div>
    </div>
  );
}

/** Buyer-facing ENT-1 framing: existing enterprise systems become more valuable. */
export function EnterpriseValueCard() {
  const [health, setHealth] = useState<EnterpriseHealth | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchEnterpriseHealth().then((payload) => {
      if (mounted) setHealth(payload);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const sampleMode = sourceLabel(health?.sap) === "Sample" || sourceLabel(health?.celonis) === "Sample";
  const impact = health?.combinedImpact;
  const dollarValue = impact?.openPurchaseOrderValue;
  const dollarLabel = typeof dollarValue === "number"
    ? `$${Math.round(dollarValue).toLocaleString()}`
    : "$604K";

  return (
    <section data-testid="enterprise-value-card" className="rounded-lg border border-purple-300/20 bg-gradient-to-br from-purple-500/10 via-white/[0.04] to-cyan-500/10 p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-purple-200/80">ENT-1 · Sunk-Investment Multiplier</p>
          <h2 className="mt-1 text-lg font-semibold text-white">Enterprise Systems Integration</h2>
        </div>
        <span className="rounded-full border border-purple-200/30 px-3 py-1 text-xs text-purple-100">Your existing systems, more valuable</span>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <SystemStatus label="SAP S/4HANA" system={health?.sap} />
        <SystemStatus label="Celonis" system={health?.celonis} />
      </div>

      <div className="mt-4 rounded-md border border-white/10 bg-black/10 p-3">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-200/80">Combined insight</p>
        <p className="mt-2 text-sm leading-6 text-slate-100">
          Celonis sees WHERE. SAP sees WHAT. The graph sees WHY — and the <strong>{dollarLabel}</strong>.
        </p>
      </div>

      {sampleMode ? (
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-amber-100">
          <ProvenanceBadge source="sample" />
          <span>Running on sample data. Connect live SAP/Celonis for your data.</span>
        </div>
      ) : null}

      <a
        className="mt-4 inline-flex items-center rounded-md border border-cyan-300/30 px-3 py-2 text-sm font-medium text-cyan-100 transition hover:bg-cyan-400/10"
        href={`${BASE}/api/discovery/cross-system`}
        target="_blank"
        rel="noreferrer"
      >
        Open cross-graph discovery →
      </a>
    </section>
  );
}

export default EnterpriseValueCard;
