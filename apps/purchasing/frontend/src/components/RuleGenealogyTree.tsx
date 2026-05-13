export function RuleGenealogyTree() {
  return (
    <section className="purchase-card">
      <p className="purchase-kicker">SC-13 Rule Genealogy</p>
      <h3 className="purchase-title">Purchasing rule lineage</h3>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {[
          ["Seeded policy", "Invoice matching and supplier risk baseline."],
          ["GraphStore signal", "Verified purchase decisions update rule confidence."],
          ["Promoted rule", "High-accuracy patterns move into active assistance."],
        ].map(([title, body], index) => (
          <article key={title} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600">step {index + 1}</span>
            <h4 className="mt-2 font-semibold text-slate-900">{title}</h4>
            <p className="mt-1 text-sm text-slate-600">{body}</p>
          </article>
        ))}
      </div>
      <p className="purchase-muted mt-4">Based on GraphStore self-computation data.</p>
    </section>
  );
}

