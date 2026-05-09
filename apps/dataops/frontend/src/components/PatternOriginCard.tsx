import type { PatternOrigin } from "../types";

interface PatternOriginCardProps {
  origin: PatternOrigin | null;
}

const colors: Record<string, string> = {
  soc: "#2563eb",
  s2p: "#059669",
  dataops: "#7c3aed",
};

export default function PatternOriginCard({ origin }: PatternOriginCardProps) {
  const chain = origin?.chain || [];

  return (
    <section className="copilot-card p-5">
      <div className="mb-4">
        <h2 className="dataops-section-title">Pattern Origin</h2>
        <p className="mt-1 text-sm dataops-muted">
          {origin?.narrative || "No pattern origin narrative available."}
        </p>
      </div>

      {chain.length === 0 ? (
        <div className="rounded-md p-4 text-sm dataops-muted" style={{ background: "var(--copilot-surface-muted)" }}>
          No cross-copilot chain available.
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-3">
          {chain.map((step) => {
            const key = String(step.copilot || "").toLowerCase();
            const color = colors[key] || "var(--copilot-primary)";
            return (
              <article key={`${step.copilot}-${step.ruleId}`} className="rounded-md border p-4" style={{ borderColor: color }}>
                <div className="mb-2 inline-flex rounded px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color }}>
                  {step.copilot || "copilot"}
                </div>
                <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
                  {step.ruleId || "unknown rule"}
                </div>
                <p className="mt-2 text-sm dataops-muted">{step.description || "No description."}</p>
                <p className="mt-2 text-xs dataops-muted">{step.contribution || ""}</p>
                {typeof step.warmStartPrior === "number" ? (
                  <div className="mt-3 text-sm font-semibold" style={{ color }}>
                    Warm start prior {step.warmStartPrior.toFixed(3)}
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      )}

      {(origin?.rejected || []).length > 0 ? (
        <div className="mt-4 rounded-md p-3 text-sm" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-danger)" }}>
          Rejected pattern: {origin?.rejected?.[0]?.id || "unknown"} · {origin?.rejected?.[0]?.reason || "No reason recorded."}
        </div>
      ) : null}
    </section>
  );
}
