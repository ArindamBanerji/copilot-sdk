import type { DataOpsAlert } from "../types";
import AERecommendationBadge from "./AERecommendationBadge";
import RecurrenceBadge from "./RecurrenceBadge";

interface AlertCardProps {
  alert: DataOpsAlert;
  onClick: () => void;
}

const severityColor: Record<string, string> = {
  critical: "var(--copilot-danger)",
  high: "var(--copilot-danger)",
  medium: "var(--copilot-warning)",
  low: "var(--copilot-success)",
};

export default function AlertCard({ alert, onClick }: AlertCardProps) {
  const color = severityColor[String(alert.severity || "").toLowerCase()] || "var(--copilot-text-muted)";

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-md border p-3 text-left transition hover:shadow-sm"
      style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
    >
      <div className="mb-2 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
              {alert.alertId}
            </span>
            <span className="rounded px-2 py-0.5 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color }}>
              {alert.severity || "unknown"}
            </span>
          </div>
          <div className="mt-1 truncate text-sm dataops-muted">{alert.dataset || "unknown dataset"}</div>
        </div>
        <RecurrenceBadge count={alert.recurrenceCount} />
      </div>
      <div className="grid gap-1 text-xs dataops-muted">
        <div>{alert.system || "unknown system"}</div>
        <div>{formatCategory(alert.category)}</div>
      </div>
      {alert.actionTaken === "auto_approve" ? (
        <div className="mt-3">
          <AERecommendationBadge action="Auto approve" variantId="fixture-history" confidence={alert.isCorrect ? 0.82 : 0.48} />
        </div>
      ) : null}
    </button>
  );
}

function formatCategory(value?: string): string {
  return value ? value.replace(/_/g, " ") : "uncategorized";
}
