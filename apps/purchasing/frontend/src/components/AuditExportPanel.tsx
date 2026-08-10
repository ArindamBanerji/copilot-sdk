import { useEffect, useState } from "react";
import { BASE } from "../api";

type AuditPack = {
  period?: string;
  total_decisions?: number;
  total_overrides?: number;
  override_rate?: number;
  narrative?: string;
  sections?: {
    conservation_proof?: { status?: string };
    hash_chain_verification?: { verified?: boolean; hash?: string };
  };
};

export default function AuditExportPanel() {
  const [pack, setPack] = useState<AuditPack | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const response = await fetch(`${BASE}/api/purchasing/audit/pack`);
        if (!response.ok) throw new Error("Purchasing backend unavailable");
        const payload = (await response.json()) as AuditPack;
        if (mounted) setPack(payload);
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "Purchasing backend unavailable");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <section className="purchase-card" data-panel-ready="false">
        <p className="purchase-kicker">Quarterly review</p>
        <h2 className="purchase-title">Audit &amp; Compliance Pack</h2>
        <p>Loading audit pack...</p>
      </section>
    );
  }
  if (error) {
    return (
      <section className="purchase-card error-card" data-panel-ready="true">
        <p className="purchase-kicker">Audit pack unavailable</p>
        <h2 className="purchase-title">Audit &amp; Compliance Pack</h2>
        <p>{error}</p>
      </section>
    );
  }

  const proof = pack?.sections?.conservation_proof;
  const hash = pack?.sections?.hash_chain_verification;
  return (
    <section className="purchase-card" data-panel-ready="true">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Quarterly review</p>
          <h2 className="purchase-title">Audit &amp; Compliance Pack</h2>
        </div>
        <span className="pill">{proof?.status ?? "pending"}</span>
      </div>
      <p className="purchase-muted">{pack?.narrative}</p>
      <div className="stats-row">
        <div><span>Total decisions</span><strong>{pack?.total_decisions ?? 0}</strong></div>
        <div><span>Overrides</span><strong>{pack?.total_overrides ?? 0}</strong></div>
        <div><span>Override rate</span><strong>{(Number(pack?.override_rate ?? 0) * 100).toFixed(1)}%</strong></div>
        <div><span>Hash chain</span><strong>{hash?.verified ? "verified" : "pending"}</strong></div>
      </div>
      <p className="mt-3 text-sm">Hash proof: {hash?.hash ?? "pending"}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <a className="rounded-md border px-3 py-2 text-sm font-semibold" href={`${BASE}/api/purchasing/audit/export/json`}>Download JSON</a>
        <a className="rounded-md border px-3 py-2 text-sm font-semibold" href={`${BASE}/api/purchasing/audit/export/csv`}>Download CSV</a>
      </div>
    </section>
  );
}
