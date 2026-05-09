import type { SimilarOrder } from "../types";

interface SimilarOrdersPanelProps {
  orders: SimilarOrder[];
  count: number;
}

function pct(value?: number) {
  return Number.isFinite(value) ? `${(Number(value) * 100).toFixed(0)}%` : "n/a";
}

export default function SimilarOrdersPanel({ orders, count }: SimilarOrdersPanelProps) {
  return (
    <section className="purchase-card similar-orders">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Similar orders</p>
          <h2 className="purchase-title">Prior decisions before confirmation</h2>
        </div>
        <span className="purchase-pill">{count} matches</span>
      </div>
      {orders.length === 0 ? (
        <p className="purchase-muted">No close historical matches met the similarity threshold.</p>
      ) : (
        <div className="similar-list">
          {orders.map((order) => (
            <article key={order.orderId ?? `${order.item}-${order.similarity}`} className="similar-row">
              <div>
                <strong>{order.item ?? "Unknown item"}</strong>
                <span>{order.category ?? "category n/a"} | {order.dayOfWeek ?? "day n/a"}</span>
              </div>
              <div>
                <span>Event</span>
                <strong>{order.isEventDay ? "Yes" : "No"}</strong>
              </div>
              <div>
                <span>Quantity</span>
                <strong>{order.quantityLbs ?? "n/a"}</strong>
              </div>
              <div>
                <span>Waste</span>
                <strong>{pct(order.wastePct)}</strong>
              </div>
              <div>
                <span>Stockout</span>
                <strong>{order.stockoutOccurred ? "Yes" : "No"}</strong>
              </div>
              <div>
                <span>Correct</span>
                <strong>{order.isCorrect ? "Yes" : "No"}</strong>
              </div>
              <div>
                <span>Similarity</span>
                <strong>{pct(order.similarity)}</strong>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
