type ProvenanceBadgeProps = {
  source?: string | null;
  provenance?: string | null;
  asOf?: string | null;
  className?: string;
};

type ProvenanceKind = "external" | "learned" | "sample";

function normalize(source?: string | null, provenance?: string | null): ProvenanceKind {
  const value = `${provenance ?? ""} ${source ?? ""}`.toLowerCase();
  if (value.includes("sample") || value.includes("fixture") || value.includes("demo")) return "sample";
  if (value.includes("learned") || value.includes("verified") || value.includes("real_measured") || value.includes("computed")) return "learned";
  return "external";
}

const META: Record<ProvenanceKind, { label: string; title: string; className: string }> = {
  external: {
    label: "░░ External",
    title: "Real external context -- not yet customer-specific",
    className: "border-emerald-300 bg-emerald-50 text-emerald-800",
  },
  learned: {
    label: "██ Learned",
    title: "Learned from your verified decisions",
    className: "border-blue-300 bg-blue-50 text-blue-800",
  },
  sample: {
    label: "Sample",
    title: "Demo data -- excluded from all metrics",
    className: "border-slate-300 bg-slate-100 text-slate-700",
  },
};

export function ProvenanceBadge({ source, provenance, asOf, className = "" }: ProvenanceBadgeProps) {
  const meta = META[normalize(source, provenance)];
  const title = asOf ? `${meta.title}. As of ${asOf}` : meta.title;

  return (
    <span
      className={`inline-flex shrink-0 items-center rounded border px-2 py-0.5 text-[11px] font-semibold ${meta.className} ${className}`}
      title={title}
      aria-label={title}
    >
      {meta.label}
    </span>
  );
}
