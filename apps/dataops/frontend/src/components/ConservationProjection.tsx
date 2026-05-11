import { ConservationProjection as SharedConservationProjection } from "../../../../../copilot_sdk/frontend";
import type { ConservationState, TrajectoryResponse } from "../types";

interface ConservationProjectionProps {
  conservation: ConservationState | null;
  trajectory: TrajectoryResponse | null;
}

export default function ConservationProjection({
  conservation,
  trajectory,
}: ConservationProjectionProps) {
  return <SharedConservationProjection conservation={conservation} trajectory={trajectory} />;
}
