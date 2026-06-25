import { useEffect, useState } from "react";
import { fetchDiscoveryDigest, fetchDiscoveryInsights, type DiscoveryInsight } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

export default function DiscoveryDigestCard() {
  const [insights, setInsights] = useState<DiscoveryInsight[]>([]);
  const [digest, setDigest] = useState<string[]>([]);
  const [provenance, setProvenance] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [nextInsights, nextDigest] = await Promise.all([fetchDiscoveryInsights(), fetchDiscoveryDigest()]);
        if (mounted) {
          setInsights(nextInsights.insights ?? []);
          setDigest(nextDigest.digest ?? []);
          setProvenance(nextInsights.provenance ?? nextDigest.provenance);
        }
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "Not enough decisions for cross-category analysis");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Cross-Category Intelligence</p>
          <h2 className="purchase-title">Weekly patterns across the kitchen</h2>
        </div>
        <ProvenanceBadge source={provenance === "demo" ? "sample" : provenance} />
      </div>
      {loading ? <p className="purchase-muted">Looking for linked kitchen patterns...</p> : null}
      {error ? <p className="purchase-muted">{error}</p> : null}
      {!loading && !error && insights.length === 0 ? <p className="purchase-muted">Not enough decisions for cross-category analysis</p> : null}
      {insights.length > 0 ? (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {insights.slice(0, 3).map((insight) => (
              <div key={insight.title} className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
                <div className="purchase-muted text-sm">{insight.strength ?? "early"} pattern</div>
                <strong>{insight.title}</strong>
                <p className="purchase-muted mt-1 text-sm">{insight.explanation}</p>
                <p className="mt-2 text-sm font-semibold">{insight.suggestedAction}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
            <strong>Weekly digest</strong>
            <ul className="purchase-muted mt-2 list-disc pl-5 text-sm">
              {(digest.length ? digest : insights.map((item) => item.explanation ?? "")).slice(0, 3).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        </>
      ) : null}
    </section>
  );
}
