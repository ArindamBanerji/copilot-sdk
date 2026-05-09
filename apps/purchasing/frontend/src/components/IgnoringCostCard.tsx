import type { Analytics } from "../types";

function currency(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "$0";
}

interface IgnoringCostCardProps {
  analytics?: Analytics;
}

export default function IgnoringCostCard({ analytics }: IgnoringCostCardProps) {
  const cost = analytics?.wasteCostAnalysis;
  const counterfactual = analytics?.counterfactual;
  const waste = Number(cost?.totalWasteCostDollars ?? cost?.wasteCostDollars ?? 0);
  const stockout = Number(cost?.totalStockoutCostDollars ?? cost?.stockoutCostDollars ?? 0);
  const total = Number(cost?.totalCostDollars ?? waste + stockout);

  return (
    <section className="purchase-card ignoring-cost-card">
      <div>
        <p className="purchase-kicker">Cost analysis</p>
        <h2 className="purchase-title">Historical waste is the signal</h2>
        <p className="purchase-muted">
          Weather and events describe the day. The spend pattern comes from repeated waste and stockouts.
        </p>
      </div>
      <div className="cost-grid">
        <div>
          <span>Waste cost</span>
          <strong>{currency(waste)}</strong>
        </div>
        <div>
          <span>Stockout cost</span>
          <strong>{currency(stockout)}</strong>
        </div>
        <div>
          <span>Total leak</span>
          <strong>{currency(total)}</strong>
        </div>
        <div>
          <span>Recoverable</span>
          <strong>{currency(counterfactual?.dollarsSaved)}</strong>
        </div>
      </div>
      {counterfactual?.scenario && (
        <p className="purchase-muted">
          {counterfactual.scenario}: {counterfactual.ordersAdjusted ?? 0} orders adjusted.
        </p>
      )}
    </section>
  );
}
