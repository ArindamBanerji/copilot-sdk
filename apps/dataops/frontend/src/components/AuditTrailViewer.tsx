import { useEffect, useMemo, useState } from "react";
import { getAlerts, getAuditTrail } from "../api";
import type { AuditTrailResponse, AuditTrailStep, DataOpsAlert } from "../types";

const EXPECTED_STEPS = ["signal", "context", "enrichment", "score", "decision", "outcome"];

export default function AuditTrailViewer() {
  const [alerts, setAlerts] = useState<DataOpsAlert[]>([]);
  const [selectedAlertId, setSelectedAlertId] = useState("");
  const [trail, setTrail] = useState<AuditTrailResponse | null>(null);
  const [loadingAlerts, setLoadingAlerts] = useState(true);
  const [loadingTrail, setLoadingTrail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadingAlerts(true);
    getAlerts()
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setAlerts(payload);
        const firstAlertId = getAlertId(payload[0]);
        if (firstAlertId) {
          setSelectedAlertId(firstAlertId);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load alerts for audit trail.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingAlerts(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedAlertId) {
      setTrail(null);
      return;
    }

    let cancelled = false;
    setLoadingTrail(true);
    setError(null);
    getAuditTrail(selectedAlertId)
      .then((payload) => {
        if (!cancelled) {
          setTrail(payload);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setTrail(null);
          setError(caught instanceof Error ? caught.message : "Could not load audit trail.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingTrail(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [selectedAlertId]);

  const chain = trail?.chain || [];
  const presentSteps = useMemo(() => new Set(chain.map((step) => step.step).filter(Boolean)), [chain]);
  const missingSteps = EXPECTED_STEPS.filter((step) => !presentSteps.has(step));

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-16
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Audit Trail
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            Signal, context, enrichment, score, decision, and outcome for a selected alert.
          </p>
        </div>
        <span
          className="rounded-full px-2 py-1 text-xs font-semibold"
          style={{
            background: trail?.complete ? "rgba(34, 197, 94, 0.12)" : "var(--copilot-surface-muted)",
            color: trail?.complete ? "var(--copilot-success)" : "var(--copilot-text-muted)",
          }}
        >
          {trail?.complete ? "Complete chain" : "Incomplete chain"}
        </span>
      </div>

      <label className="mt-4 grid gap-1 text-xs font-semibold dataops-muted">
        Alert
        <select
          className="rounded-md border px-2 py-2 text-sm"
          style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }}
          value={selectedAlertId}
          onChange={(event) => setSelectedAlertId(event.target.value)}
          disabled={loadingAlerts || alerts.length === 0}
        >
          {alerts.length === 0 ? <option value="">No alerts available</option> : null}
          {alerts.map((alert) => {
            const alertId = getAlertId(alert);
            return (
              <option key={alertId} value={alertId}>
                {alertId} - {getAlertSystem(alert)} - {alert.category || "uncategorized"}
              </option>
            );
          })}
        </select>
      </label>

      {error ? <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}
      {loadingTrail ? <p className="mt-4 text-sm dataops-muted">Loading audit trail...</p> : null}
      {!loadingTrail && !error && chain.length === 0 ? (
        <p className="mt-4 text-sm dataops-muted">No audit trail available for this alert.</p>
      ) : null}

      {!loadingTrail && chain.length > 0 ? (
        <div className="mt-5 grid gap-3">
          {chain.map((step, index) => (
            <AuditStepCard key={`${step.step || "step"}-${index}`} step={step} index={index} />
          ))}
        </div>
      ) : null}

      {!loadingTrail && chain.length > 0 && !trail?.complete ? (
        <div className="mt-4 rounded-md border p-3 text-sm dataops-muted" style={{ borderColor: "var(--copilot-border)" }}>
          Pending steps: {missingSteps.map(humanize).join(", ") || "none"}. Untriaged alerts can have incomplete chains.
        </div>
      ) : null}
    </section>
  );
}

function AuditStepCard({ step, index }: { step: AuditTrailStep; index: number }) {
  const stepName = step.step || "step";
  const terminal = stepName === "outcome" || stepName === "decision";
  return (
    <article className="grid gap-3 rounded-md border p-4 sm:grid-cols-[3rem_minmax(0,1fr)]" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex sm:justify-center">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold"
          style={{
            background: terminal ? "var(--copilot-primary-light)" : "var(--copilot-surface-muted)",
            color: terminal ? "var(--copilot-primary)" : "var(--copilot-text-muted)",
          }}
        >
          {index + 1}
        </div>
      </div>
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
              {step.label || humanize(stepName)}
            </div>
            <p className="mt-1 text-sm dataops-muted">{step.detail || "No detail available."}</p>
          </div>
          <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
            {humanize(stepName)}
          </span>
        </div>
        <div className="mt-3 grid gap-2 text-xs dataops-muted sm:grid-cols-3">
          <span>Source: {step.source || "computed"}</span>
          <span>Timestamp: {step.timestamp || "n/a"}</span>
          <span>Signal: {step.variantId || step.action || step.actionTaken || "n/a"}</span>
        </div>
        {step.data ? (
          <pre className="mt-3 max-h-32 overflow-auto rounded-md p-3 text-xs" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
            {JSON.stringify(step.data, null, 2)}
          </pre>
        ) : null}
      </div>
    </article>
  );
}

function getAlertId(alert?: DataOpsAlert): string {
  return String(alert?.alertId || alert?.alert_id || alert?.eventId || alert?.event_id || "");
}

function getAlertSystem(alert: DataOpsAlert): string {
  return String(alert.systemName || alert.system_name || alert.system || "unknown system");
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
