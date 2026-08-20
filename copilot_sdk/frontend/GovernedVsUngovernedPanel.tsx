import type { ReactNode } from "react";
import type { ScoreResult } from "./ScoreResultCard";

export interface GovernedVsUngovernedPanelProps {
  scoreResponse: ScoreResult | null;
  copilot: string;
  conservationStatus?: string;
  evidenceTier?: string;
  promotionState?: string;
  gateResult?: string;
  governedAction?: string;
}

export default function GovernedVsUngovernedPanel({
  scoreResponse,
  copilot,
  conservationStatus = "UNKNOWN",
  evidenceTier = "T_S",
  promotionState = "SHADOW",
  gateResult,
  governedAction,
}: GovernedVsUngovernedPanelProps) {
  const conservation = conservationStatus.toUpperCase();
  const evidence = evidenceTier.toUpperCase();
  const promotion = promotionState.toUpperCase();
  const resolvedGate = (gateResult || gateFor(conservation, evidence, promotion)).toUpperCase();
  const rawAction = scoreResponse?.action || "UNAVAILABLE";
  const finalAction = governedAction || (resolvedGate === "PASS" ? rawAction : "OBSERVE");
  const diverges = rawAction !== "UNAVAILABLE" && rawAction !== finalAction;

  return (
    <section
      data-testid="governed-vs-ungoverned-panel"
      className={`copilot-card p-5 ${diverges ? "border-2 border-red-400/70" : ""}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-amber-700">DIFF-1</p>
          <h2 className="mt-1 text-lg font-semibold">Governed versus ungoverned</h2>
          <p className="mt-1 text-sm opacity-75">{copilot}: the same input through two decision paths.</p>
        </div>
        {diverges ? <span data-testid="governance-divergence" className="rounded-full bg-red-500/15 px-2 py-1 text-xs font-semibold text-red-700">Decision diverges</span> : null}
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <PathCard
          testId="ungoverned-path"
          title="Ungoverned path"
          subtitle="Raw scorer output"
          scoreResponse={scoreResponse}
          action={rawAction}
        >
          <p className="text-xs opacity-70">No conservation, evidence, or promotion checks.</p>
        </PathCard>
        <PathCard
          testId="governed-path"
          title="Governed path"
          subtitle="Conservation + evidence + promotion"
          scoreResponse={scoreResponse}
          action={finalAction}
        >
          <div className="grid gap-2 text-sm">
            <Badge label="Conservation" value={conservation} />
            <Badge label="Evidence" value={evidence} />
            <Badge label="Promotion" value={promotion} />
            <Badge label="Gate" value={resolvedGate} />
          </div>
        </PathCard>
      </div>

      <p data-testid="governance-caption" className="mt-4 text-center text-sm font-semibold opacity-80">
        Same input. Same model. Different decision. The difference is governance.
      </p>
    </section>
  );
}

function PathCard({
  testId,
  title,
  subtitle,
  scoreResponse,
  action,
  children,
}: {
  testId: string;
  title: string;
  subtitle: string;
  scoreResponse: ScoreResult | null;
  action: string;
  children: ReactNode;
}) {
  return (
    <article data-testid={testId} className="rounded-md border border-white/10 p-4">
      <p className="text-xs uppercase tracking-wide opacity-65">{subtitle}</p>
      <h3 className="mt-1 text-base font-semibold">{title}</h3>
      <div className="mt-4 grid gap-2 text-sm">
        <div className="flex items-center justify-between"><span className="opacity-70">Score</span><strong>{scoreResponse ? scoreResponse.confidence.toFixed(2) : "-"}</strong></div>
        <div className="flex items-center justify-between"><span className="opacity-70">Action</span><strong>{action}</strong></div>
        <div className="flex items-center justify-between"><span className="opacity-70">Category</span><strong>{scoreResponse?.category || "-"}</strong></div>
      </div>
      <div className="mt-4">{children}</div>
    </article>
  );
}

function Badge({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between rounded border border-white/10 px-2 py-1"><span className="opacity-70">{label}</span><strong>{value}</strong></div>;
}

function gateFor(conservation: string, evidence: string, promotion: string): string {
  if (conservation === "RED") return "BLOCK";
  if (evidence !== "T_O") return "ABSTAIN";
  if (!promotion.includes("PROMOTED") && !promotion.includes("FULL")) return "HELD";
  return conservation === "GREEN" ? "PASS" : "HELD";
}
