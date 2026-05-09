import type { Analytics, Variant } from "../types";

function pct(value?: number) {
  return Number.isFinite(value) ? `${Math.round(Number(value) * 100)}%` : "n/a";
}

function money(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toFixed(0)}` : "$0";
}

interface AEStatusBarProps {
  analytics?: Analytics;
  variants?: Variant[];
}

function isRejectedVariant(variant: Variant) {
  const eventType = String(variant.eventType ?? variant.event_type ?? "");
  const status = String(variant.status ?? "");
  return eventType === "promotion_rejected" || status === "rejected";
}

function isApprovedVariant(variant: Variant) {
  if (isRejectedVariant(variant)) {
    return false;
  }
  const eventType = String(variant.eventType ?? variant.event_type ?? "");
  const status = String(variant.status ?? "");
  return (
    eventType === "promotion_approved" ||
    status === "promoted" ||
    status === "approved"
  );
}

export default function AEStatusBar({ analytics, variants }: AEStatusBarProps) {
  const ae = analytics?.aeImpact;
  const managed = ae?.managedByRules;
  const unmanaged = ae?.unmanaged;
  const activeVariants = (variants ?? []).filter(isApprovedVariant);
  const rejectedVariants = (variants ?? []).filter(isRejectedVariant);

  return (
    <section className="purchase-card ae-status-bar">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Autonomous execution</p>
          <h2 className="purchase-title">Items you are consistent on can be managed</h2>
        </div>
        <span className="purchase-pill ae-pill">{activeVariants.length} AE rules</span>
      </div>
      <div className="ae-status-grid">
        <div>
          <span>Managed accuracy</span>
          <strong>{pct(managed?.accuracy)}</strong>
          <small>{managed?.count ?? 0} orders</small>
        </div>
        <div>
          <span>Manual accuracy</span>
          <strong>{pct(unmanaged?.accuracy)}</strong>
          <small>{unmanaged?.count ?? 0} orders</small>
        </div>
        <div>
          <span>Promoted savings</span>
          <strong>{money(ae?.estimatedSavingsFromPromotedRules)}</strong>
          <small>{managed?.matchedRules ?? 0} matched rules | {rejectedVariants.length} rejected excluded</small>
        </div>
      </div>
    </section>
  );
}
