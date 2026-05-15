import { useEffect, useState } from "react";

export interface TransferBadgeProps {
  apiBase: string;
  className?: string;
}

interface TransferStatus {
  warm_started?: boolean;
  warmStarted?: boolean;
  source_copilot?: string;
  sourceCopilot?: string;
  patterns_transferred?: number;
  patternsTransferred?: number;
}

export default function TransferBadge({ apiBase, className }: TransferBadgeProps) {
  const [status, setStatus] = useState<TransferStatus | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    fetch(`${apiBase}/api/transfer/status`, { signal: controller.signal })
      .then((response) => (response.ok ? response.json() : null))
      .then((payload: unknown) => {
        if (payload && typeof payload === "object") {
          setStatus(payload as TransferStatus);
        }
      })
      .catch(() => {
        setStatus(null);
      });

    return () => {
      controller.abort();
    };
  }, [apiBase]);

  const warmStarted = status?.warmStarted ?? status?.warm_started;
  if (warmStarted !== true) {
    return null;
  }

  const sourceCopilot = status?.sourceCopilot ?? status?.source_copilot ?? "unknown";
  const patternsTransferred = status?.patternsTransferred ?? status?.patterns_transferred ?? 0;

  return (
    <div
      className={className}
      data-testid="transfer-badge"
      style={{
        alignItems: "center",
        background: "rgba(20, 184, 166, 0.12)",
        border: "1px solid rgba(20, 184, 166, 0.35)",
        borderRadius: 6,
        color: "var(--copilot-text, inherit)",
        display: "inline-flex",
        fontSize: 13,
        fontWeight: 600,
        gap: 6,
        lineHeight: 1.4,
        padding: "6px 10px",
      }}
    >
      Warm-started from {sourceCopilot}: {patternsTransferred} patterns
    </div>
  );
}
