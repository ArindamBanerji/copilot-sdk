export default function RuleLifecyclePanel() {
  const states = ["proposed", "shadow", "promoted", "rejected"];
  return (
    <section className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase" style={{ color: "var(--copilot-primary)" }}>SC-15</p>
      <h2 className="mt-1 text-xl font-semibold">Rule Lifecycle</h2>
      <div className="mt-4 grid gap-2 sm:grid-cols-4">
        {states.map((state) => (
          <div key={state} className="rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
            {state.replace(/_/g, " ")}
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs trading-muted">Lifecycle state is ready for promoted trading rules.</p>
    </section>
  );
}
