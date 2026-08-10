interface ProvenanceBadgeProps {
  source: string;
  asOf?: string | null;
  market?: boolean;
}

function cachedAge(asOf?: string | null): string {
  if (!asOf) return "";
  const timestamp = Date.parse(asOf);
  if (Number.isNaN(timestamp)) return "";
  const hours = Math.max(0, Math.round((Date.now() - timestamp) / (1000 * 60 * 60)));
  if (hours < 1) return " (<1h ago)";
  return ` (${hours}h ago)`;
}

export default function ProvenanceBadge({ source, asOf, market = false }: ProvenanceBadgeProps) {
  const normalized = source.toLowerCase();
  const label =
    normalized === "live" || normalized === "scraped_external"
      ? "Market data: live external"
      : normalized === "instrument"
        ? "Instrument"
      : normalized === "accumulating"
        ? "Accumulating"
      : normalized === "illustrative"
        ? "Illustrative demo"
      : normalized === "real_measured" || normalized === "learned" || normalized === "verified"
        ? "██ Learned"
      : normalized === "cached"
        ? `Market data: cached${cachedAge(asOf)}`
        : market
          ? "Market data: sample"
        : "Sample";
  const title =
    normalized === "live" || normalized === "scraped_external"
      ? "Real external context (░░) - real data, not yet customer-specific"
      : normalized === "instrument"
        ? "Instrument calibrated - no measured magnitude claimed yet"
      : normalized === "accumulating"
        ? "Verified decisions are accumulating - magnitude withheld until measured"
      : normalized === "illustrative"
        ? "Illustrative demo magnitude (T-O) - not measured performance"
      : normalized === "real_measured" || normalized === "learned" || normalized === "verified"
        ? "Learned from your decisions (██) - measured, not synthesized"
        : normalized === "cached"
          ? `Cached real external context${cachedAge(asOf)}`
          : "Demo data - excluded from all metrics and scores";
  const color =
    normalized === "live" || normalized === "scraped_external"
      ? "bg-emerald-500"
      : normalized === "instrument"
        ? "bg-slate-500"
      : normalized === "accumulating"
        ? "bg-amber-500"
      : normalized === "illustrative"
        ? "bg-violet-400"
      : normalized === "real_measured" || normalized === "learned" || normalized === "verified"
        ? "bg-blue-500"
      : normalized === "cached"
        ? "bg-amber-500"
        : "bg-slate-400";

  return (
    <div data-testid="provenance-badge" className="mt-1 inline-flex items-center gap-2 text-xs trading-muted" title={title}>
      <span className={`h-2 w-2 rounded-full ${color}`} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
