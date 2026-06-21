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
    ? "border-emerald-300/50 bg-emerald-500/10 text-emerald-700"
    : isLearned
      ? "border-blue-300/50 bg-blue-500/10 text-blue-700"
      : isCached
        ? "border-slate-300/70 bg-slate-500/10 text-slate-600"
        : isSample
          ? "border-amber-300/70 bg-amber-500/10 text-amber-700"
          : "border-slate-300/70 bg-slate-100 text-slate-600";

  return (
    <span
      data-testid="provenance-badge"
      className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold ${style}`}
      title={`Source: ${normalized}`}
    >
      {label}
    </span>
  );
}
