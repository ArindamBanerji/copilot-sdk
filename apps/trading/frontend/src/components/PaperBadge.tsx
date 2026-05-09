export default function PaperBadge() {
  return (
    <div
      className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold"
      style={{
        borderColor: "var(--copilot-border)",
        background: "var(--copilot-primary-light)",
        color: "var(--copilot-primary)",
      }}
    >
      <span aria-hidden="true">P</span>
      <span>Paper</span>
    </div>
  );
}
