interface ProvenanceBadgeProps {
  source?: string | null;
  provenance?: string | null;
  asOf?: string | null;
}

function cachedAge(asOf?: string | null): string {
  if (!asOf) return "";
  const timestamp = Date.parse(asOf);
  if (Number.isNaN(timestamp)) return "";
  const hours = Math.max(0, Math.round((Date.now() - timestamp) / (1000 * 60 * 60)));
  if (hours < 1) return " (<1h ago)";
  return ` (${hours}h ago)`;
}

function normalizeSource(value?: string | null): string {
  return (value || "unknown").toLowerCase();
}

export default function ProvenanceBadge({ source, provenance, asOf }: ProvenanceBadgeProps) {
  const normalized = normalizeSource(provenance ?? source);
  const isExternal = normalized === "scraped_external" || normalized === "live";
  const isLearned = normalized === "real_measured" || normalized === "learned" || normalized === "verified";
  const isCached = normalized === "cached" || normalized === "stale_cached";
  const isSample = normalized === "sample" || normalized === "fixture";
  const label = isExternal
    ? "░░ External"
    : isLearned
      ? "██ Learned"
      : isCached
        ? `Cached${cachedAge(asOf)}`
        : isSample
          ? "Sample"
          : "Unlabeled";
  const style = isExternal
    ? "border-emerald-300/40 bg-emerald-500/10 text-emerald-100"
    : isLearned
      ? "border-blue-300/40 bg-blue-500/10 text-blue-100"
      : isCached
        ? "border-slate-500/40 bg-slate-500/10 text-slate-200"
        : isSample
          ? "border-amber-300/50 bg-amber-500/10 text-amber-100"
          : "border-slate-500/40 bg-slate-500/10 text-slate-200";

  return (
    <span
      data-testid="provenance-badge"
      className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold ${style}`}
      title={isExternal ? "Real external context (░░) - real data, not yet customer-specific" : isLearned ? "Learned from your decisions (██) - measured, not synthesized" : isSample ? "Demo data - excluded from all metrics and scores" : `Source: ${normalized}`}
    >
      {label}
    </span>
  );
}
