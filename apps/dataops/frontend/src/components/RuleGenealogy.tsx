import type { RuleGenealogyData } from "../types";

interface RuleGenealogyProps {
  genealogy?: RuleGenealogyData | null;
}

const colors: Record<string, string> = {
  soc: "#2563eb",
  s2p: "#059669",
  dataops: "#7c3aed",
};

export default function RuleGenealogy({ genealogy }: RuleGenealogyProps) {
  const stages = genealogy?.stages || [];

  if (stages.length === 0) {
    return (
      <section className="copilot-card p-5">
        <h2 className="dataops-section-title">Rule Genealogy</h2>
        <p className="mt-2 text-sm dataops-muted">No rule genealogy available.</p>
      </section>
    );
  }

  return (
    <section className="copilot-card p-5">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
          SC-13
        </p>
        <h2 className="mt-1 dataops-section-title">Rule Genealogy</h2>
        <p className="mt-1 text-sm dataops-muted">
          SOC -&gt; S2P -&gt; DataOps win-rate progression across domains.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {stages.map((stage) => {
          const key = String(stage.copilot || "").toLowerCase();
          const color = colors[key] || "var(--copilot-primary)";
          return (
            <article key={key || stage.copilot || "stage"} className="rounded-md border p-4" style={{ borderColor: color }}>
              <div className="mb-2 inline-flex rounded px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color }}>
                {stage.copilot || "copilot"}
              </div>
              <div className="text-2xl font-semibold" style={{ color }}>
                {formatPercent(stage.winRate ?? stage.win_rate)}
              </div>
              <p className="mt-1 text-sm dataops-muted">{formatNumber(stage.decisions)} decisions</p>
              {stage.warmStart ?? stage.warm_start ? (
                <p className="mt-2 text-xs dataops-muted">
                  Warm start {formatPercent(stage.warmStart ?? stage.warm_start)}
                </p>
              ) : null}
            </article>
          );
        })}
      </div>

      {genealogy?.improvement ? (
        <div className="mt-4 rounded-md p-3 text-sm font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
          {genealogy.improvement}
        </div>
      ) : null}
    </section>
  );
}

function formatPercent(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? `${Math.round(number * 100)}%` : "n/a";
}

function formatNumber(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? String(Math.round(number)) : "n/a";
}
