import type { Analytics } from "../types";

interface CounterfactualCardProps {
  analytics?: Analytics;
}

function money(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toFixed(0)}` : "n/a";
}

function pct(value?: number) {
  return Number.isFinite(value) ? `${(Number(value) * 100).toFixed(0)}%` : "n/a";
}

export default function CounterfactualCard({ analytics }: CounterfactualCardProps) {
  const counterfactual = analytics?.counterfactual;
  return (
    <section className="purchase-card">
      <p className="purchase-kicker">Counterfactual</p>
      <h2 className="purchase-title">{counterfactual?.scenario ?? "No counterfactual available"}</h2>
      <div className="stats-row">
        <div><span>Orders adjusted</span><strong>{counterfactual?.ordersAdjusted ?? 0}</strong></div>
        <div><span>Dollars saved</span><strong>{money(counterfactual?.dollarsSaved)}</strong></div>
        <div><span>Original accuracy</span><strong>{pct(Number(counterfactual?.originalAccuracy))}</strong></div>
        <div><span>Adjusted accuracy</span><strong>{pct(Number(counterfactual?.adjustedAccuracy))}</strong></div>
      </div>
      <p className="purchase-muted">{counterfactual?.explanation ?? "Applying proven AE rules reduces the visible waste leak."}</p>
    </section>
  );
}
