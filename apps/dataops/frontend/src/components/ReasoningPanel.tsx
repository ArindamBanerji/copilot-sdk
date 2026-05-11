import { ReasoningPanel as SharedReasoningPanel } from "../../../../../copilot_sdk/frontend";
import { DATAOPS_ACTIONS } from "./ActionPicker";
import { DATAOPS_FACTORS } from "./FactorAutoFill";
import type {
  FactorAutoFillResponse,
  FingerprintResponse,
  ScoreResponse,
  SimilarAlert,
} from "../types";

interface ReasoningPanelProps {
  scoreResult: ScoreResponse;
  similarAlerts: SimilarAlert[];
  fingerprint: FingerprintResponse | null;
  factorValues: FactorAutoFillResponse | null;
  actionNames?: string[];
}

const ACTION_LABELS: Record<string, string> = Object.fromEntries(
  DATAOPS_ACTIONS.map((action) => [action.value, action.label]),
);

const FACTOR_LABELS: Record<string, string> = {
  impact_scope: "Impact scope",
  source_reliability: "Source reliability",
  recurrence_frequency: "Recurrence",
  downstream_urgency: "Downstream urgency",
  data_freshness: "Data freshness",
  business_criticality: "Business criticality",
};

export default function ReasoningPanel({
  scoreResult,
  similarAlerts,
  fingerprint,
  factorValues,
  actionNames,
}: ReasoningPanelProps) {
  return (
    <SharedReasoningPanel
      scoreResult={scoreResult}
      similarItems={similarAlerts}
      fingerprint={fingerprint}
      factorValues={factorValues}
      actionNames={actionNames?.length ? actionNames : DATAOPS_ACTIONS.map((action) => action.value)}
      factorNames={DATAOPS_FACTORS.map((factor) => factor.key)}
      actionLabels={ACTION_LABELS}
      factorLabels={FACTOR_LABELS}
    />
  );
}
