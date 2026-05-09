import type { ReactNode } from "react";

export interface DecisionHistoryProps<T = Record<string, unknown>> {
  decisions: T[];
  renderCard: (decision: T, index: number) => ReactNode;
  title?: string;
  emptyMessage?: string;
  maxVisible?: number;
}

export default function DecisionHistory<T = Record<string, unknown>>({
  decisions,
  renderCard,
  title = "History",
  emptyMessage = "No decisions yet.",
  maxVisible = 20,
}: DecisionHistoryProps<T>) {
  const visible = decisions.slice(0, Math.max(0, maxVisible));

  return (
    <section className="copilot-card overflow-hidden">
      <div
        className="flex items-center justify-between border-b px-4 py-3"
        style={{ borderColor: "var(--copilot-border)" }}
      >
        <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
          {title}
        </h2>
        <span
          className="rounded-full px-2 py-1 text-xs font-semibold"
          style={{
            background: "var(--copilot-surface-muted)",
            color: "var(--copilot-text-muted)",
          }}
        >
          {decisions.length}
        </span>
      </div>

      {visible.length === 0 ? (
        <div className="px-4 py-8 text-sm" style={{ color: "var(--copilot-text-muted)" }}>
          {emptyMessage}
        </div>
      ) : (
        <div className="max-h-[32rem] overflow-y-auto p-3">
          <div className="flex flex-col gap-3">
            {visible.map((decision, index) => (
              <div key={index}>{renderCard(decision, index)}</div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
