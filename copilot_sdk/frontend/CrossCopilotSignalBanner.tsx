import type { ReactNode } from "react";

export interface CrossCopilotSignal {
  signal_id?: string;
  source_copilot: string;
  signal_type: string;
  entity_id: string;
  confidence: number;
  detail: string;
  timestamp: string;
}

export interface CrossCopilotSignalBannerProps {
  signals: CrossCopilotSignal[];
  onDismiss?: (signalId: string) => void;
}

export default function CrossCopilotSignalBanner({
  signals,
  onDismiss,
}: CrossCopilotSignalBannerProps): ReactNode {
  if (signals.length === 0) return null;
  return (
    <aside
      className="mb-4 rounded-md border px-4 py-3"
      role="status"
      style={{
        borderColor: "var(--copilot-warning)",
        background: "color-mix(in srgb, var(--copilot-warning) 10%, transparent)",
        color: "var(--copilot-text)",
      }}
    >
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide">
        ⚠ Cross-copilot signals
      </div>
      <div className="grid gap-2">
        {signals.map((signal, index) => {
          const signalId = signal.signal_id ?? `${signal.source_copilot}-${signal.entity_id}-${index}`;
          return (
            <div key={signalId} className="flex items-start justify-between gap-3 text-sm">
              <div>
                <div className="font-semibold">
                  {signal.source_copilot} · {signal.entity_id}
                  <span className="ml-2 rounded px-1.5 py-0.5 text-xs" style={{ background: "var(--copilot-surface-muted)" }}>
                    {(signal.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <div style={{ color: "var(--copilot-text-muted)" }}>{signal.detail}</div>
              </div>
              {onDismiss ? (
                <button type="button" onClick={() => onDismiss(signalId)} aria-label={`Dismiss ${signal.entity_id}`}>
                  Dismiss
                </button>
              ) : null}
            </div>
          );
        })}
      </div>
      <div className="mt-2 text-xs" style={{ color: "var(--copilot-text-muted)" }}>
        Signals transfer facts; judgment is per-copilot.
      </div>
    </aside>
  );
}
