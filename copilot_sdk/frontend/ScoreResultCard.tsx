import { useState } from "react";

export interface ScoreResult {
  decisionId: string;
  action: string;
  actionIndex: number;
  confidence: number;
  probabilities: number[];
  category: string;
  factors?: Record<string, number>;
  actionNames: string[];
}

export interface RewardLine {
  reward: number;
  previousReward?: number | null;
  rewardMultiplier?: number;
}

export interface CentroidDelta {
  value: number;
  beforeLabel?: string;
  afterLabel?: string;
}

export interface ScoreResultCardProps {
  result: ScoreResult;
  onConfirm: (decisionId: string) => void;
  onOverride: (decisionId: string, action: string) => void;
  iksDelta?: number;
  rewardLine?: RewardLine;
  centroidDelta?: CentroidDelta;
}

function clampUnit(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

export default function ScoreResultCard({
  result,
  onConfirm,
  onOverride,
  iksDelta,
  rewardLine,
  centroidDelta,
}: ScoreResultCardProps) {
  const [confirmed, setConfirmed] = useState(false);
  const [showCentroid, setShowCentroid] = useState(false);

  function confirm() {
    onConfirm(result.decisionId);
    setConfirmed(true);
  }

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
            Recommended Action
          </h2>
          <p className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
            {result.category}
          </p>
        </div>
        <span
          className="rounded-full px-3 py-1 text-sm font-semibold"
          style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-primary)" }}
        >
          {(clampUnit(result.confidence) * 100).toFixed(0)}%
        </span>
      </div>

      <div className="mb-4 rounded-md p-4" style={{ background: "var(--copilot-surface-muted)" }}>
        <div className="text-xs uppercase tracking-wide" style={{ color: "var(--copilot-text-subtle)" }}>
          Action
        </div>
        <div className="text-2xl font-semibold" style={{ color: "var(--copilot-text)" }}>
          {result.action}
        </div>
      </div>

      <div className="mb-4 flex flex-col gap-2">
        {result.actionNames.map((name, index) => {
          const probability = clampUnit(result.probabilities[index] ?? 0);
          const recommended = index === result.actionIndex;
          return (
            <div key={name}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span style={{ color: recommended ? "var(--copilot-primary)" : "var(--copilot-text-muted)" }}>
                  {name}
                </span>
                <span style={{ color: "var(--copilot-text)" }}>{(probability * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 rounded-full" style={{ background: "var(--copilot-surface-muted)" }}>
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${probability * 100}%`,
                    background: recommended ? "var(--copilot-primary)" : "var(--copilot-accent)",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex flex-wrap gap-2">
        <button type="button" className="copilot-button px-3 py-2 text-sm" onClick={confirm}>
          Confirm
        </button>
        <select
          className="copilot-button-secondary px-3 py-2 text-sm"
          defaultValue=""
          onChange={(event) => {
            if (event.target.value) {
              onOverride(result.decisionId, event.target.value);
              event.target.value = "";
            }
          }}
          aria-label="Override action"
        >
          <option value="" disabled>
            Override
          </option>
          {result.actionNames.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {confirmed ? (
        <div className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="grid gap-3 md:grid-cols-3">
            {typeof iksDelta === "number" ? (
              <Metric label="IKS delta" value={`${iksDelta > 0 ? "+" : ""}${iksDelta.toFixed(1)}`} />
            ) : null}
            {rewardLine ? (
              <Metric label="Reward" value={rewardLine.reward.toFixed(3)} />
            ) : null}
            {rewardLine?.rewardMultiplier !== undefined ? (
              <Metric label="Multiplier" value={`${rewardLine.rewardMultiplier.toFixed(2)}x`} />
            ) : null}
          </div>

          {centroidDelta ? (
            <div className="mt-3">
              <button
                type="button"
                className="text-sm font-semibold"
                style={{ color: "var(--copilot-primary)" }}
                onClick={() => setShowCentroid((value) => !value)}
              >
                {showCentroid ? "Hide" : "Show"} centroid delta
              </button>
              {showCentroid ? (
                <div className="mt-2 rounded-md p-3" style={{ background: "var(--copilot-surface-muted)" }}>
                  <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>
                    {centroidDelta.value.toFixed(4)}
                  </div>
                  <div style={{ color: "var(--copilot-text-muted)" }}>
                    {centroidDelta.beforeLabel || "Before"} to {centroidDelta.afterLabel || "after"}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs" style={{ color: "var(--copilot-text-muted)" }}>
        {label}
      </div>
      <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value}
      </div>
    </div>
  );
}
