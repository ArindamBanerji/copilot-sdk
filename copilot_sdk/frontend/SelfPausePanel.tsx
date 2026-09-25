export type SelfPauseStatus = "GREEN" | "AMBER" | "RED";

export interface SelfPausePanelProps {
  status: SelfPauseStatus;
  autoPauseActive: boolean;
  reason?: string;
  onSimulateFailure?: () => void;
}

const STATUS_COLORS: Record<SelfPauseStatus, string> = {
  GREEN: "#16A34A",
  AMBER: "#D97706",
  RED: "#DC2626",
};

export default function SelfPausePanel({
  status,
  autoPauseActive,
  reason,
  onSimulateFailure,
}: SelfPausePanelProps) {
  const color = STATUS_COLORS[status];
  return (
    <section className="copilot-card p-4" aria-label="Self-pause health">
      <div
        aria-hidden="true"
        style={{
          backgroundColor: color,
          borderRadius: "999px",
          height: "8px",
          transition: "background-color 300ms ease",
          width: "100%",
        }}
      />
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span
          className="rounded-full px-2 py-1 text-xs font-semibold"
          style={{ backgroundColor: color, color: "white" }}
        >
          {status}
        </span>
        {autoPauseActive ? (
          <span
            className="rounded-full px-2 py-1 text-xs font-semibold"
            style={{ backgroundColor: "var(--copilot-surface-muted)", color: "var(--copilot-text)" }}
          >
            AUTO-PAUSE ACTIVE
          </span>
        ) : null}
      </div>
      {reason ? (
        <p className="mt-2 text-sm" style={{ color: "var(--copilot-text-muted)" }}>
          {reason}
        </p>
      ) : null}
      {onSimulateFailure ? (
        <button
          className="mt-3 rounded-md border px-3 py-2 text-sm font-semibold"
          onClick={onSimulateFailure}
          style={{ borderColor: "var(--copilot-primary)", color: "var(--copilot-primary)" }}
          type="button"
        >
          Simulate Failure
        </button>
      ) : null}
    </section>
  );
}
