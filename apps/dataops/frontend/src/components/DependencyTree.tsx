import type { BlastRadius, DependencyNode } from "../types";

interface DependencyTreeProps {
  deps: BlastRadius | null;
}

export default function DependencyTree({ deps }: DependencyTreeProps) {
  const tree = deps?.downstreamTree || deps?.tree;

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="dataops-section-title">Dependency Tree</h2>
          <p className="text-sm dataops-muted">Blast radius from the affected pipeline graph.</p>
        </div>
        <div className="grid gap-1 text-right text-xs">
          <Metric label="Affected" value={formatNumber(deps?.totalAffected)} />
          <Metric label="Max criticality" value={formatPercent(deps?.maxCriticality)} />
          <Metric label="Min SLA" value={formatMinutes(deps?.minSla)} />
        </div>
      </div>

      {tree ? (
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <TreeNode node={tree} />
        </div>
      ) : (
        <div className="rounded-md p-4 text-sm dataops-muted" style={{ background: "var(--copilot-surface-muted)" }}>
          No dependency tree available.
        </div>
      )}
    </section>
  );
}

function TreeNode({ node }: { node: DependencyNode }) {
  const children = node.children || [];
  const name = node.displayName || node.name || node.system || "unknown system";

  return (
    <div>
      <div className="flex items-center justify-between gap-3 rounded-md px-2 py-2" style={{ background: "var(--copilot-surface-muted)" }}>
        <div>
          <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{name}</div>
          <div className="text-xs dataops-muted">Depth {node.depth ?? 0}</div>
        </div>
        <div className="flex gap-3 text-xs">
          {typeof node.slaMinutes === "number" ? <Metric label="SLA" value={formatMinutes(node.slaMinutes)} /> : null}
          {typeof node.businessCriticality === "number" ? <Metric label="Criticality" value={formatPercent(node.businessCriticality)} /> : null}
        </div>
      </div>
      {children.length > 0 ? (
        <div className="ml-4 mt-2 grid gap-2 border-l pl-3" style={{ borderColor: "var(--copilot-border)" }}>
          {children.map((child, index) => (
            <TreeNode key={`${child.system || child.name || "node"}-${index}`} node={child} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="dataops-muted">{label}</div>
      <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</div>
    </div>
  );
}

function formatNumber(value?: number): string {
  return Number.isFinite(value) ? String(value) : "0";
}

function formatPercent(value?: number): string {
  return Number.isFinite(value) ? `${Math.round(Number(value) * 100)}%` : "0%";
}

function formatMinutes(value?: number): string {
  return Number.isFinite(value) ? `${Number(value)}m` : "--";
}
