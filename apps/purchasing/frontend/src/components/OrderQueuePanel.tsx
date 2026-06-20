import { useEffect, useMemo, useState } from "react";
import { getOrderQueue } from "../api";
import type { OrderQueueItem, OrderQueueResponse } from "../types";

function money(value?: number | null) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "n/a";
  }
  return `$${number.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function percent(value?: number | null) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "0%";
  }
  return `${Math.round(Math.max(0, Math.min(number, 1)) * 100)}%`;
}

function label(value?: string) {
  return String(value || "unknown").replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function priorityColor(value?: number) {
  const score = Number(value || 0);
  if (score > 0.7) return "#b91c1c";
  if (score >= 0.45) return "#b45309";
  return "#15803d";
}

function rowKey(item: OrderQueueItem, index: number) {
  return `${item.orderId ?? item.whatToOrder ?? "queue"}-${index}`;
}

export default function OrderQueuePanel() {
  const [queue, setQueue] = useState<OrderQueueResponse>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const nextQueue = await getOrderQueue();
        if (active) {
          setQueue(nextQueue);
        }
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load order queue");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  const items = useMemo(() => queue?.queue ?? [], [queue]);
  const highPriority = useMemo(
    () => items.filter((item) => Number(item.priorityScore || 0) > 0.7).length,
    [items],
  );

  if (loading) {
    return (
      <section className="purchase-card" data-testid="queue-loading">
        Loading order queue...
      </section>
    );
  }

  if (error) {
    return (
      <section className="purchase-card" data-testid="order-queue-panel">
        <p className="purchase-kicker">Order queue</p>
        <h2 className="purchase-title">Queue unavailable</h2>
        <p className="purchase-muted">{error}</p>
      </section>
    );
  }

  return (
    <section className="purchase-card order-queue-panel" data-testid="order-queue-panel">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Order queue</p>
          <h2 className="purchase-title">Prioritized supplier orders</h2>
        </div>
      </div>

      <div className="mini-metric-grid" data-testid="queue-summary">
        <div>
          <span>Pending orders</span>
          <strong>{queue?.count ?? items.length}</strong>
        </div>
        <div>
          <span>High priority</span>
          <strong>{highPriority}</strong>
        </div>
        <div>
          <span>Conservation</span>
          <strong>{String(queue?.conservationStatus?.status ?? "BOOTSTRAP")}</strong>
        </div>
      </div>

      <div data-testid="queue-table" style={{ display: "grid", gap: 10, marginTop: 16 }}>
        {items.length === 0 ? (
          <p className="purchase-muted">No pending orders in the queue.</p>
        ) : (
          items.map((item, index) => {
            const priority = Number(item.priorityScore || 0);
            return (
              <details
                key={rowKey(item, index)}
                data-testid="queue-item"
                style={{
                  border: "1px solid #e5e7eb",
                  borderLeft: `4px solid ${priorityColor(priority)}`,
                  borderRadius: 8,
                  padding: "10px 12px",
                }}
              >
                <summary
                  style={{
                    alignItems: "center",
                    cursor: "pointer",
                    display: "grid",
                    gap: 8,
                    gridTemplateColumns: "1fr 1fr 0.8fr 0.9fr 0.8fr 0.8fr",
                  }}
                >
                  <span>
                    <strong>{item.orderId ?? "Queued order"}</strong>
                    <br />
                    <small className="purchase-muted">{item.whatToOrder ?? "Mixed items"}</small>
                  </span>
                  <span>{item.supplierName ?? item.supplierId ?? "Unknown supplier"}</span>
                  <span>{label(item.category)}</span>
                  <span>{label(item.recommendedAction)}</span>
                  <span>{percent(item.confidence)}</span>
                  <span style={{ color: priorityColor(priority), fontWeight: 800 }}>
                    {percent(priority)}
                  </span>
                </summary>

                <div style={{ display: "grid", gap: 10, marginTop: 10 }}>
                  <div className="stats-row">
                    <div>
                      <span>Amount</span>
                      <strong>{money(item.totalAmount)}</strong>
                    </div>
                    <div>
                      <span>Stockout risk</span>
                      <strong>{percent(item.stockoutRisk)}</strong>
                    </div>
                    <div>
                      <span>Age</span>
                      <strong>{Number(item.agingDays ?? 0)}d</strong>
                    </div>
                  </div>
                  <div data-testid="queue-top-factors" style={{ display: "grid", gap: 6 }}>
                    {(item.topFactors ?? []).map((factor) => (
                      <div
                        key={factor.name}
                        style={{
                          alignItems: "center",
                          display: "grid",
                          gap: 8,
                          gridTemplateColumns: "1fr auto 1.2fr",
                        }}
                      >
                        <span>{label(factor.name)}</span>
                        <strong>{Number(factor.value).toFixed(2)}</strong>
                        <small className="purchase-muted">{factor.interpretation}</small>
                      </div>
                    ))}
                  </div>
                </div>
              </details>
            );
          })
        )}
      </div>
    </section>
  );
}
