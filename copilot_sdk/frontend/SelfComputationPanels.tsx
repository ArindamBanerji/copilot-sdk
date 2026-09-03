import AccuracyAlertsPanel from "./AccuracyAlertsPanel";
import AuditTrailPanel from "./AuditTrailPanel";
import CentroidTimelinePanel from "./CentroidTimelinePanel";
import DecisionExplorerPanel from "./DecisionExplorerPanel";
import RuleGenealogyPanel from "./RuleGenealogyPanel";
import RuleLifecyclePanel from "./RuleLifecyclePanel";

export interface SelfComputationPanelsProps { baseUrl?: string; ruleId?: string; }

export default function SelfComputationPanels({ baseUrl, ruleId = "active" }: SelfComputationPanelsProps) {
  return <div data-testid="self-computation-panels" className="grid gap-4 md:grid-cols-2"><CentroidTimelinePanel baseUrl={baseUrl} /><AccuracyAlertsPanel baseUrl={baseUrl} /><RuleGenealogyPanel baseUrl={baseUrl} /><DecisionExplorerPanel baseUrl={baseUrl} /><RuleLifecyclePanel baseUrl={baseUrl} ruleId={ruleId} /><AuditTrailPanel baseUrl={baseUrl} /></div>;
}
