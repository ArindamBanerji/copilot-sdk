import type { AbstentionState } from "../types";

export default function AbstentionBanner({ state }: { state?: AbstentionState | null }) {
  if (!state?.shouldAbstain) return null;
  return <aside data-testid="abstention-banner" className="copilot-card border-rose-300/50 bg-rose-500/10 p-4" role="alert"><p className="text-xs font-semibold uppercase tracking-wide text-rose-300">DI-ABSTAIN · I DON’T KNOW</p><h2 className="mt-1 text-lg font-semibold text-rose-100">Insufficient evidence — abstaining</h2><p className="mt-1 text-sm text-rose-100/80">{state.reason || "The system does not have enough evidence for this alert type."}</p><p className="mt-2 text-xs text-rose-100/70">Evidence: {state.currentEvidence ?? 0} / required {state.evidenceFloor ?? "threshold"}</p></aside>;
}
