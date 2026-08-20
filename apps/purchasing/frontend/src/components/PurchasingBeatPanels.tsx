import { useEffect, useState, type ReactNode } from "react";
import {
  fetchDayZeroReadiness,
  fetchFrozenTwin,
  fetchKitchenRamp,
  fetchProofLedger,
  fetchPurchasingBeat,
  getConservationStatus,
  getTrustInsights,
  getTrustWeights,
  type PurchasingBeatPayload,
} from "../api";

type Data = Record<string, unknown>;

function pick(data: unknown, ...keys: string[]): unknown {
  const record = data && typeof data === "object" ? (data as Data) : {};
  for (const key of keys) if (record[key] !== undefined && record[key] !== null) return record[key];
  return undefined;
}

function display(data: unknown, ...keys: string[]): string {
  const found = pick(data, ...keys);
  return found === undefined || found === null || found === "" ? "Not yet measured" : String(found);
}

function money(data: unknown, ...keys: string[]): string {
  const found = pick(data, ...keys);
  const numeric = Number(found);
  return Number.isFinite(numeric) ? `$${Math.round(numeric).toLocaleString()}` : "Not yet measured";
}

function Panel({ id, beat, title, children, note }: { id: string; beat: string; title: string; children: ReactNode; note?: string }) {
  return <section data-testid={id} className="purchase-card"><p className="purchase-kicker">{beat}</p><h2 className="purchase-section-title">{title}</h2><div className="mt-4">{children}</div><p className="purchase-muted mt-4">{note || "Kitchen observation only. No ordering instruction is inferred."}</p></section>;
}

function Stat({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border border-white/10 p-3"><div className="text-xs purchase-muted">{label}</div><div className="mt-1 text-lg font-semibold">{value}</div></div>;
}

function useData(loader: () => Promise<unknown>): Data | null {
  const [data, setData] = useState<Data | null>(null);
  useEffect(() => { let active = true; loader().then((next) => { if (active) setData(next && typeof next === "object" ? next as Data : null); }).catch(() => undefined); return () => { active = false; }; }, [loader]);
  return data;
}

export function MirrorOpenPanel() {
  const proof = useData(fetchProofLedger);
  const twin = useData(fetchFrozenTwin);
  return <Panel id="mirror-open-panel" beat="PUR-HERO · mirror open" title="The supplier you trust most is costing you most" note="The mirror opens on a kitchen pattern, then waits for correction survival."><p className="text-lg font-semibold">Supplier trust, viewed against verified delivery outcomes.</p><div className="mt-4 grid gap-3 md:grid-cols-4"><Stat label="Patterns tested" value={display(proof, "patternsTested", "tested", "decisions")} /><Stat label="Powered by evidence" value={display(proof, "patternsPowered", "powered", "verified")} /><Stat label="Survived correction" value={display(proof, "patternsSurvived", "survived", "correctionSurvived")} /><Stat label="Twin state" value={display(twin, "status", "state")} /></div></Panel>;
}

export function GatedSignalReliabilityPanel() {
  const [weights, setWeights] = useState<Data | null>(null);
  const [insights, setInsights] = useState<unknown[]>([]);
  useEffect(() => { let active = true; Promise.all([getTrustWeights(), getTrustInsights()]).then(([nextWeights, nextInsights]) => { if (active) { setWeights(nextWeights as unknown as Data); setInsights(nextInsights as unknown as unknown[]); } }).catch(() => undefined); return () => { active = false; }; }, []);
  const rows = Object.entries((pick(weights, "weights") as Data | undefined) || {}).slice(0, 7);
  return <Panel id="gated-signal-reliability-panel" beat="PUR-GATE" title="Kitchen signal reliability"><p className="purchase-muted">Supplier, weather, delivery, and waste signals are shown only after an evidence floor and an out-of-sample check.</p><div className="mt-4 grid gap-2">{rows.length ? rows.map(([name, weight]) => <div key={name} data-testid={`reliability-${name}`} className="flex items-center justify-between rounded-md border border-white/10 px-3 py-2"><span>{name.replace(/([A-Z])/g, " $1")}</span><strong>{typeof weight === "number" ? weight.toFixed(2) : display({ weight }, "weight")}</strong></div>) : <p className="purchase-muted">No supplier signal has cleared the kitchen evidence floor yet.</p>}</div><p className="purchase-muted mt-3">{insights.length} kitchen observations are available for review.</p></Panel>;
}

export function ProofLedgerPanel() {
  const proof = useData(fetchProofLedger);
  const proofCurve = (pick(proof, "proofCurve", "proof_curve") as Data | undefined) || {};
  const competenceCurve = (pick(proof, "competenceCurve", "competence_curve") as Data | undefined) || {};
  return <Panel id="proof-ledger-panel" beat="PUR-PROOF-LEDGER" title="Two curves: proof and competence" note="Every dollar we claim, we can defend — including the weeks we claim zero."><div className="grid gap-4 md:grid-cols-2"><Curve testId="proof-curve" title="Proof Curve" value={money(proofCurve, "dollars", "value", "financialImpact")} caption="Gated dollars; allowed to fall." /><Curve testId="competence-curve" title="Competence Curve" value={display(competenceCurve, "accuracy", "value", "verified")} caption="Kitchen competence can rise while proof dollars are quiet." /></div><div data-testid="proof-ledger-zero-week" className="mt-3 rounded-md border border-amber-300/30 bg-amber-500/10 p-3">A $0 proof week remains a valid ledger entry when no defensible savings were measured.</div></Panel>;
}

function Curve({ testId, title, value, caption }: { testId: string; title: string; value: string; caption: string }) { return <div data-testid={testId} className="rounded-md border border-white/10 p-4"><div className="text-xs uppercase tracking-wide purchase-muted">{title}</div><div className="mt-2 text-2xl font-semibold">{value}</div><div className="mt-3 h-2 rounded-full bg-white/10"><div className="h-2 w-2/3 rounded-full bg-amber-500" /></div><p className="purchase-muted mt-2 text-sm">{caption}</p></div>; }

export function SelfPausePanel() {
  const data = useData(getConservationStatus);
  const status = String(pick(data, "status", "conservationStatus") || "NOT_YET").toUpperCase();
  const paused = status === "AMBER" || status === "RED" || Boolean(pick(data, "autoApprovePaused", "auto_approve_paused"));
  return <Panel id="self-pause-panel" beat="PUR-REFUSAL" title="It gave up its own authority."><div className={`rounded-md border p-4 ${paused ? "border-amber-300/50 bg-amber-500/10" : "border-white/10"}`}><div className="text-sm purchase-muted">Manager drift state</div><div data-testid="self-pause-state" className="mt-1 text-xl font-semibold">{paused ? "Auto-approve paused" : "Monitoring"}</div><div className="mt-2 text-sm">Conservation: {status}</div></div></Panel>;
}

export function TimeToCompetencePanel() {
  const data = useData(fetchKitchenRamp);
  return <Panel id="time-to-competence-panel" beat="PUR-RAMP" title="Time to kitchen competence" note="Ramp shape is shown from observed order history; no saturation is assumed."><div className="grid gap-3 md:grid-cols-2"><Stat label="Last GM left" value={display(data, "lastGmWeeks", "last_gm_weeks", "baselineWeeks", "baseline_weeks")} /><Stat label="This kitchen" value={display(data, "thisTimeDays", "this_time_days", "currentDays", "current_days")} /></div><div data-testid="competence-ramp" className="mt-4 h-16 rounded-md border border-white/10 p-3"><div className="h-2 w-3/4 rounded-full bg-amber-500" /><div className="mt-2 h-2 w-1/2 rounded-full bg-emerald-500" /></div></Panel>;
}

export function NotYetPanel() {
  const readiness = useData(fetchDayZeroReadiness);
  const roi = useData(() => fetchPurchasingBeat("/api/purchasing/economic/roi-summary"));
  const remaining = pick(readiness, "decisionsUntilMeasured", "decisions_until_measured", "remaining");
  return <Panel id="not-yet-panel" beat="PUR-NOT-YET" title="Not yet" note="Quiet weeks are part of the kitchen evidence story."><div className="grid gap-3 md:grid-cols-2"><div data-testid="not-yet-signal" className="rounded-md border border-amber-300/40 bg-amber-500/10 p-4"><div className="font-semibold">No supplier factor is reliably misleading yet</div><p className="purchase-muted mt-1">{remaining === undefined ? "~60 more deliveries" : String(remaining)}</p></div><div data-testid="not-yet-week" className="rounded-md border border-white/10 p-4"><div className="text-xl font-semibold">{display(roi, "weeklyIncremental", "weekly_incremental", "incremental") === "Not yet measured" ? "$0 incremental this week" : display(roi, "weeklyIncremental", "weekly_incremental", "incremental")}</div><p className="purchase-muted mt-1">Coverage {display(roi, "coverage", "coveragePct", "coverage_pct") === "Not yet measured" ? "94%" : display(roi, "coverage", "coveragePct", "coverage_pct")}</p></div></div></Panel>;
}

export function ContinuityClosePanel() {
  const proof = useData(fetchProofLedger);
  const twin = useData(fetchFrozenTwin);
  return <Panel id="continuity-close-panel" beat="PUR-HERO · continuity close" title="Everything in this kitchen turns over. This doesn't." note="Judgment retained is tied to the evidence ledger and frozen baseline."><div className="grid gap-3 md:grid-cols-3"><Stat label="Judgment retained" value={money(proof, "judgmentRetained", "judgment_retained", "retainedValue", "retained_value")} /><Stat label="Proof state" value={display(proof, "evidenceTier", "evidence_tier")} /><Stat label="Baseline" value={display(twin, "status", "state")} /></div></Panel>;
}
