export interface MeasurementStateView {
  state?: string;
  decisionsVerified?: number;
  decisionsNeeded?: number;
  armsMeasured?: number;
  armsTotal?: number;
  accuracy?: number | null;
  iks?: number | null;
  message?: string;
  provenance?: string;
}

interface DayZeroPanelProps {
  measurementState: MeasurementStateView | null;
}

const STEPS = ["instrument_validated", "accumulating", "measured"] as const;

function stateLabel(state: string): string {
  return state.replace(/_/g, " ").replace(/\b\w/g, (letter: string) => letter.toUpperCase());
}

function currentIndex(state?: string): number {
  const index = STEPS.indexOf((state || "instrument_validated").toLowerCase() as (typeof STEPS)[number]);
  return index < 0 ? 0 : index;
}

export default function DayZeroPanel({ measurementState }: DayZeroPanelProps) {
  const state = measurementState?.state?.toLowerCase() || "instrument_validated";
  const activeIndex = currentIndex(state) + 1;
  const measured = state === "measured" && measurementState?.provenance === "real_measured";
  const verified = measurementState?.decisionsVerified ?? 0;
  const provenance = measured ? "real_measured" : "sample";

  return (
    <section className="copilot-card p-5" data-testid="day-zero-panel" aria-label="Day-zero measurement state">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-purple-200/75">DZ-1 · Day zero</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Measurement state</h2>
        </div>
        <span
          className={`rounded-full border px-2 py-1 text-xs font-semibold ${measured
            ? "border-emerald-300/40 bg-emerald-500/10 text-emerald-200"
            : "border-amber-300/40 bg-amber-500/10 text-amber-200"}`}
          data-testid="measurement-provenance"
        >
          {provenance}
        </span>
      </div>

      <div className="mt-5 grid grid-cols-4 gap-2" role="list" aria-label="Measurement state ladder">
        {["day_zero", ...STEPS].map((step, index) => (
          <div
            key={step}
            role="listitem"
            data-testid={`measurement-step-${step}`}
            className={`rounded-md border px-3 py-3 text-center text-xs font-semibold ${index === activeIndex
              ? "border-purple-300/70 bg-purple-500/20 text-white"
              : index < activeIndex
                ? "border-emerald-300/30 bg-emerald-500/10 text-emerald-200"
                : "border-white/10 text-white/45"}`}
          >
            <span className="block text-base">{index}</span>
            <span>{step === "day_zero" ? "Day zero" : stateLabel(step)}</span>
          </div>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
        <span className="font-semibold text-white">Current: {stateLabel(state)}</span>
        <span className="dataops-muted">{verified} verified decisions</span>
        {measurementState?.decisionsNeeded ? (
          <span className="dataops-muted">{measurementState.decisionsNeeded} needed for the next arm</span>
        ) : null}
      </div>
      <p className="mt-3 text-sm leading-6 dataops-muted">
        This number was EARNED from {verified} verified decisions, not fabricated.
        {state === "instrument_validated" ? " The instrument is working. The number will fill in on YOUR data." : null}
      </p>
      {measurementState?.message ? <p className="mt-2 text-xs dataops-muted">{measurementState.message}</p> : null}
    </section>
  );
}
