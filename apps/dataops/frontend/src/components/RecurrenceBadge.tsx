interface RecurrenceBadgeProps {
  count?: number;
}

export default function RecurrenceBadge({ count }: RecurrenceBadgeProps) {
  const safeCount = Number.isFinite(count) ? Number(count) : 0;
  let label = "First-time ⚡";
  let tone = "var(--copilot-info)";

  if (safeCount >= 7) {
    label = `Recurring (${safeCount}x)`;
    tone = "var(--copilot-primary)";
  } else if (safeCount > 1) {
    label = `Seen ${safeCount}x before`;
    tone = "var(--copilot-warning)";
  }

  return (
    <span className="shrink-0 rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)", color: tone }}>
      {label}
    </span>
  );
}
