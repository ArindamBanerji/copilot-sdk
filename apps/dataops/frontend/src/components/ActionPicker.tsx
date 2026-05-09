import type { AERecommendation } from "../types";
import AERecommendationBadge from "./AERecommendationBadge";

export const DATAOPS_ACTIONS = [
  { value: "auto_approve", label: "Auto-approve", scoreLabel: "Auto-approve" },
  { value: "investigate", label: "Investigate", scoreLabel: "Investigate" },
  { value: "escalate_to_owner", label: "Escalate to owner", scoreLabel: "Escalate" },
  { value: "pause_downstream", label: "Pause downstream", scoreLabel: "Pause downstream" },
  { value: "refer_to_specialist", label: "Refer to specialist", scoreLabel: "Refer" },
] as const;

interface ActionPickerProps {
  recommendation?: AERecommendation | null;
  selectedAction?: string | null;
  disabled?: boolean;
  onAction: (action: string) => void;
}

export default function ActionPicker({ recommendation, selectedAction, disabled, onAction }: ActionPickerProps) {
  const recommendedAction = inferRecommendedAction(recommendation);

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="dataops-section-title">Action</h2>
          <p className="text-sm dataops-muted">Choose the operational response. Factors are already computed.</p>
        </div>
        {recommendation ? (
          <AERecommendationBadge
            action={recommendedAction ? labelForAction(recommendedAction) : "AE suggestion"}
            variantId={recommendation.variantId}
            confidence={recommendation.confidence}
          />
        ) : null}
      </div>

      <div className="grid gap-2 md:grid-cols-5">
        {DATAOPS_ACTIONS.map((action) => {
          const isRecommended = action.value === recommendedAction;
          const selected = action.value === selectedAction;
          return (
            <button
              key={action.value}
              type="button"
              disabled={disabled}
              onClick={() => onAction(action.value)}
              className="rounded-md border px-3 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60"
              style={{
                borderColor: isRecommended || selected ? "var(--copilot-primary)" : "var(--copilot-border)",
                boxShadow: isRecommended ? "0 0 0 3px rgba(124, 58, 237, 0.16)" : "none",
                background: selected ? "var(--copilot-primary)" : "var(--copilot-surface)",
                color: selected ? "var(--copilot-primary-contrast)" : "var(--copilot-text)",
              }}
            >
              {action.label}
            </button>
          );
        })}
      </div>
    </section>
  );
}

export function labelForAction(action: string): string {
  return DATAOPS_ACTIONS.find((item) => item.value === action || item.scoreLabel === action)?.label || action;
}

export function actionFromScoreLabel(label: string): string {
  return DATAOPS_ACTIONS.find((item) => item.scoreLabel === label || item.label === label)?.value || label;
}

function inferRecommendedAction(recommendation?: AERecommendation | null): string | null {
  const text = `${recommendation?.description || ""} ${recommendation?.impact || ""}`.toLowerCase();
  if (text.includes("pause")) {
    return "pause_downstream";
  }
  if (text.includes("escalate")) {
    return "escalate_to_owner";
  }
  if (text.includes("auto")) {
    return "auto_approve";
  }
  return recommendation?.action || null;
}
