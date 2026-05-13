export default function RuleGenealogyTree() {
  return (
    <section className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase" style={{ color: "var(--copilot-primary)" }}>SC-13</p>
      <h2 className="mt-1 text-xl font-semibold">Rule Genealogy</h2>
      <div className="mt-4 grid gap-3 text-sm">
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          Trading decisions inherit their lineage from GraphStore decision, factor, recommendation, and outcome records.
        </div>
      </div>
      <p className="mt-4 text-xs trading-muted">Based on GraphStore audit data.</p>
    </section>
  );
}
