import type { PipelineSystem } from "../types";

interface PipelineGridProps {
  pipelines: PipelineSystem[];
}

const statusLabels: Record<string, { icon: string; color: string; label: string }> = {
  healthy: { icon: "OK", color: "var(--copilot-success)", label: "Healthy" },
  active: { icon: "OK", color: "var(--copilot-success)", label: "Active" },
  warning: { icon: "!", color: "var(--copilot-warning)", label: "Warning" },
  degraded: { icon: "!!", color: "var(--copilot-danger)", label: "Critical" },
  critical: { icon: "!!", color: "var(--copilot-danger)", label: "Critical" },
};

export default function PipelineGrid({ pipelines }: PipelineGridProps) {
  if (pipelines.length === 0) {
    return (
      <div className="copilot-card p-6 text-sm" style={{ color: "var(--copilot-text-muted)" }}>
        No pipeline systems available.
      </div>
    );
  }

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {pipelines.map((pipeline) => {
        const status = statusLabels[String(pipeline.status || "healthy")] || statusLabels.healthy;
        return (
          <article key={pipeline.name} className="copilot-card p-4">
            <div className="mb-3 flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
                  {pipeline.displayName || pipeline.name}
                </h3>
                <div className="mt-1 text-xs dataops-muted">{pipeline.owner || "unassigned"}</div>
              </div>
              <span
                className="rounded px-2 py-1 text-xs font-semibold"
                style={{ background: "var(--copilot-surface-muted)", color: status.color }}
                title={status.label}
              >
                {status.icon}
              </span>
            </div>
            <div className="grid gap-2 text-xs">
              <Metric label="Active alerts" value={formatNumber(pipeline.activeAlertCount)} />
              <Metric label="Business criticality" value={formatPercent(pipeline.businessCriticality)} />
              <Metric label="Downstream" value={formatNumber(pipeline.downstreamCount)} />
            </div>
          </article>
        );
      })}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="dataops-muted">{label}</span>
      <span className="font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value}
      </span>
    </div>
  );
}

function formatNumber(value?: number): string {
  return Number.isFinite(value) ? String(value) : "0";
}

function formatPercent(value?: number): string {
  return Number.isFinite(value) ? `${Math.round(Number(value) * 100)}%` : "0%";
}
