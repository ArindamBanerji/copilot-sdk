interface CelonisBadgeProps {
  km_name?: string;
  kmName?: string;
  variant_count?: number;
  variantCount?: number;
  live?: boolean;
}

export function CelonisBadge({
  km_name,
  kmName,
  variant_count,
  variantCount,
  live,
}: CelonisBadgeProps) {
  const km = kmName ?? km_name ?? "Process Intelligence";
  const variants = variantCount ?? variant_count;
  const status = live ? "Live" : "cached";
  const statusClass = live
    ? "border-emerald-300/40 bg-emerald-500/10 text-emerald-100"
    : "border-amber-300/40 bg-amber-500/10 text-amber-100";

  return (
    <span className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold ${statusClass}`}>
      Celonis · {km}
      {typeof variants === "number" ? ` · ${variants} variants` : ""} · {status}
    </span>
  );
}
