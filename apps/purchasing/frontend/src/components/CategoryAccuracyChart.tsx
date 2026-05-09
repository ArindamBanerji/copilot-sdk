import type { Analytics } from "../types";

interface CategoryAccuracyChartProps {
  analytics?: Analytics;
}

const categories = ["protein", "produce", "dairy", "dry_goods", "beverages"];

export default function CategoryAccuracyChart({ analytics }: CategoryAccuracyChartProps) {
  const data = analytics?.categoryAccuracy ?? {};
  return (
    <section className="purchase-card">
      <p className="purchase-kicker">Category accuracy</p>
      <h2 className="purchase-title">Where ordering is consistent</h2>
      <div className="bar-list">
        {categories.map((category) => {
          const metric = data[category];
          const accuracy = Number(metric?.accuracy ?? 0);
          return (
            <div className="bar-row" key={category}>
              <span>{category.replace("_", " ")}</span>
              <div className="factor-track"><span style={{ width: `${Math.max(accuracy * 100, 2)}%` }} /></div>
              <strong>{(accuracy * 100).toFixed(0)}%</strong>
              <small>{metric?.count ?? 0} orders</small>
            </div>
          );
        })}
      </div>
    </section>
  );
}
