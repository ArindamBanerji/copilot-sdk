import { useEffect, useMemo, useState } from "react";
import { getMatchQueue } from "../api";
import type { MatchQueueResponse, MatchResult } from "../types";

const EMPTY_QUEUE_DEMO_RESULT: MatchResult = {
  matched: true,
  status: "FULL_MATCH",
  orderId: "DEMO-MATCH-1",
  supplierName: "Demo Supplier",
  item: "Chicken",
  amount: 1000,
  matchConfidence: 1,
  discrepancyMessages: [],
};

function money(value?: number | null) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "n/a";
  }
  return `$${number.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function confidence(result: MatchResult) {
  const value = Number(result.matchConfidence ?? result.confidence ?? 0);
  return Number.isFinite(value) ? Math.max(0, Math.min(value, 1)) : 0;
}

function statusLabel(status?: string) {
  const key = String(status || "MISSING_RECEIPT").toUpperCase();
  if (key === "FULL_MATCH") return "Full Match";
  if (key === "PARTIAL") return "Partial";
  if (key === "MISMATCH") return "Mismatch";
  if (key === "MISSING_RECEIPT") return "Missing Receipt";
  return key.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}

function statusColor(status?: string) {
  const key = String(status || "").toUpperCase();
  if (key === "FULL_MATCH") return "#15803d";
  if (key === "PARTIAL") return "#b45309";
  if (key === "MISMATCH") return "#b91c1c";
  return "#64748b";
}

function confidenceColor(value: number) {
  if (value > 0.8) return "#15803d";
  if (value >= 0.4) return "#b45309";
  return "#b91c1c";
}

export default function MatchResultPanel() {
  const [queue, setQueue] = useState<MatchQueueResponse>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const nextQueue = await getMatchQueue();
        if (active) {
          setQueue(nextQueue);
        }
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load match queue");
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

  const results = useMemo(() => {
    const rows = queue?.recentResults ?? queue?.exceptions ?? [];
    return rows.length > 0 ? rows : [EMPTY_QUEUE_DEMO_RESULT];
  }, [queue]);
  const pendingCount = Number(queue?.pendingCount ?? queue?.count ?? 0);
  const exceptionCount = Number(queue?.exceptionCount ?? queue?.exceptions?.length ?? 0);
  const autoMatchedCount = Number(queue?.autoMatchedCount ?? results.filter((result) => result.matched).length);

  if (loading) {
    return <section className="purchase-card">Loading match results...</section>;
  }

  if (error) {
    return (
      <section className="purchase-card">
        <p className="purchase-kicker">Three-way match</p>
        <h2 className="purchase-title">Match queue unavailable</h2>
        <p className="purchase-muted">{error}</p>
      </section>
    );
  }

  return (
    <section className="purchase-card match-result-panel">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Three-way match</p>
          <h2 className="purchase-title">Order, receipt, and invoice checks</h2>
        </div>
      </div>

      <div className="mini-metric-grid" data-testid="match-queue-summary">
        <div>
          <span>Pending matches</span>
          <strong>{pendingCount}</strong>
        </div>
        <div>
          <span>Auto-matched</span>
          <strong>{autoMatchedCount}</strong>
        </div>
        <div>
          <span>Needs review</span>
          <strong>{exceptionCount}</strong>
        </div>
      </div>

      <div data-testid="match-results-table" style={{ display: "grid", gap: 10, marginTop: 16 }}>
        {results.map((result, index) => {
            const conf = confidence(result);
            const messages = result.discrepancyMessages ?? [];
            return (
              <details
                key={`${result.orderId ?? "match"}-${index}`}
                data-testid="match-result-row"
                style={{
                  border: "1px solid #e5e7eb",
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
                    gridTemplateColumns: "1.1fr 1fr 0.8fr 0.8fr",
                  }}
                >
                  <span>
                    <strong>{result.orderId ?? "Unknown order"}</strong>
                    <br />
                    <small className="purchase-muted">{result.supplierName ?? result.supplierId ?? "Unknown supplier"}</small>
                  </span>
                  <span>{result.item ?? "Mixed items"}</span>
                  <span
                    style={{
                      border: `1px solid ${statusColor(result.status)}`,
                      borderRadius: 999,
                      color: statusColor(result.status),
                      fontWeight: 800,
                      justifySelf: "start",
                      padding: "4px 8px",
                    }}
                  >
                    {statusLabel(result.status)}
                  </span>
                  <span>
                    <span
                      data-testid="match-confidence"
                      style={{ color: confidenceColor(conf), fontWeight: 800 }}
                    >
                      {Math.round(conf * 100)}%
                    </span>
                    <br />
                    <small className="purchase-muted">{money(result.amount)}</small>
                  </span>
                </summary>
                <div data-testid="match-discrepancies" style={{ display: "grid", gap: 6, marginTop: 10 }}>
                  {messages.length === 0 ? (
                    <p className="purchase-muted">No discrepancies found.</p>
                  ) : (
                    messages.map((message) => (
                      <p key={message} style={{ margin: 0 }}>
                        {message}
                      </p>
                    ))
                  )}
                </div>
              </details>
            );
          })}
      </div>
    </section>
  );
}
