import type { TrustFactor, TrustResponse } from "../types";

interface TrustCardProps {
  trust: TrustResponse | null;
}

const BAR_COLORS: Record<string, string> = {
  reliable: "#35b779",
  moderate: "#e5a93d",
  noisy: "#d95d6a",
};

export default function TrustCard({ trust }: TrustCardProps) {
  return (
    <section className="copilot-card p-4" data-testid="trust-card" aria-label="Source reliability trust profile">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em]" style={{ color: "#9b7cff" }}>
            SC-TRUST
          </p>
          <h2 className="mt-1 dataops-section-title">Source reliability</h2>
        </div>
        {trust ? <TrustScore value={trust.overallTrust} /> : null}
      </div>

      {trust ? (
        <>
          <div className="mt-4 grid gap-3" role="list" aria-label="Learned source reliability factors">
            {trust.factors.map((factor) => (
              <TrustFactorBar factor={factor} key={factor.name} />
            ))}
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full px-2 py-1 font-semibold" style={conservationStyle(trust.conservationStatus)}>
              Conservation {trust.conservationStatus}
            </span>
            <span className="dataops-muted">{trust.verifiedDecisions} verified decisions</span>
            {trust.iks !== null ? <span className="dataops-muted">IKS {trust.iks.toFixed(1)}</span> : null}
          </div>
          <p className="mt-4 text-sm leading-6 dataops-muted">{trust.narrative}</p>
        </>
      ) : (
        <p className="mt-4 text-sm dataops-muted">Trust profile unavailable.</p>
      )}
    </section>
  );
}

function TrustScore({ value }: { value: number }) {
  return (
    <div className="text-right">
      <div className="text-3xl font-bold" style={{ color: "#9b7cff" }}>{value.toFixed(2)}</div>
      <div className="text-[0.65rem] uppercase tracking-[0.12em] dataops-muted">overall trust</div>
    </div>
  );
}

function TrustFactorBar({ factor }: { factor: TrustFactor }) {
  const width = `${Math.round(Math.max(0, Math.min(1, factor.dkWeight)) * 100)}%`;
  const color = BAR_COLORS[factor.label] || "#9b7cff";
  return (
    <div data-testid="trust-factor" role="listitem">
      <div className="mb-1 flex items-center justify-between gap-3 text-xs">
        <span className="font-medium" style={{ color: "var(--copilot-text)" }}>{factor.name}</span>
        <span style={{ color }}>{factor.dkWeight.toFixed(2)} · {factor.label}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full" style={{ background: "var(--copilot-border)" }}>
        <div className="h-full rounded-full" style={{ width, background: color }} aria-label={`${factor.name} reliability ${factor.dkWeight.toFixed(2)}`} />
      </div>
    </div>
  );
}

function conservationStyle(status: string): React.CSSProperties {
  const normalized = status.toUpperCase();
  if (normalized === "GREEN") {
    return { background: "rgba(53, 183, 121, 0.16)", color: "#35b779" };
  }
  if (normalized === "RED") {
    return { background: "rgba(217, 93, 106, 0.16)", color: "#d95d6a" };
  }
  return { background: "rgba(229, 169, 61, 0.16)", color: "#e5a93d" };
}
