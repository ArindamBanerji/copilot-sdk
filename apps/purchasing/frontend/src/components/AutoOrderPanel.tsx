import { useEffect, useMemo, useState } from "react";
import {
  disableAutoOrder,
  enableAutoOrder,
  getAutoOrderAudit,
  getAutoOrderStatus,
} from "../api";
import type { AutoOrderAuditEvent, AutoOrderStatus } from "../types";

function percent(value?: number | null) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "0%";
  }
  return `${Math.round(Math.max(0, Math.min(number, 1)) * 100)}%`;
}

function label(value?: string | null) {
  return String(value || "unknown").replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function statusColor(enabled?: boolean) {
  return enabled ? "#15803d" : "#64748b";
}

export default function AutoOrderPanel() {
  const [status, setStatus] = useState<AutoOrderStatus>();
  const [audit, setAudit] = useState<AutoOrderAuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();

  async function load() {
    setError(undefined);
    const [nextStatus, nextAudit] = await Promise.all([
      getAutoOrderStatus(),
      getAutoOrderAudit(),
    ]);
    setStatus(nextStatus);
    setAudit(nextAudit);
  }

  useEffect(() => {
    let active = true;
    async function run() {
      setLoading(true);
      try {
        const [nextStatus, nextAudit] = await Promise.all([
          getAutoOrderStatus(),
          getAutoOrderAudit(),
        ]);
        if (active) {
          setStatus(nextStatus);
          setAudit(nextAudit);
        }
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unable to load auto-ordering status");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }
    run();
    return () => {
      active = false;
    };
  }, []);

  async function toggle() {
    setBusy(true);
    setError(undefined);
    try {
      const next = status?.enabled ? await disableAutoOrder() : await enableAutoOrder();
      setStatus(next);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update auto-ordering");
    } finally {
      setBusy(false);
    }
  }

  const recent = useMemo(() => audit.slice(-10).reverse(), [audit]);
  const enabled = Boolean(status?.enabled);
  const color = statusColor(enabled);

  if (loading) {
    return (
      <section className="purchase-card" data-testid="auto-order-status">
        Loading auto-ordering controls...
      </section>
    );
  }

  return (
    <section className="purchase-card auto-order-panel">
      <div className="purchase-card-header" style={{ alignItems: "flex-start", gap: 16 }}>
        <div>
          <p className="purchase-kicker">Auto-order</p>
          <h2 className="purchase-title">Conservation-gated auto-ordering</h2>
          <p className="purchase-muted">Requires GREEN conservation before the gate can turn on.</p>
        </div>
        <span
          data-testid="auto-order-status"
          style={{
            alignItems: "center",
            border: `1px solid ${color}`,
            borderRadius: 999,
            color,
            display: "inline-flex",
            fontWeight: 800,
            gap: 8,
            padding: "6px 10px",
            whiteSpace: "nowrap",
          }}
        >
          <span
            aria-hidden="true"
            style={{ background: color, borderRadius: 999, display: "inline-block", height: 8, width: 8 }}
          />
          {enabled ? "Auto-ordering enabled" : "Auto-ordering disabled"}
        </span>
      </div>

      {error ? <p className="purchase-muted">{error}</p> : null}

      <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: 10, marginTop: 12 }}>
        <button
          className="purchase-button"
          data-testid="auto-order-toggle"
          type="button"
          disabled={busy}
          onClick={toggle}
        >
          {enabled ? "Disable auto-ordering" : "Enable auto-ordering"}
        </button>
        <span className="purchase-muted">
          Conservation {status?.conservationStatus ?? "RED"} · {status?.verifiedCount ?? 0} verified decisions
        </span>
        {status?.reason === "conservation_not_green" ? (
          <span className="purchase-muted">GREEN conservation required before enabling.</span>
        ) : null}
      </div>

      <div className="mini-metric-grid" data-testid="auto-order-stats" style={{ marginTop: 16 }}>
        <div>
          <span>Threshold</span>
          <strong>{percent(status?.threshold)}</strong>
        </div>
        <div>
          <span>Auto-ordered</span>
          <strong>{status?.autoOrderedCount ?? 0}</strong>
        </div>
        <div>
          <span>Spot checks</span>
          <strong>{status?.spotCheckCount ?? 0}</strong>
        </div>
        <div>
          <span>Error rate</span>
          <strong>{percent(status?.errorRate)}</strong>
        </div>
      </div>

      <div data-testid="auto-order-history" style={{ display: "grid", gap: 8, marginTop: 16 }}>
        <div className="purchase-card-header">
          <strong>Recent auto-orders</strong>
          <span className="purchase-muted">Last 10</span>
        </div>
        {recent.length === 0 ? (
          <p className="purchase-muted">No auto-ordered entries yet.</p>
        ) : (
          recent.map((event) => (
            <div
              key={event.eventId ?? `${event.orderId}-${event.createdAt}`}
              style={{
                border: "1px solid #e5e7eb",
                borderRadius: 8,
                display: "grid",
                gap: 8,
                gridTemplateColumns: "1fr 0.8fr 0.8fr 0.8fr 0.7fr",
                padding: "8px 10px",
              }}
            >
              <span>{event.orderId ?? event.decisionId ?? "Auto-order check"}</span>
              <span>{label(event.category)}</span>
              <span>{label(event.action)}</span>
              <span>{percent(event.confidence)}</span>
              <span>{event.spotCheck ? "Spot check" : event.autoOrder ? "Auto-ordered" : label(event.reason)}</span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
