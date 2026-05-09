import type { DataOpsAlert } from "../types";
import AlertCard from "./AlertCard";

interface AlertQueueProps {
  alerts: DataOpsAlert[];
  onAlertClick: (alertId: string) => void;
}

const severityRank: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

export default function AlertQueue({ alerts, onAlertClick }: AlertQueueProps) {
  const unresolved = alerts
    .filter((alert) => !isAutoResolved(alert))
    .sort((a, b) => rank(b) - rank(a));
  const autoResolved = alerts
    .filter(isAutoResolved)
    .sort((a, b) => rank(b) - rank(a));

  return (
    <section className="copilot-card overflow-hidden">
      <div className="flex items-center justify-between border-b px-4 py-3" style={{ borderColor: "var(--copilot-border)" }}>
        <h2 className="dataops-section-title">Alert Queue</h2>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
          {alerts.length}
        </span>
      </div>
      <div className="max-h-[42rem] overflow-y-auto p-3">
        {unresolved.length === 0 && autoResolved.length === 0 ? (
          <div className="p-4 text-sm dataops-muted">No alerts available.</div>
        ) : null}
        <div className="grid gap-3">
          {unresolved.map((alert) => (
            <AlertCard key={alert.alertId} alert={alert} onClick={() => onAlertClick(alert.alertId)} />
          ))}
        </div>
        {autoResolved.length > 0 ? (
          <div className="mt-5">
            <div className="mb-3 border-t pt-3 text-xs font-semibold uppercase dataops-muted" style={{ borderColor: "var(--copilot-border)" }}>
              Auto-resolved
            </div>
            <div className="grid gap-3 opacity-80">
              {autoResolved.map((alert) => (
                <AlertCard key={alert.alertId} alert={alert} onClick={() => onAlertClick(alert.alertId)} />
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function isAutoResolved(alert: DataOpsAlert): boolean {
  const raw = alert as DataOpsAlert & {
    auto_resolved?: boolean;
    resolved?: boolean;
  };
  const status = String(alert.status || "").toLowerCase();

  if (status === "active") {
    return false;
  }

  // actionTaken=auto_approve can be the suggested or chosen action; only backend resolved/autoResolved flags indicate completed auto-resolution.
  if (alert.autoResolved === true || raw.auto_resolved === true) {
    return true;
  }

  if (raw.resolved === true) {
    return true;
  }

  return ["resolved", "auto_resolved", "auto-resolved", "monitoring", "managed"].includes(status);
}

function rank(alert: DataOpsAlert): number {
  return severityRank[String(alert.severity || "").toLowerCase()] || 0;
}
