import { useEffect, useState } from "react";
import { getPatternOrigin } from "../api";
import type { PatternOrigin } from "../types";

export default function RuleGenealogyTree() {
  const [data, setData] = useState<PatternOrigin | null>(null);

  useEffect(() => {
    let cancelled = false;
    getPatternOrigin()
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const chain = data?.chain || [];
  if (chain.length === 0) {
    return null;
  }

  return (
    <section className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
        SC-13
      </p>
      <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
        Rule Genealogy
      </h2>
      <div className="mt-5 grid gap-3">
        {chain.map((step, index) => (
          <article key={`${step.copilot || "copilot"}-${index}`} className="grid gap-3 rounded-md border p-4 sm:grid-cols-[8rem_minmax(0,1fr)]" style={{ borderColor: "var(--copilot-border)" }}>
            <div>
              <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
                {String(step.copilot || "source").toUpperCase()}
              </span>
            </div>
            <div>
              <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>{step.ruleId || "rule"}</div>
              <p className="mt-1 text-sm dataops-muted">{step.description || step.contribution || "No genealogy detail available."}</p>
              {typeof step.warmStartPrior === "number" ? <p className="mt-2 text-xs dataops-muted">Accuracy prior {Math.round(step.warmStartPrior * 100)}%</p> : null}
            </div>
          </article>
        ))}
      </div>
      <p className="mt-4 text-xs dataops-muted">Based on seeded evolution data.</p>
    </section>
  );
}
