interface AERecommendationBadgeProps {
  action?: string;
  variantId?: string;
  confidence?: number;
}

export default function AERecommendationBadge({ action, variantId, confidence }: AERecommendationBadgeProps) {
  const confidenceLabel = Number.isFinite(confidence) ? `${Math.round(Number(confidence) * 100)}%` : "n/a";

  return (
    <span
      className="inline-flex max-w-full items-center gap-2 rounded-full px-2 py-1 text-xs font-semibold"
      style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}
      title={variantId || "AgentEvolver recommendation"}
    >
      <span>AE</span>
      <span className="truncate">{action || "Recommendation"}</span>
      <span>{confidenceLabel}</span>
    </span>
  );
}
