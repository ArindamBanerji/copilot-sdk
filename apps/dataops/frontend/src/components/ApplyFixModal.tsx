import { useEffect, useRef, useState } from "react";
import { applyFix } from "../api";
import type { ApplyFixConservationCheck, ApplyFixRequest, ApplyFixResponse } from "../types";

interface ApplyFixModalProps {
  open: boolean;
  alertId: string;
  option: string;
  optionLabel: string;
  entityId: string;
  supplier: string;
  matchingParameter: string;
  conservationPreview: ApplyFixConservationCheck;
  onClose: () => void;
  onApplied: (response: ApplyFixResponse, alertId: string) => void;
}

export default function ApplyFixModal({
  open,
  alertId,
  option,
  optionLabel,
  entityId,
  supplier,
  matchingParameter,
  conservationPreview,
  onClose,
  onApplied,
}: ApplyFixModalProps) {
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<ApplyFixResponse | null>(null);
  const currentAlertIdRef = useRef(alertId);

  useEffect(() => {
    currentAlertIdRef.current = alertId;
    setApplying(false);
    setError(null);
    setResponse(null);
  }, [alertId]);

  if (!open) {
    return null;
  }

  const conservation = response?.conservationCheck || conservationPreview;

  async function handleApply() {
    const requestAlertId = alertId;
    const request: ApplyFixRequest = {
      alertId: requestAlertId,
      option,
      optionLabel,
      entityType: "PurchaseOrder",
      entityId,
      payload: {
        matchingParameter,
      },
    };

    setApplying(true);
    setError(null);
    try {
      const result = await applyFix(request);
      if (currentAlertIdRef.current !== requestAlertId) {
        return;
      }
      setResponse(result);
      onApplied(result, requestAlertId);
    } catch (caught) {
      if (currentAlertIdRef.current === requestAlertId) {
        setError(caught instanceof Error ? caught.message : "Could not apply fix.");
      }
    } finally {
      if (currentAlertIdRef.current === requestAlertId) {
        setApplying(false);
      }
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="presentation">
      <section
        className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-md border p-5 shadow-xl"
        style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="apply-fix-title"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
              SAP Write-back
            </p>
            <h2 id="apply-fix-title" className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
              Apply Fix to SAP S/4HANA
            </h2>
            <p className="mt-1 text-sm dataops-muted">Fixture-backed write simulation for alert {alertId}.</p>
          </div>
          <button type="button" className="copilot-button-secondary px-3 py-2 text-sm" onClick={onClose}>
            Close
          </button>
        </div>

        {response ? (
          <div className="mt-5 rounded-md border p-4" style={{ borderColor: "var(--copilot-success)", background: "rgba(34, 197, 94, 0.10)" }}>
            <div className="text-sm font-semibold" style={{ color: "var(--copilot-success)" }}>
              Applied to SAP S/4HANA.
            </div>
            <p className="mt-2 text-sm dataops-muted">
              {response.optionLabel || optionLabel} applied to {response.sapResponse?.d?.PurchaseOrder || entityId}.
            </p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              <Metric label="Status" value={response.sapResponse?.d?.Status || response.status || "applied"} />
              <Metric label="Estimated savings" value={response.estimatedSavings || "pending"} />
            </div>
            <button type="button" className="copilot-button mt-4 px-3 py-2 text-sm" onClick={onClose}>
              Done
            </button>
          </div>
        ) : (
          <>
            <div className="mt-5 grid gap-3">
              <Metric label="Option" value={`${option}: ${optionLabel}`} />
              <Metric label="Target" value={`${entityId} / ${supplier}`} />
              <Metric label="Parameter" value={`matching_parameter -> ${matchingParameter}`} />
            </div>

            <div className="mt-5 rounded-md border p-4" style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface-muted)" }}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.16em] dataops-muted">Conservation Check</div>
                  <p className="mt-1 text-sm dataops-muted">Caller-visible safety preview before fixture write-back.</p>
                </div>
                <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "rgba(34, 197, 94, 0.12)", color: "var(--copilot-success)" }}>
                  {conservation.status || "pending"}
                </span>
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-4">
                <Metric label="Current automation" value={formatPercent(conservation.currentAutomation)} />
                <Metric label="Projected automation" value={formatPercent(conservation.projectedAutomation)} />
                <Metric label="Theta min" value={formatDecimal(conservation.thetaMin)} />
                <Metric label="Safe" value={conservation.safe ? "true" : "false"} />
              </div>
            </div>

            {error ? <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}

            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <button type="button" className="copilot-button-secondary px-3 py-2 text-sm" onClick={onClose} disabled={applying}>
                Cancel
              </button>
              <button type="button" className="copilot-button px-3 py-2 text-sm" onClick={handleApply} disabled={applying || conservation.safe !== true}>
                {applying ? "Applying..." : "Apply to SAP"}
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}>
      <div className="text-xs font-semibold uppercase dataops-muted">{label}</div>
      <div className="mt-1 text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</div>
    </div>
  );
}

function formatPercent(value?: number) {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "pending";
}

function formatDecimal(value?: number) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "pending";
}
