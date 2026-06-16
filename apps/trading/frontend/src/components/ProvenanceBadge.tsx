interface ProvenanceBadgeProps {
  source: string;
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

export default function ProvenanceBadge({ source, asOf }: ProvenanceBadgeProps) {
  const normalized = source.toLowerCase();
  const label =
    normalized === "live"
      ? "Market data: live"
      : normalized === "cached"
        ? `Market data: cached${cachedAge(asOf)}`
        : "Market data: sample";
  const color =
    normalized === "live"
      ? "bg-emerald-500"
      : normalized === "cached"
        ? "bg-amber-500"
        : "bg-slate-400";

  return (
    <div className="mt-1 inline-flex items-center gap-2 text-xs trading-muted">
      <span className={`h-2 w-2 rounded-full ${color}`} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
