import { useEffect, useState } from "react";
import { fetchEnterpriseHealth } from "../api";
import type { EnterpriseSystemHealth } from "../types";

interface CelonisBadgeProps {
  km_name?: string;
  kmName?: string;
  variant_count?: number;
  variantCount?: number;
  live?: boolean;
  celonis?: EnterpriseSystemHealth;
}

export function CelonisBadge({
  km_name,
  kmName,
  variant_count,
  variantCount,
  live,
  celonis,
}: CelonisBadgeProps) {
  const [remoteCelonis, setRemoteCelonis] = useState<EnterpriseSystemHealth | null>(celonis ?? null);

  useEffect(() => {
    if (celonis) {
      setRemoteCelonis(celonis);
      return;
    }
    let cancelled = false;
    fetchEnterpriseHealth().then((health) => {
      if (!cancelled) {
        setRemoteCelonis(health?.celonis ?? null);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [celonis]);

  const km = kmName ?? km_name ?? "Process Intelligence";
  const variants = variantCount ?? variant_count ?? remoteCelonis?.kpiCount;
  const connected = live ?? remoteCelonis?.connected === true;
  const status = connected ? "Live" : "Offline";
  const statusClass = connected
    ? "border-emerald-300/40 bg-emerald-500/10 text-emerald-100"
    : "border-slate-500/40 bg-slate-500/10 text-slate-200";

  return (
    <span className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold ${statusClass}`}>
      {connected ? `Celonis · ${km}` : "Celonis Offline"}
      {typeof variants === "number" ? ` · ${variants} KPIs` : ""} · {status}
    </span>
  );
}
