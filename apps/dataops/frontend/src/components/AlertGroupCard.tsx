import { useState } from "react";
import type { AlertGroup, AlertGroupAlert } from "../types";

interface AlertGroupCardProps {
  group: AlertGroup;
  defaultExpanded?: boolean;
  onSelectAlert: (alertId: string) => void;
}

export default function AlertGroupCard({ group, defaultExpanded = false, onSelectAlert }: AlertGroupCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const alerts = group.alerts || [];
  const rootSystem = group.rootSystem || group.root_system || "unknown_root";
  const rootDisplay = group.rootDisplay || group.root_display || rootSystem;
  const cascadingSystems = group.cascadingSystems || group.cascading_systems || [];
  const alertCount = numberOr(group.alertCount ?? group.alert_count, alerts.length);
  const summary = summarizeSeverity(alerts);
  const tone = severityTone(alerts);

  return (
    <section className="copilot-card overflow-hidden">
      <button
        type="button"
        className="flex w-full items-start justify-between gap-4 border-b px-4 py-3 text-left"
        style={{ borderColor: "var(--copilot-border)", borderLeft: `4px solid ${tone}` }}
        onClick={() => setExpanded((current) => !current)}
      >
        <div className="min-w-0">
          <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            {rootDisplay}
          </div>
          <div className="mt-1 truncate text-xs dataops-muted">{rootSystem}</div>
          <div className="mt-2 text-xs dataops-muted">{summary}</div>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span
            className="rounded-full px-2 py-1 text-xs font-semibold"
            style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text)" }}
          >
            {alertCount} alerts
          </span>
          <span className="text-sm font-semibold" style={{ color: "var(--copilot-primary)" }}>
            {expanded ? "Collapse" : "Expand"}
          </span>
        </div>
      </button>

      {expanded ? (
        <div className="grid gap-3 p-3">
          {cascadingSystems.length > 0 ? (
            <div className="rounded-md p-3 text-xs dataops-muted" style={{ background: "var(--copilot-surface-muted)" }}>
              Cascading systems: {cascadingSystems.join(", ")}
            </div>
          ) : (
            <div className="rounded-md p-3 text-xs dataops-muted" style={{ background: "var(--copilot-surface-muted)" }}>
              Root-system alerts only.
            </div>
          )}

          {alerts.length > 0 ? (
            alerts.map((alert, index) => (
              <AlertRow
                key={`${alertId(alert) || "alert"}-${index}`}
                alert={alert}
                onSelectAlert={onSelectAlert}
              />
            ))
          ) : (
            <div className="rounded-md p-3 text-sm dataops-muted" style={{ background: "var(--copilot-surface-muted)" }}>
              No alerts in this root-cause group.
            </div>
          )}
        </div>
      ) : null}
    </section>
  );
}

function AlertRow({ alert, onSelectAlert }: { alert: AlertGroupAlert; onSelectAlert: (alertId: string) => void }) {
  const id = alertId(alert);
  const system = alert.systemName || alert.system_name || "unknown system";
  const severity = alert.severity || "unknown";

  return (
    <div className="rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>{id || "unknown alert"}</div>
          <div className="mt-1 text-xs dataops-muted">
            {system} · {formatCategory(alert.category)} · {severity}
          </div>
        </div>
        <button
          type="button"
          className="copilot-button-secondary px-3 py-2 text-xs"
          disabled={!id}
          onClick={() => {
            if (id) {
              onSelectAlert(id);
            }
          }}
        >
          Triage
        </button>
      </div>
    </div>
  );
}

function summarizeSeverity(alerts: AlertGroupAlert[]): string {
  const highRisk = alerts.filter((alert) => isCriticalOrHigh(alert.severity)).length;
  const medium = alerts.filter((alert) => String(alert.severity || "").toLowerCase() === "medium").length;
  if (highRisk > 0) {
    return `${highRisk} critical/high alerts`;
  }
  if (medium > 0) {
    return `${medium} medium alerts`;
  }
  return "No high-severity alerts";
}

function severityTone(alerts: AlertGroupAlert[]): string {
  if (alerts.some((alert) => isCriticalOrHigh(alert.severity))) {
    return "var(--copilot-danger)";
  }
  if (alerts.some((alert) => String(alert.severity || "").toLowerCase() === "medium")) {
    return "var(--copilot-warning)";
  }
  return "var(--copilot-success)";
}

function isCriticalOrHigh(severity?: string): boolean {
  const normalized = String(severity || "").toLowerCase();
  return normalized === "critical" || normalized === "high";
}

function alertId(alert: AlertGroupAlert): string {
  return alert.alertId || alert.alert_id || "";
}

function numberOr(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function formatCategory(value?: string): string {
  return value ? value.replace(/_/g, " ") : "uncategorized";
}
