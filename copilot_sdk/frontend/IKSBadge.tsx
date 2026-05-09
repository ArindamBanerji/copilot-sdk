import type { CSSProperties } from "react";

export interface IKSBadgeProps {
  value: number;
  delta?: number;
  size?: "sm" | "md" | "lg";
}

const sizeClasses: Record<NonNullable<IKSBadgeProps["size"]>, string> = {
  sm: "h-16 w-16 text-lg",
  md: "h-20 w-20 text-2xl",
  lg: "h-24 w-24 text-3xl",
};

function clampScore(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(100, value));
}

export default function IKSBadge({ value, delta, size = "md" }: IKSBadgeProps) {
  const score = Math.round(clampScore(value));
  const hasDelta = typeof delta === "number" && Number.isFinite(delta);
  const deltaColor =
    hasDelta && delta < 0 ? "var(--copilot-danger)" : "var(--copilot-success)";
  const ringStyle = {
    "--iks-fill": `${score}%`,
  } as CSSProperties;

  return (
    <div className="inline-flex flex-col items-center gap-1" style={{ color: "var(--copilot-text)" }}>
      <div
        className={`grid shrink-0 place-items-center rounded-full font-semibold ${sizeClasses[size]}`}
        style={{
          ...ringStyle,
          background:
            "conic-gradient(var(--copilot-primary) var(--iks-fill), var(--copilot-surface-muted) 0)",
          color: "var(--copilot-text)",
        }}
        aria-label={`IKS ${score}`}
      >
        <div
          className="grid h-[78%] w-[78%] place-items-center rounded-full"
          style={{ background: "var(--copilot-surface)" }}
        >
          <span>{score}</span>
        </div>
      </div>
      <div className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--copilot-text-muted)" }}>
        IKS
      </div>
      {hasDelta ? (
        <div className="text-xs font-semibold" style={{ color: deltaColor }}>
          {delta > 0 ? "+" : ""}
          {delta.toFixed(1)}
        </div>
      ) : null}
    </div>
  );
}
