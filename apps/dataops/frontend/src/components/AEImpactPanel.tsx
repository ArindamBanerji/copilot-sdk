import type { AEImpact } from "../types";

interface AEImpactPanelProps {
  impact: AEImpact | null;
  compact?: boolean;
}

export default function AEImpactPanel({ impact, compact = false }: AEImpactPanelProps) {
  const hoursSaved = Object.values(impact?.breakdown || {}).reduce(
    (total, entry) => total + (Number(entry?.estimatedHoursSaved) || 0),
    0,
  );

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="dataops-section-title">AgentEvolver Impact</h2>
          <p className="text-sm dataops-muted">Autonomous rules currently shaping alert handling.</p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
          AE
        </span>
      </div>

      <div className={`grid gap-3 ${compact ? "" : "md:grid-cols-3"}`}>
        <Metric label="Auto-resolved" value={formatNumber(impact?.autoResolvedCount)} />
        <Metric label="Accuracy" value={formatPercent(impact?.accuracy)} />
        <Metric label="Hours saved" value={hoursSaved.toFixed(1)} />
      </div>

      {!compact ? (
        <div className="mt-4 grid gap-4">
          <div className="grid gap-3 md:grid-cols-2">
            <RuleList title="Active rules" rules={impact?.activeRules || []} tone="active" />
            <RuleList title="Rejected rules" rules={impact?.rejectedRules || []} tone="rejected" />
          </div>
          <div className="grid gap-2">
            {Object.entries(impact?.breakdown || {}).map(([key, entry]) => (
              <div key={key} className="rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>{formatLabel(key)}</div>
                <div className="mt-1 text-xs dataops-muted">
                  {formatNumber(entry.alertsPrevented)} alerts prevented · {formatNumber(entry.estimatedHoursSaved)} hours saved
                </div>
              </div>
            ))}
          </div>
          {impact?.rejectedExample?.reason ? (
            <div className="rounded-md p-3 text-sm" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-danger)" }}>
              {impact.rejectedExample.variantId ? `${impact.rejectedExample.variantId}: ` : ""}
              {impact.rejectedExample.reason}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs dataops-muted">{label}</div>
      <div className="text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value}
      </div>
    </div>
  );
}

function formatNumber(value?: number): string {
  return Number.isFinite(value) ? String(value) : "0";
}

function formatPercent(value?: number): string {
  return Number.isFinite(value) ? `${Math.round(Number(value) * 100)}%` : "0%";
}

function RuleList({ title, rules, tone }: { title: string; rules: string[]; tone: "active" | "rejected" }) {
  return (
    <div>
      <div className="mb-2 text-xs font-semibold uppercase dataops-muted">{title}</div>
      <div className="grid gap-2">
        {rules.length === 0 ? (
          <div className="rounded-md border px-3 py-2 text-sm dataops-muted" style={{ borderColor: "var(--copilot-border)" }}>
            None
          </div>
        ) : (
          rules.map((rule) => (
            <div
              key={rule}
              className="rounded-md border px-3 py-2 text-sm font-semibold"
              style={{
                borderColor: tone === "active" ? "var(--copilot-success)" : "var(--copilot-danger)",
                color: "var(--copilot-text)",
              }}
            >
              {rule}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
}
