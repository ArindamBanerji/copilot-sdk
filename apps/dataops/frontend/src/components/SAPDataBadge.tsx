import { useEffect, useState } from "react";
import { fetchEnterpriseHealth } from "../api";
import type { EnterpriseSystemHealth } from "../types";

interface SAPDataBadgeProps {
  po_count?: number;
  poCount?: number;
  variant_text?: string;
  variantText?: string;
  sap?: EnterpriseSystemHealth;
}

export function SAPDataBadge({
  po_count,
  poCount,
  variant_text,
  variantText,
  sap,
}: SAPDataBadgeProps) {
  const [remoteSap, setRemoteSap] = useState<EnterpriseSystemHealth | null>(sap ?? null);

  useEffect(() => {
    if (sap) {
      setRemoteSap(sap);
      return;
    }
    let cancelled = false;
    fetchEnterpriseHealth().then((health) => {
      if (!cancelled) {
        setRemoteSap(health?.sap ?? null);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [sap]);

  const count = poCount ?? po_count ?? remoteSap?.recordCount;
  const variant = variantText ?? variant_text;
  const connected = remoteSap?.connected === true;
  const status = remoteSap?.source === "fixture" ? "Fixture" : connected ? "Live" : "Offline";
  const tone = connected
    ? "border-emerald-300/40 bg-emerald-500/10 text-emerald-100"
    : "border-slate-500/40 bg-slate-500/10 text-slate-200";

  return (
    <span className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold ${tone}`}>
      {connected || status === "Fixture" ? "SAP S/4HANA" : "SAP Offline"}
      {typeof count === "number" ? ` · ${count} records` : ""}
      {variant ? ` · ${variant}` : ""} · {status}
    </span>
  );
}
