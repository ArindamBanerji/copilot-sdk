import type { SimilarAlert } from "../types";

interface SimilarAlertsPanelProps {
  alerts: SimilarAlert[];
  loading: boolean;
}

export default function SimilarAlertsPanel({ alerts, loading }: SimilarAlertsPanelProps) {
  if (loading) {
    return (
      <section className="copilot-card p-4 text-sm dataops-muted">
        Finding similar alerts...
      </section>
    );
  }

  const summary = buildActionSummary(alerts);

  return (
    <section className="copilot-card p-4">
      <div className="mb-4">
        <h2 className="dataops-section-title">Similar Alerts</h2>
        <p className="text-sm dataops-muted">Past decisions with a close factor profile.</p>
      </div>

      {alerts.length === 0 ? (
        <div className="rounded-md p-3 text-sm dataops-muted" style={{ background: "var(--copilot-surface-muted)" }}>
          No similar alerts found in history.
        </div>
      ) : (
        <div className="grid gap-2">
          {summary ? (
            <div className="rounded-md p-3 text-sm font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
              {summary}
            </div>
          ) : null}

          {alerts.map((alert, index) => (
            <div
              key={`${alert.eventId || "similar"}-${index}`}
              className="rounded-md border p-3 text-sm"
              style={{ borderColor: "var(--copilot-border)" }}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>
                    {alert.eventId || "unknown event"} · {formatAction(alert.actionTaken)}
                  </div>
                  <div className="mt-1 text-xs dataops-muted">
                    {alert.dataset || "unknown dataset"} · {formatCategory(alert.category)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold" style={{ color: alert.isCorrect ? "var(--copilot-success)" : "var(--copilot-danger)" }}>
                    {alert.isCorrect ? "✓" : "✗"}
                  </div>
                  <div className="text-xs dataops-muted">{formatSimilarity(alert.similarity)} match</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function buildActionSummary(alerts: SimilarAlert[]): string | null {
  const counts = new Map<string, { wins: number; total: number }>();
  for (const alert of alerts) {
    const action = alert.actionTaken || "unknown";
    const current = counts.get(action) || { wins: 0, total: 0 };
    current.total += 1;
    if (alert.isCorrect) {
      current.wins += 1;
    }
    counts.set(action, current);
  }

  let best: { action: string; wins: number; total: number } | null = null;
  for (const [action, value] of counts.entries()) {
    if (!best || value.wins / value.total > best.wins / best.total || (value.wins === best.wins && value.total > best.total)) {
      best = { action, ...value };
    }
  }

  if (!best || best.total === 0) {
    return null;
  }
  return `${formatAction(best.action)} worked ${best.wins}/${best.total} times for this profile.`;
}

function formatSimilarity(value?: number): string {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "--";
}

function formatAction(value?: string): string {
  return value ? value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) : "Unknown action";
}

function formatCategory(value?: string): string {
  return value ? value.replace(/_/g, " ") : "uncategorized";
}
