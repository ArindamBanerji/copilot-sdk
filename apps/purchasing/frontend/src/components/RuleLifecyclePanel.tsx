const STATES = [
  ["proposed", "Candidate rule observed from recent exceptions."],
  ["shadow", "Rule tracked without purchase workflow impact."],
  ["promoted", "Rule assists live recommendations after verification."],
  ["rejected", "Rule retired when accuracy falls below threshold."],
];

export function RuleLifecyclePanel() {
  return (
    <section className="purchase-card">
      <p className="purchase-kicker">SC-15 Rule Lifecycle</p>
      <h3 className="purchase-title">Rule promotion states</h3>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        {STATES.map(([state, description]) => (
          <article key={state} className="rounded-lg border border-slate-200 bg-white p-3">
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600">{state}</span>
            <p className="mt-2 text-sm text-slate-600">{description}</p>
          </article>
        ))}
      </div>
      <p className="purchase-muted mt-4">Based on seeded evolution data and GraphStore verification.</p>
    </section>
  );
}

