import { CentroidExplorer } from "./CentroidExplorer";

export function CentroidExplorerPanel({ decisionId }: { decisionId?: string }) {
  return <CentroidExplorer decisionId={decisionId} />;
}
