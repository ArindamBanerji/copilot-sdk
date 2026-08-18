interface EvidenceTierBadgeProps {
  tier?: string;
  label?: string;
}

export default function EvidenceTierBadge({ tier = "T_S", label }: EvidenceTierBadgeProps) {
  const measured = tier === "T_O" || tier === "T_R";
  return (
    <span
      data-testid="evidence-tier-badge"
      className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${measured ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}
      title={label || (measured ? "Measured evidence" : "Synthetic or modelled evidence; not measured")}
    >
      {tier}: {label || (measured ? "measured" : "synthetic / modelled — not measured")}
    </span>
  );
}
