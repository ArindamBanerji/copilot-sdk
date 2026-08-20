import { useEffect, useState, type ReactNode } from "react";
import {
  fetchClaimGate,
  fetchRejectionSummary,
  fetchSituationAbstention,
  fetchSituationConditionedStats,
  fetchSituationRegime,
  fetchSituationRejections,
  fetchVolatilityDispersion,
  fetchVolatilityRichCheap,
  fetchVolatilitySharpe,
  fetchVolatilityTailBets,
  fetchVolatilityVrp,
} from "../api";
import type {
  ClaimGateResponse,
  SituationAbstentionResponse,
  SituationConditionedStatsResponse,
  SituationRegimeResponse,
  SituationRejectionsResponse,
  VolatilitySurfaceResponse,
} from "../types";

type AnyPayload = Record<string, unknown>;

function asRecord(value: unknown): AnyPayload {
  return value && typeof value === "object" ? (value as AnyPayload) : {};
}

function value(payload: unknown, ...keys: string[]): unknown {
  const record = asRecord(payload);
  for (const key of keys) if (record[key] !== undefined && record[key] !== null) return record[key];
  return undefined;
}

function text(payload: unknown, fallback = "Observation data is accumulating."): string {
  const found = value(payload, "observation", "message", "summary");
  return typeof found === "string" && found.trim() ? found : fallback;
}

function number(payload: unknown, ...keys: string[]): string {
  const found = value(payload, ...keys);
  return typeof found === "number" && Number.isFinite(found) ? found.toFixed(2) : "-";
}

function percent(payload: unknown, ...keys: string[]): string {
  const found = value(payload, ...keys);
  return typeof found === "number" && Number.isFinite(found) ? `${Math.round(found * 100)}%` : "-";
}

function Evidence({ payload }: { payload: unknown }) {
  return (
    <span className="rounded-full border border-white/10 px-2 py-1 text-xs trading-muted">
      Evidence: {String(value(payload, "evidenceTier", "evidence_tier", "evidenceLabel", "substantiation") || "insufficient")}
    </span>
  );
}

function Shell({ testId, title, beat, children, observation }: { testId: string; title: string; beat: string; children: ReactNode; observation?: string }) {
  return (
    <section data-testid={testId} className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide trading-muted">{beat}</p>
          <h2 className="mt-1 text-lg font-semibold">{title}</h2>
        </div>
      </div>
      <div className="mt-4">{children}</div>
      <p className="mt-4 text-sm trading-muted">{observation || "Observation only: no forward action is inferred from this panel."}</p>
    </section>
  );
}

function useData<T>(loader: () => Promise<T>): { data: T | null; loading: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    loader().then((next) => { if (!cancelled) setData(next); }).catch(() => undefined).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [loader]);
  return { data, loading };
}

export function RegimeMirrorPanel() {
  const { data, loading } = useData(fetchSituationConditionedStats);
  const regimes = Object.entries(data?.regimes || {});
  return <Shell testId="regime-mirror-panel" title="Regime mirror" beat="TRD-S1" observation={data?.mirrorMessage || undefined}>
    <div className="grid gap-3 md:grid-cols-3">{regimes.map(([regime, row]) => <div key={regime} data-testid={`regime-mirror-${regime}`} className="rounded-md border border-white/10 p-3"><div className="text-xs uppercase trading-muted">{regime}</div><div className="mt-1 text-xl font-semibold">{loading ? "-" : percent(row, "accuracy")}</div><div className="text-xs trading-muted">{String(value(row, "verifiedCount", "decisionCount") || 0)} verified observations</div></div>)}</div>
  </Shell>;
}

export function SituationalAbstentionBanner() {
  const { data, loading } = useData<SituationAbstentionResponse>(fetchSituationAbstention);
  return <div data-testid="situational-abstention-banner" className="rounded-md border border-amber-300/40 bg-amber-500/10 p-4"><div className="text-xs uppercase tracking-wide trading-muted">TRD-S2 · regime evidence state</div><p className="mt-1 font-semibold">{loading ? "Checking regime evidence..." : data?.message || `Insufficient evidence in ${data?.regime || "this"} regime.`}</p><p className="mt-1 text-sm trading-muted">{data?.decisionCount ?? 0} decisions observed; minimum {data?.minimumDecisions ?? "not exposed"}.</p></div>;
}

export function AutonomyThrottlePanel() {
  const { data, loading } = useData<SituationRegimeResponse>(fetchSituationRegime);
  const amber = String(data?.conservationStatus || "").toUpperCase() === "AMBER";
  return <Shell testId="autonomy-throttle-panel" title="Situation-conditioned autonomy" beat="TRD-S3"><div className={`rounded-md border p-4 ${amber ? "border-amber-300/50 bg-amber-500/10" : "border-white/10"}`}><div className="text-sm trading-muted">Current regime: <span className="font-semibold text-white">{loading ? "-" : data?.regime || "unavailable"}</span></div><div className="mt-2 text-sm">Conservation: <span data-testid="autonomy-throttle-status" className="font-semibold">{data?.conservationStatus || "unavailable"}</span></div><div className="mt-2 text-sm">Observed autonomy multiplier: <span className="font-semibold">{number(data, "autonomyMultiplier", "autonomy_multiplier")}x</span></div></div></Shell>;
}

export function RegimeRejectionPanel() {
  const { data, loading } = useData<SituationRejectionsResponse>(fetchSituationRejections);
  return <Shell testId="regime-rejection-panel" title="Regime-scoped rejection" beat="TRD-S4"><div className="grid gap-3 md:grid-cols-3"><Metric label="Tested" value={loading ? "-" : String(data?.variantsTested ?? 0)} /><Metric label="Rejected" value={loading ? "-" : String(data?.variantsRejected ?? 0)} /><Metric label="State" value="observation" /></div></Shell>;
}

function VolPanel({ testId, title, beat, loader, fields }: { testId: string; title: string; beat: string; loader: () => Promise<VolatilitySurfaceResponse>; fields: Array<[string, string[]]> }) {
  const { data, loading } = useData(loader);
  return <Shell testId={testId} title={title} beat={beat} observation={text(data)}><div className="grid gap-3 sm:grid-cols-2">{fields.map(([label, keys]) => <Metric key={label} label={label} value={loading ? "-" : number(data, ...keys)} />)}<Evidence payload={data} /></div></Shell>;
}

export function VolShortPanel() { return <VolPanel testId="vol-short-panel" title="Clustering-adjusted Sharpe" beat="TRD-V1" loader={fetchVolatilitySharpe} fields={[["Adjusted quality", ["qualityAdjustedScore", "quality_adjusted_score"]], ["Decisions", ["nDecisions", "n_decisions"]]]} />; }
export function VRPPanel() { return <VolPanel testId="vrp-panel" title="VRP and tail-dependence window" beat="TRD-V2" loader={fetchVolatilityVrp} fields={[["VRP spread", ["vrpSpreadMean", "vrp_spread_mean"]], ["Tail capture", ["tailCapture", "tail_capture"]]]} />; }
export function RichCheapPanel() { return <VolPanel testId="rich-cheap-panel" title="Regime-conditioned rich / cheap" beat="TRD-V5" loader={fetchVolatilityRichCheap} fields={[["IV percentile", ["ivPercentile", "iv_percentile"]], ["Band", ["band"]]]} />; }
export function DispersionPanel() { return <VolPanel testId="dispersion-panel" title="Dispersion follow-rate" beat="TRD-V6" loader={fetchVolatilityDispersion} fields={[["Follow-rate", ["followRate", "follow_rate"]], ["Observed impact", ["skippedValue", "skipped_value"]]]} />; }
export function TailBetsPanel() { return <VolPanel testId="tail-bets-panel" title="Effective bets in tail" beat="TRD-V7" loader={fetchVolatilityTailBets} fields={[["Effective bets", ["effectiveBets", "effective_bets"]], ["Tail decisions", ["tailDecisions", "tail_decisions"]]]} />; }

function useClaim(): { data: ClaimGateResponse | null; loading: boolean } { return useData(fetchClaimGate); }

export function ClaimGateBadge() {
  const { data, loading } = useClaim();
  return <div data-testid="claim-gate-badge" className="copilot-card p-4"><div className="flex items-center justify-between gap-3"><div><div className="text-xs uppercase trading-muted">TRD-CLAIM-GATE</div><h2 className="mt-1 font-semibold">Evidence claim gate</h2></div><Evidence payload={data} /></div><div className="mt-3 grid grid-cols-3 gap-2 text-center"><Metric label="Tested" value={loading ? "-" : String(data?.tested ?? 0)} /><Metric label="Powered" value={loading ? "-" : String(data?.powered ?? 0)} /><Metric label="Survived" value={loading ? "-" : String(data?.survived ?? 0)} /></div></div>;
}

export function CertificatePanel() {
  const { data, loading } = useClaim();
  return <Shell testId="certificate-panel" title="Clean-trader certificate" beat="TRD-CERTIFICATE"><div className="rounded-md border border-emerald-300/40 bg-emerald-500/10 p-4 text-center text-lg font-semibold">{loading ? "Checking certificate state..." : data?.certificate || "Certificate state unavailable"}</div></Shell>;
}

export function GateDividendPanel() {
  const { data, loading } = useClaim();
  return <Shell testId="gate-dividend-panel" title="Gate dividend" beat="TRD-GATE-DIVIDEND"><div className="grid gap-3 md:grid-cols-2"><Metric label="Findings withheld" value={loading ? "-" : String(data?.withheld ?? 0)} /><Metric label="Observed impact" value={loading ? "-" : typeof data?.savedImpact === "number" ? `$${data.savedImpact.toLocaleString()}` : "-"} /></div></Shell>;
}

export function RejectionMomentTable() {
  const { data, loading } = useData(fetchRejectionSummary);
  return <Shell testId="rejection-moment-table" title="Rejection moments" beat="DM-1 / TR3"><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="py-2">State</th><th className="py-2">Count</th></tr></thead><tbody><tr className="border-t border-white/10"><td className="py-2">Tested</td><td className="py-2">{loading ? "-" : data?.totalTested ?? 0}</td></tr><tr className="border-t border-white/10"><td className="py-2">Promoted</td><td className="py-2">{loading ? "-" : data?.totalPromoted ?? 0}</td></tr><tr className="border-t border-white/10"><td className="py-2">Rejected</td><td className="py-2">{loading ? "-" : data?.totalRejected ?? 0}</td></tr></tbody></table></div></Shell>;
}

function Metric({ label, value: metricValue }: { label: string; value: string }) { return <div className="rounded-md border border-white/10 p-3"><div className="text-xs trading-muted">{label}</div><div className="mt-1 text-lg font-semibold">{metricValue}</div></div>; }
