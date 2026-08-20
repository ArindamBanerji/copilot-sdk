import { useEffect, useState, type ReactNode } from "react";

export interface MeasurementStateView {
  state?: string;
  decisionsVerified?: number;
  decisions_verified?: number;
  decisionsNeeded?: number;
  decisions_needed?: number;
  armsMeasured?: number;
  arms_measured?: number;
  armsTotal?: number;
  arms_total?: number;
  accuracy?: number | null;
  iks?: number | null;
  message?: string;
  provenance?: string;
  evidenceTier?: string;
  evidence_tier?: string;
  conservationStatus?: string;
  conservation_status?: string;
}

export interface DayZeroPanelProps {
  /** New consumers identify their copilot and backend port. */
  copilot?: string;
  port?: number;
  healthEndpoint?: string;
  conservationEndpoint?: string;
  /** Compatibility input for consumers that already own measurement state. */
  measurementState?: MeasurementStateView | null;
  threshold?: number;
  renderEvidenceTier?: (tier: string, label: string) => ReactNode;
}

type MeasurementState = "instrument_validated" | "accumulating" | "measured";

interface PanelState extends MeasurementStateView {
  state: MeasurementState;
  decisionsVerified: number;
  decisionsNeeded: number;
  evidenceTier: "T_S" | "T_O";
  evidenceLabel: string;
  conservationStatus: string;
}

const DEFAULT_THRESHOLD = 30;
const STEPS: Array<{ id: MeasurementState; label: string }> = [
  { id: "instrument_validated", label: "Instrument validated" },
  { id: "accumulating", label: "Accumulating" },
  { id: "measured", label: "Measured" },
];

const DEFAULT_PANEL_STATE: PanelState = {
  state: "instrument_validated",
  decisionsVerified: 0,
  decisionsNeeded: DEFAULT_THRESHOLD,
  accuracy: null,
  iks: null,
  evidenceTier: "T_S",
  evidenceLabel: "synthetic / modelled — not measured",
  conservationStatus: "AMBER",
  provenance: "instrument",
  message: "The instrument is working. The proof is calibrating.",
};

export default function DayZeroPanel({
  copilot,
  port = 8030,
  healthEndpoint,
  conservationEndpoint,
  measurementState,
  threshold = DEFAULT_THRESHOLD,
  renderEvidenceTier,
}: DayZeroPanelProps) {
  const [loadedState, setLoadedState] = useState<PanelState>(DEFAULT_PANEL_STATE);
  const [loading, setLoading] = useState(measurementState === undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (measurementState !== undefined) {
      setLoadedState(toPanelState(measurementState, threshold));
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    const base = import.meta.env.VITE_API_URL || `http://127.0.0.1:${port}`;
    const healthUrl = resolveEndpoint(base, healthEndpoint, "/api/health");
    const conservationUrl = resolveEndpoint(base, conservationEndpoint, "/api/conservation/status");

    Promise.all([fetchJson(healthUrl), fetchJson(conservationUrl)])
      .then(([health, conservation]) => {
        if (cancelled) return;
        setLoadedState(toPanelState(mergePayloads(health, conservation), threshold));
        setError(null);
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setLoadedState(DEFAULT_PANEL_STATE);
          setError(caught instanceof Error ? caught.message : "Measurement state unavailable");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [measurementState, threshold, port, healthEndpoint, conservationEndpoint]);

  const state = measurementState === undefined
    ? loadedState
    : toPanelState(measurementState, threshold);
  const activeIndex = STEPS.findIndex((step) => step.id === state.state);
  const currentIndex = activeIndex < 0 ? 0 : activeIndex;
  const measured = state.state === "measured" && state.evidenceTier === "T_O";
  const title = loading ? "Measurement state" : titleFor(state.state);
  const tierBadge = renderEvidenceTier
    ? renderEvidenceTier(state.evidenceTier, state.evidenceLabel)
    : <EvidenceTierBadge tier={state.evidenceTier} label={state.evidenceLabel} />;

  return (
    <div data-testid="day-zero-card">
      <section className="copilot-card p-5" data-testid="day-zero-panel" aria-label={`${copilot || "Copilot"} day-zero measurement state`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary, #7c3aed)" }}>
            V6 · DZ-1 · Day-zero honesty
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text, #111827)" }}>{title}</h2>
          <p className="mt-1 text-sm dataops-muted">{copilot ? `${capitalize(copilot)} · instrument state` : "Instrument state"}</p>
        </div>
        <div data-testid="day-zero-evidence-tier">{tierBadge}</div>
      </div>

      <div className="mt-5 grid gap-2 md:grid-cols-3" role="list" aria-label="Day-zero measurement state transition">
        {STEPS.map((step, index) => (
          <div
            key={step.id}
            role="listitem"
            data-testid={`measurement-step-${step.id}`}
            data-state={step.id === state.state ? "current" : index < currentIndex ? "complete" : "pending"}
            className={`rounded-md border px-3 py-3 text-center text-xs font-semibold ${index === currentIndex
              ? "border-purple-300/70 bg-purple-500/20 text-white"
              : index < currentIndex
                ? "border-emerald-300/40 bg-emerald-500/10 text-emerald-200"
                : "border-white/10 text-white/45"}`}
          >
            <span className="block text-base">{index + 1}</span>
            <span>{step.label}</span>
          </div>
        ))}
      </div>

      <div className="mt-4">
        <div className="flex flex-wrap items-center gap-2 text-sm" data-testid="day-zero-state-summary">
          <span className="font-semibold" data-testid="day-zero-state">{state.state.toUpperCase()}</span>
          <span className="dataops-muted">{state.decisionsVerified} verified decisions</span>
          {state.decisionsNeeded > 0 ? <span className="dataops-muted">{state.decisionsNeeded} needed</span> : null}
        </div>

        {state.state === "measured" && measured ? (
          <MeasuredBody state={state} />
        ) : state.state === "accumulating" ? (
          <AccumulatingBody state={state} threshold={threshold} />
        ) : (
          <InstrumentBody />
        )}

        <p className="mt-4 text-sm leading-6 dataops-muted" data-testid="day-zero-caption">
          Day one we don&apos;t hand you a fake ROI. We show the instrument working and the proof it&apos;s calibrating.
        </p>
        <p className="mt-2 text-xs dataops-muted">{state.message}</p>
        {error ? <p className="mt-2 text-xs" style={{ color: "var(--copilot-danger, #b91c1c)" }}>Live state unavailable; showing the instrument contract.</p> : null}
      </div>
      </section>
    </div>
  );
}

function InstrumentBody() {
  return (
    <div className="mt-3 grid gap-2 text-sm" data-testid="day-zero-instrument-body">
      <p>The instrument is working. The proof is calibrating.</p>
      <p className="font-semibold">Awaiting verified decisions from your data.</p>
      <p className="font-semibold">No magnitude claims yet.</p>
      <p className="dataops-muted">This is what honest looks like on day one. No fake numbers.</p>
    </div>
  );
}

function AccumulatingBody({ state, threshold }: { state: PanelState; threshold: number }) {
  const total = Math.max(threshold, state.decisionsVerified + state.decisionsNeeded);
  const progress = Math.min(100, Math.round((state.decisionsVerified / total) * 100));
  return (
    <div className="mt-4" data-testid="day-zero-accumulating-body">
      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full bg-amber-500" style={{ width: `${progress}%` }} />
      </div>
      <div className="mt-2 text-sm font-semibold">Accumulating. {state.decisionsVerified} decisions verified. Building judgment.</div>
      <div className="mt-1 text-xs dataops-muted">{state.decisionsVerified} / {total} decisions · magnitude remains gated until the instrument is measured.</div>
    </div>
  );
}

function MeasuredBody({ state }: { state: PanelState }) {
  const iks = formatNumber(state.iks);
  const conservation = state.conservationStatus || "GREEN";
  return (
    <div className="mt-3" data-testid="day-zero-measured-body">
      <p className="text-sm font-semibold">Measured. IKS = {iks}. Conservation {conservation}. Judgment measured.</p>
      <div className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
        <Metric label="Accuracy" value={formatPercent(state.accuracy)} />
        <Metric label="IKS" value={iks} />
        <Metric label="Verified decisions" value={String(state.decisionsVerified)} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div><div className="text-xs dataops-muted">{label}</div><div className="text-lg font-semibold">{value}</div></div>;
}

function EvidenceTierBadge({ tier, label }: { tier: string; label: string }) {
  return <span className="rounded-full border border-amber-300/40 bg-amber-500/10 px-2 py-1 text-xs font-semibold text-amber-200" title={label}>{tier}</span>;
}

function titleFor(state: MeasurementState): string {
  if (state === "measured") return "Measured";
  if (state === "accumulating") return "Accumulating evidence";
  return "Instrument Calibrated";
}

function toPanelState(raw: MeasurementStateView | null | undefined, threshold: number): PanelState {
  const value = raw || {};
  const verified = numberOr(value.decisionsVerified ?? value.decisions_verified, 0);
  const needed = numberOr(value.decisionsNeeded ?? value.decisions_needed, Math.max(threshold - verified, 0));
  const provenance = textOr(value.provenance, verified >= threshold ? "real_measured" : verified > 0 ? "accumulating" : "instrument");
  const rawState = normalizeState(value.state);
  const state = rawState || (verified <= 0 ? "instrument_validated" : needed > 0 ? "accumulating" : "measured");
  const tier = evidenceTier(value, state, provenance);
  return {
    ...value,
    state,
    decisionsVerified: verified,
    decisionsNeeded: needed,
    evidenceTier: tier,
    evidenceLabel: tier === "T_O" ? "observed / measured" : "synthetic / modelled — not measured",
    conservationStatus: textOr(value.conservationStatus ?? value.conservation_status, state === "measured" ? "GREEN" : "AMBER"),
    provenance,
  };
}

function normalizeState(value?: string): MeasurementState | null {
  const normalized = value?.toLowerCase().replace(/[-\s]/g, "_");
  if (normalized === "instrument_validated" || normalized === "instrument" || normalized === "a") return "instrument_validated";
  if (normalized === "accumulating" || normalized === "b") return "accumulating";
  if (normalized === "measured" || normalized === "c") return "measured";
  return null;
}

function evidenceTier(value: MeasurementStateView, state: MeasurementState, provenance: string): "T_S" | "T_O" {
  const explicit = textOr(value.evidenceTier ?? value.evidence_tier, "").toUpperCase();
  if (explicit === "T_O" || explicit === "OBSERVED") return "T_O";
  if (state === "measured" && ["real_measured", "observed", "pilot"].includes(provenance.toLowerCase())) return "T_O";
  return "T_S";
}

function mergePayloads(health: Record<string, unknown>, conservation: Record<string, unknown>): MeasurementStateView {
  const nestedHealth = objectValue(health.measurementState ?? health.measurement_state);
  const nestedConservation = objectValue(health.conservation);
  return {
    ...nestedHealth,
    ...nestedConservation,
    ...conservation,
    state: textOr(nestedHealth.state ?? health.phase ?? conservation.state, ""),
    decisionsVerified: numberOr(
      nestedHealth.decisionsVerified ?? nestedHealth.decisions_verified ?? conservation.verified_count ?? conservation.verifiedCount ?? health.verified_count,
      0,
    ),
    decisionsNeeded: numberOr(
      nestedHealth.decisionsNeeded ?? nestedHealth.decisions_needed ?? conservation.decisions_needed,
      DEFAULT_THRESHOLD,
    ),
    accuracy: optionalNumber(nestedHealth.accuracy ?? conservation.q),
    iks: optionalNumber(nestedHealth.iks ?? conservation.iks ?? health.iks),
    provenance: textOr(nestedHealth.provenance ?? conservation.provenance, "instrument"),
    conservationStatus: textOr(conservation.status ?? nestedConservation.status, "AMBER"),
  };
}

async function fetchJson(url: string): Promise<Record<string, unknown>> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const payload: unknown = await response.json();
  return objectValue(payload);
}

function resolveEndpoint(base: string, endpoint: string | undefined, fallback: string): string {
  const value = endpoint || fallback;
  return value.startsWith("http") ? value : `${base}${value.startsWith("/") ? value : `/${value}`}`;
}

function objectValue(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function numberOr(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function optionalNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function textOr(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function formatPercent(value?: number | null): string {
  return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "pending";
}

function formatNumber(value?: number | null): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(1) : "pending";
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
