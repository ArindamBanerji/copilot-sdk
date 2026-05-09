const checklistItems = [
  "Reviewed earnings/financials",
  "Analyzed chart + key levels",
  "Compared sector peers",
  "Scanned news/catalysts",
  "Written thesis documented",
];

export default function ResearchChecklist({
  value,
  onChange,
}: {
  value: boolean[];
  onChange: (next: boolean[]) => void;
}) {
  const checkedCount = value.filter(Boolean).length;
  return (
    <section className="copilot-card p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold">Research Checklist</h2>
          <p className="text-sm trading-muted">Research depth: {checkedCount}/5</p>
        </div>
        <div className="rounded-md px-3 py-2 text-sm font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
          {(checkedCount / 5).toFixed(2)}
        </div>
      </div>
      <div className="mt-4 grid gap-2">
        {checklistItems.map((item, index) => (
          <label key={item} className="flex items-center gap-3 rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
            <input
              type="checkbox"
              checked={Boolean(value[index])}
              onChange={(event) => {
                const next = [...value];
                next[index] = event.target.checked;
                onChange(next);
              }}
            />
            <span className="text-sm">{item}</span>
          </label>
        ))}
      </div>
    </section>
  );
}
