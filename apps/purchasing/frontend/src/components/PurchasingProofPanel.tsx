import { useEffect, useState } from "react";
import { BASE } from "../api";

type RecordValue = Record<string, unknown>;

async function read(path: string): Promise<RecordValue> {
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) throw new Error(`${response.status}`);
  return (await response.json()) as RecordValue;
}

function text(value: unknown, fallback = "—"): string {
  return value === undefined || value === null || value === "" ? fallback : String(value);
}

export default function PurchasingProofPanel() {
  const [proof, setProof] = useState<RecordValue | null>(null);
  const [readiness, setReadiness] = useState<RecordValue | null>(null);
  const [legal, setLegal] = useState<RecordValue | null>(null);
  const [twin, setTwin] = useState<RecordValue | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      read("/api/purchasing/proof-ledger"),
      read("/api/purchasing/day-0-readiness"),
      read("/api/purchasing/legal-exposure"),
      read("/api/purchasing/frozen-twin"),
    ]).then(([nextProof, nextReadiness, nextLegal, nextTwin]) => {
      if (active) {
        setProof(nextProof);
        setReadiness(nextReadiness);
        setLegal(nextLegal);
        setTwin(nextTwin);
      }
    }).catch(() => undefined);
    return () => { active = false; };
  }, []);

  const curve = (proof?.proofCurve ?? {}) as RecordValue;
  const competence = (proof?.competenceCurve ?? {}) as RecordValue;
  return (
    <section data-testid="purchasing-proof-panel" className="purchase-card">
      <p className="purchase-kicker">Proof of learning</p>
      <h2 className="purchase-section-title">Proof Ledger</h2>
      <p className="purchase-muted">Verified outcomes only; synthetic uplift is not attributed.</p>
      <div className="purchase-grid purchase-grid--three">
        <div><strong>{text(curve.decisions, "0")}</strong><span> decisions</span></div>
        <div><strong>{text(curve.verified, "0")}</strong><span> verified</span></div>
        <div><strong>{text(competence.accuracy, "0")}</strong><span> measured accuracy</span></div>
      </div>
      <div className="purchase-grid purchase-grid--three">
        <div><strong>Evidence: {text(proof?.evidenceTier, "T_S")}</strong><span> {text(proof?.evidenceLabel, "synthetic / modelled — not measured")}</span></div>
        <div><strong>Day-0 Readiness</strong><span> {readiness?.ready ? "READY" : "NOT_YET"}</span></div>
        <div><strong>Legal exposure</strong><span> {text(legal?.complianceStatus, "REVIEW_REQUIRED")}</span></div>
      </div>
      <p className="purchase-muted">Frozen Twin: {text(twin?.status, "NOT_INITIALIZED")} · Handoff: evidence chain exportable · Observation-only boundary preserved.</p>
    </section>
  );
}
