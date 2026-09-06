import { useEffect, useState } from "react";

export interface CentroidTimelinePanelProps { baseUrl?: string; }

export default function CentroidTimelinePanel({ baseUrl = "/api/self" }: CentroidTimelinePanelProps) {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => {
    setLoading(true);
    setError(false);
    fetch(`${baseUrl}/centroid-timeline`, { signal: AbortSignal.timeout(10_000) })
      .then((response) => {
        if (!response.ok) throw new Error("Centroid timeline unavailable");
        return response.json();
      })
      .then((value: { checkpoints?: unknown }) => {
        setRows(Array.isArray(value.checkpoints) ? value.checkpoints.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null) : []);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [baseUrl]);
  return <section data-testid="centroid-timeline-panel" data-panel-ready={String(!loading)} className="copilot-card p-4"><h2 className="text-base font-semibold">Centroid Timeline</h2><p className="text-sm">Centroid evolution across verified decisions.</p><div>{error ? "Centroid timeline unavailable" : `${rows.length} checkpoints`}</div></section>;
}
