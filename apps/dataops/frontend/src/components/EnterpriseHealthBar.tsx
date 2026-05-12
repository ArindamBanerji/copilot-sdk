import { useEffect, useState } from "react";
import { fetchEnterpriseHealth } from "../api";
import type { EnterpriseHealth, EnterpriseSystemHealth } from "../types";

function statusFor(system?: EnterpriseSystemHealth) {
  if (!system) {
    return { label: "unavailable", live: false };
  }

  const status = `${system.status ?? system.source ?? ""}`.toLowerCase();
  const live = system.live === true || status.includes("live") || status.includes("connected");
  const cached = system.cached === true || status.includes("cache") || status.includes("cached");

  return {
    label: live ? "Live" : cached ? "cached" : system.status ?? "unavailable",
    live,
  };
}

function HealthPill({ label, system }: { label: string; system?: EnterpriseSystemHealth }) {
  const status = statusFor(system);
  const tone = status.live
    ? "border-emerald-300/40 bg-emerald-500/10 text-emerald-100"
    : "border-amber-300/40 bg-amber-500/10 text-amber-100";

  return (
    <div className={`rounded-md border px-3 py-2 ${tone}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-current/70">{label}</p>
      <p className="mt-1 text-sm font-semibold">{status.label}</p>
    </div>
  );
}

export function EnterpriseHealthBar() {
  const [health, setHealth] = useState<EnterpriseHealth | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchEnterpriseHealth().then((data) => {
      if (!cancelled) {
        setHealth(data);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="rounded-md border border-white/10 bg-white/[0.04] p-4 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-purple-200/75">
            Enterprise Health
          </p>
          <h2 className="mt-1 text-lg font-semibold text-white">Process-Tech Fusion</h2>
        </div>
        <p className="text-sm text-slate-300">engine {health?.engineVersion ?? "v0.7.23"}</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <HealthPill label="SAP S/4HANA" system={health?.sap} />
        <HealthPill label="Celonis" system={health?.celonis} />
        <HealthPill label="Graph" system={health?.graph} />
      </div>
    </section>
  );
}
