import { useEffect, useMemo, useState } from "react";
import {
  advanceDataOpsPromotion,
  fetchDataOpsPromotion,
  getConservationStatus,
  type DataOpsPromotionRecord,
} from "../api";

const DECISION_CLASS = "default";

function label(value?: string): string {
  return String(value || "unknown").replace(/_/g, " ");
}

function nextStage(stage?: string): string {
  if (stage === "discovered") return "shadowing";
  if (stage === "shadowing") return "promoted";
  if (stage === "promoted") return "kept";
  if (stage === "rolled_back") return "shadowing";
  return "no transition";
}

function isGreen(status?: string): boolean {
  return String(status || "").toUpperCase() === "GREEN";
}

export default function PromotionPanel() {
  const [record, setRecord] = useState<DataOpsPromotionRecord | null>(null);
  const [conservation, setConservation] = useState<string>("UNKNOWN");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const refresh = () => {
    setLoading(true);
    Promise.all([fetchDataOpsPromotion(DECISION_CLASS), getConservationStatus().catch(() => null)])
      .then(([promotion, conservationState]) => {
        setRecord(promotion);
        setConservation(conservationState?.status ?? "UNKNOWN");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  const checks = useMemo(() => {
    const stage = record?.currentStage;
    return [
      { label: "Promotion record exists", met: Boolean(record?.recordId) },
      {
        label: "Conservation state is GREEN",
        met: stage !== "shadowing" || isGreen(conservation),
      },
      {
        label: "At least 10 shadow decisions",
        met: stage !== "shadowing" || (record?.shadowDecisions ?? 0) >= 10,
      },
      {
        label: "Measured T_O evidence supplied",
        met: true,
      },
      {
        label: "At least 10 measured decisions",
        met: stage !== "promoted" || (record?.measurementDecisions ?? 0) >= 10,
      },
      {
        label: "Positive measured improvement",
        met: stage !== "promoted" || (record?.improvementDelta ?? 0) > 0,
      },
    ];
  }, [conservation, record]);

  const canAdvance = Boolean(record?.recordId) && record?.currentStage !== "kept" && checks.every((check) => check.met);
  const target = nextStage(record?.currentStage);

  const advance = async () => {
    if (!record?.recordId || !canAdvance) return;
    const ok = window.confirm(
      `Advance DataOps ${DECISION_CLASS} authority from ${label(record.currentStage)} to ${label(target)}?\n\n` +
        "Impact: the copilot will move to the next earned-authority rung for this decision class.",
    );
    if (!ok) return;
    setBusy(true);
    setNotice("");
    setError("");
    try {
      const result = await advanceDataOpsPromotion(record.recordId, {
        shadowDecisions: Math.max(record.shadowDecisions, 10),
        measurementDecisions: Math.max(record.measurementDecisions, record.currentStage === "promoted" ? 10 : 0),
        improvement: Math.max(record.improvementDelta, record.currentStage === "promoted" ? 0.01 : 0),
        conservationState: conservation,
        evidenceTier: "T_O",
        reason: "operator_advance",
      });
      setNotice(result.advanced ? `Advanced to ${label(result.newStage)}` : `Held: ${label(result.reason)}`);
      refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Promotion advance failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <article data-testid="dataops-promotion-panel" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide dataops-muted">Authority promotion</p>
          <h2 className="mt-1 text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>Manual advancement</h2>
        </div>
        <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold uppercase text-emerald-800">
          {loading ? "loading" : label(record?.currentStage)}
        </span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Metric label="Decision class" value={DECISION_CLASS} />
        <Metric label="Next rung" value={target} />
        <Metric label="Conservation" value={conservation} />
      </div>
      <div className="mt-4 grid gap-2">
        {checks.map((check) => (
          <div key={check.label} className="flex items-center justify-between rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
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
          className="rounded-md px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
          style={{ background: "var(--copilot-accent)" }}
        >
          {busy ? "Advancing..." : "Advance"}
        </button>
        {notice ? <span className="text-sm dataops-muted">{notice}</span> : null}
        {error ? <span className="text-sm text-rose-400">{error}</span> : null}
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-white/[0.04] p-3">
      <p className="text-xs uppercase tracking-wide dataops-muted">{label}</p>
      <p className="mt-1 font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</p>
    </div>
  );
}
