// MIRROR of apps/trading/frontend/src/components/ProvenanceBadge.tsx
// Keep in sync. Workspace extraction planned for Phase 2.

interface ProvenanceBadgeProps {
  source: string;
  provenance?: string | null;
  asOf?: string | null;
  className?: string;
}

type BadgeStyle = {
  label: string;
  title: string;
  markerClass: string;
  badgeClass: string;
};

function cachedAge(asOf?: string | null): string {
  if (!asOf) return "";
  const timestamp = Date.parse(asOf);
  if (Number.isNaN(timestamp)) return "";
  const hours = Math.max(0, Math.round((Date.now() - timestamp) / (1000 * 60 * 60)));
  if (hours < 1) return " (<1h ago)";
  return ` (${hours}h ago)`;
}

function tierStyle(normalized: string, asOf?: string | null): BadgeStyle {
  if (normalized === "learned") {
    return {
      label: "██ learned",
      title: "Learned from verified decisions",
      markerClass: "bg-emerald-600",
      badgeClass: "border-emerald-600 bg-emerald-600 text-white",
    };
  }
  if (normalized === "context") {
    return {
      label: "░░ context",
      title: "Context data used for reasoning",
      markerClass: "bg-blue-500",
      badgeClass:
        "border-blue-300 bg-blue-50 text-blue-800 [background-image:repeating-linear-gradient(45deg,rgba(59,130,246,0.14)_0,rgba(59,130,246,0.14)_4px,transparent_4px,transparent_8px)]",
    };
  }
  if (normalized === "proven") {
    return {
      label: "proven",
      title: "Proven by audit or receipt evidence",
      markerClass: "bg-slate-500",
      badgeClass: "border-slate-400 bg-slate-100 text-slate-800",
    };
  }
  if (normalized === "sample") {
    return {
      label: "sample (demo)",
      title: "Demo sample data",
      markerClass: "bg-orange-500",
      badgeClass: "border-dashed border-orange-400 bg-orange-50 text-orange-800",
    };
  }
  if (normalized === "live" || normalized === "scraped_external") {
    return {
      label: "░░ External",
      title: "Real external context (░░) - real data, not yet customer-specific",
      markerClass: "bg-emerald-500",
      badgeClass: "border-emerald-300 bg-emerald-50 text-emerald-800",
    };
  }
  if (normalized === "real_measured" || normalized === "verified") {
    return {
      label: "██ Learned",
      title: "Learned from your decisions (██) - measured, not synthesized",
      markerClass: "bg-blue-500",
      badgeClass: "border-blue-300 bg-blue-50 text-blue-800",
    };
  }
  if (normalized === "transfer") {
    return {
      label: "Transfer",
      title: "Transferred from compatible learned context",
      markerClass: "bg-violet-500",
      badgeClass: "border-violet-300 bg-violet-50 text-violet-800",
    };
  }
  if (normalized === "cached") {
    return {
      label: `Market data: cached${cachedAge(asOf)}`,
      title: `Cached real external context${cachedAge(asOf)}`,
      markerClass: "bg-amber-500",
      badgeClass: "border-amber-300 bg-amber-50 text-amber-800",
    };
  }
  return {
    label: "Sample",
    title: "Demo data - excluded from all metrics and scores",
    markerClass: "bg-slate-400",
    badgeClass: "border-slate-300 bg-slate-100 text-slate-700",
  };
}

export function ProvenanceBadge({ source, provenance, asOf, className = "" }: ProvenanceBadgeProps) {
  const normalized = String(provenance || source || "sample").toLowerCase();
  const meta = tierStyle(normalized, asOf);

  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 rounded border px-2 py-0.5 text-[11px] font-semibold ${meta.badgeClass} ${className}`}
      title={meta.title}
      aria-label={meta.title}
    >
      <span className={`h-2 w-2 rounded-full ${meta.markerClass}`} aria-hidden="true" />
      <span>{meta.label}</span>
    </span>
  );
}

export default ProvenanceBadge;
