import type { Item } from "../types";

interface CostAnalysisProps {
  item?: Item;
  quantity: number;
  historicalWaste: number;
}

function money(value: number) {
  return `$${Number.isFinite(value) ? value.toFixed(0) : "0"}`;
}

export default function CostAnalysis({ item, quantity, historicalWaste }: CostAnalysisProps) {
  const unitPrice = Number(item?.unitPrice ?? 0);
  const safeQuantity = Number.isFinite(quantity) ? quantity : 0;
  const orderCost = unitPrice * safeQuantity;
  const stockoutEstimate = unitPrice * safeQuantity * 20;
  const wasteEstimate = unitPrice * safeQuantity * historicalWaste;
  const riskRatio = wasteEstimate > 0 ? stockoutEstimate / wasteEstimate : null;

  return (
    <section className="purchase-card cost-analysis-card">
      <p className="purchase-kicker">Cost analysis</p>
      <h2 className="purchase-title">Stockout costs far more than waste</h2>
      <p className="purchase-muted">
        The math is guarded against zero waste; the decision still shows the service-risk spread.
      </p>
      <div className="mini-metric-grid">
        <div>
          <span>Order cost</span>
          <strong>{money(orderCost)}</strong>
        </div>
        <div>
          <span>Stockout estimate</span>
          <strong>{money(stockoutEstimate)}</strong>
        </div>
        <div>
          <span>Waste estimate</span>
          <strong>{money(wasteEstimate)}</strong>
        </div>
        <div>
          <span>Risk ratio</span>
          <strong>{riskRatio ? `${riskRatio.toFixed(1)}x` : "n/a"}</strong>
        </div>
      </div>
    </section>
  );
}
