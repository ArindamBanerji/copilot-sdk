import type { Analytics } from "../types";

interface WasteCostCardProps {
  analytics?: Analytics;
}

function money(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "n/a";
}

export default function WasteCostCard({ analytics }: WasteCostCardProps) {
  const waste = analytics?.wasteCostAnalysis;
  const categories = analytics?.categoryAccuracy ?? {};
  const days = analytics?.dayOfWeek ?? {};
  const stockout = Number(waste?.totalStockoutCostDollars ?? 0);
  const wasteCost = Number(waste?.totalWasteCostDollars ?? 0);
  const worstCategory = Object.entries(categories).sort(
    (left, right) => Number(right[1].totalCostDollars ?? 0) - Number(left[1].totalCostDollars ?? 0),
  )[0]?.[0];
  const worstDay = Object.entries(days).sort(
    (left, right) => Number(right[1].totalCostDollars ?? 0) - Number(left[1].totalCostDollars ?? 0),
  )[0]?.[0];

  return (
    <section className="purchase-card waste-cost-card">
      <p className="purchase-kicker">Waste cost</p>
      <h2 className="purchase-title">The cost leak is concentrated</h2>
      <div className="stats-row">
        <div><span>Total waste 30d</span><strong>{money(wasteCost)}</strong></div>
        <div><span>Total stockout 30d</span><strong>{money(stockout)}</strong></div>
        <div><span>Waste / stockout</span><strong>{stockout > 0 ? `${(wasteCost / stockout).toFixed(1)}x` : "n/a"}</strong></div>
        <div><span>Worst category</span><strong>{worstCategory?.replace("_", " ") ?? "n/a"}</strong></div>
        <div><span>Worst day</span><strong>{worstDay ?? "n/a"}</strong></div>
      </div>
      <p className="purchase-muted">
        Worst order: {String(waste?.highestWasteOrder?.item ?? "n/a")} at {money(Number(waste?.highestWasteOrder?.wasteCostDollars ?? 0))}.
      </p>
    </section>
  );
}
