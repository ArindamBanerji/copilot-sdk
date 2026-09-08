import { useEffect, useMemo, useState } from "react";
import { advanceS2PPromotion, fetchConservation, fetchPromotionStatus } from "../api";
import type { ConservationStatus, PromotionRecord } from "../types";

function label(value?: string): string {
  return String(value || "unknown").replace(/_/g, " ");
}

function nextStage(stage?: string): string {
  if (stage === "discovered") return "shadowing";
  if (stage === "shadowing") return "promoted";
  if (stage === "promoted") return "measuring";
  if (stage === "measuring") return "kept";
  if (stage === "rolled_back") return "shadowing";
  return "no transition";
}

function conservationStatus(conservation: ConservationStatus | null): string {
  return conservation?.status ?? (conservation?.passed ? "GREEN" : "UNKNOWN");
}

export function AuthorityPanel() {
  const [records, setRecords] = useState<PromotionRecord[]>([]);
  const [selected, setSelected] = useState("");
  const [conservation, setConservation] = useState<ConservationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const refresh = () => {
    setLoading(true);
    setError("");
    Promise.all([fetchPromotionStatus(), fetchConservation()]).then(([promotion, conservationState]) => {
      const nextRecords = promotion?.categories ?? [];
      setRecords(nextRecords);
      setConservation(conservationState);
      setSelected((current) => current || nextRecords[0]?.decision_class || "");
      if (!promotion) {
        setError("Could not load shadow data");
      }
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  const record = records.find((item) => item.decision_class === selected) ?? records[0] ?? null;
  const state = conservationStatus(conservation);
  const checks = useMemo(() => {
    const stage = record?.current_stage;
    return [
      { label: "Promotion record exists", met: Boolean(record) },
      { label: "Conservation state is GREEN", met: stage !== "shadowing" || state === "GREEN" },
      { label: "At least 10 shadow decisions", met: stage !== "shadowing" || (record?.shadow_decisions ?? 0) >= 10 },
      { label: "At least 10 measured decisions", met: stage !== "measuring" || (record?.measurement_decisions ?? 0) >= 10 },
      { label: "Positive measured improvement", met: stage !== "measuring" || (record?.improvement_delta ?? 0) > 0 },
    ];
  }, [record, state]);
  const target = nextStage(record?.current_stage);
  const canAdvance = Boolean(record) && record?.current_stage !== "kept" && checks.every((check) => check.met);

  const advance = async () => {
    if (!record || !canAdvance) return;
    const ok = window.confirm(
      `Advance ${label(record.decision_class)} authority from ${label(record.current_stage)} to ${label(target)}?\n\n` +
        "Impact: S2P will use the next lifecycle authority level for this exception category.",
    );
    if (!ok) return;
    setBusy(true);
    setNotice("");
    setError("");
    try {
      const result = await advanceS2PPromotion(record.decision_class, {
        shadow_decisions: record.shadow_decisions ?? 0,
        measurement_decisions: record.measurement_decisions ?? 0,
        improvement: record.improvement_delta ?? 0,
        conservation_state: state,
        evidence_tier: record.evidence_tier ?? "T_S",
        reason: "operator_advance",
      });
      setNotice(result ? (result.advanced === false ? `Held: ${label(String(result.reason ?? "gate failed"))}` : "Authority updated") : "Advance request failed");
      refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Promotion advance failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <article data-testid="s2p-authority-panel" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Authority advancement</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Earned authority controls</h2>
        </div>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase text-amber-800">
          {loading ? "loading" : label(record?.current_stage)}
        </span>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_1fr]">
        <label className="text-sm font-medium text-slate-700">
          Category
          <select
            value={record?.decision_class ?? selected}
            onChange={(event) => setSelected(event.target.value)}
            className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            {records.map((item) => (
              <option key={item.decision_class} value={item.decision_class}>
                {label(item.decision_class)}
              </option>
            ))}
          </select>
        </label>
        <Metric label="Next stage" value={target} />
        <Metric label="Conservation" value={state} />
        <Metric label="Shadow decisions" value={loading ? "Loading..." : record ? String(record.shadow_decisions ?? 0) : "Unavailable"} />
        <Metric label="Measured decisions" value={loading ? "Loading..." : record ? String(record.measurement_decisions ?? 0) : "Unavailable"} />
        <Metric label="Improvement" value={loading ? "Loading..." : record ? String(record.improvement_delta ?? 0) : "Unavailable"} />
      </div>
      {!loading && records.length === 0 ? (
        <p className="mt-3 text-sm text-slate-600">No authority records available</p>
      ) : null}
      {!loading && record && (record.shadow_decisions ?? 0) === 0 ? (
        <p className="mt-3 text-sm text-slate-600">No shadow decisions yet</p>
      ) : null}
      {error ? <p className="mt-3 text-sm text-rose-600">{error}</p> : null}
      <div className="mt-4 grid gap-2">
        {checks.map((check) => (
          <div key={check.label} className="flex items-center justify-between rounded-md border border-slate-200 bg-white p-3 text-sm">
            <span>{check.label}</span>
            <span className={check.met ? "font-semibold text-emerald-700" : "font-semibold text-amber-700"}>
              {check.met ? "Met" : "Unmet"}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={advance}
          disabled={!canAdvance || busy || loading}
          className="rounded-md bg-amber-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {busy ? "Advancing..." : "Advance"}
        </button>
        {notice ? <span className="text-sm text-slate-600">{notice}</span> : null}
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}
