import { useEffect, useState } from "react";
import { fetchEnterpriseHealth } from "../api";
import type { EnterpriseHealth, EnterpriseSystemHealth } from "../types";

function statusFor(system?: EnterpriseSystemHealth) {
  if (!system) {
    return { label: "unavailable", connected: false };
  }

  const connected = system.connected === true || system.live === true;
  return { label: connected ? "Connected" : "Offline", connected };
}

function HealthPill({
  label,
  system,
  metric,
}: {
  label: string;
  system?: EnterpriseSystemHealth;
  metric: string;
}) {
  const status = statusFor(system);
  const tone = status.connected
    ? "border-emerald-300/40 bg-emerald-500/10 text-emerald-100"
    : "border-slate-500/40 bg-slate-500/10 text-slate-200";

  return (
    <div className={`rounded-md border px-3 py-2 ${tone}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-current/70">{label}</p>
      <p className="mt-1 text-sm font-semibold">{status.label}</p>
      <p className="mt-0.5 text-xs text-current/70">{metric}</p>
    </div>
  );
}

export function EnterpriseHealthBar() {
  const [health, setHealth] = useState<EnterpriseHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetchEnterpriseHealth().then((data) => {
      if (!cancelled) {
        setHealth(data);
        setLoading(false);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const overall = health?.overall ?? (loading ? "loading" : "disconnected");
  const overallClass = overall === "healthy"
    ? "border-emerald-300/40 bg-emerald-500/10 text-emerald-100"
    : overall === "degraded"
      ? "border-amber-300/40 bg-amber-500/10 text-amber-100"
      : "border-slate-500/40 bg-slate-500/10 text-slate-200";

  return (
    <section className="rounded-md border border-white/10 bg-white/[0.04] p-4 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-purple-200/75">
            Enterprise Health
          </p>
          <h2 className="mt-1 text-lg font-semibold text-white">Process-Tech Fusion</h2>
        </div>
        <span className={`rounded-md border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] ${overallClass}`}>
          {overall}
        </span>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <HealthPill label="SAP S/4HANA" system={health?.sap} metric={`${health?.sap?.recordCount ?? 0} records`} />
        <HealthPill label="Celonis" system={health?.celonis} metric={`${health?.celonis?.kpiCount ?? 0} KPIs`} />
        <HealthPill label="Graph" system={health?.graph} metric={`${health?.graph?.nodeCount ?? 0} nodes`} />
      </div>
    </section>
  );
}
