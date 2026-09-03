import { useEffect, useState } from "react";

export interface CentroidTimelinePanelProps { baseUrl?: string; }

export default function CentroidTimelinePanel({ baseUrl = "/api/self" }: CentroidTimelinePanelProps) {
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  useEffect(() => {
    fetch(`${baseUrl}/centroid-timeline`)
      .then((response) => response.json())
      .then((value: { checkpoints?: unknown }) => {
        setRows(Array.isArray(value.checkpoints) ? value.checkpoints.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null) : []);
      });
  }, [baseUrl]);
  return <section data-testid="centroid-timeline-panel" className="copilot-card p-4"><h2 className="text-base font-semibold">Centroid Timeline</h2><p className="text-sm">Centroid evolution across verified decisions.</p><div>{rows.length} checkpoints</div></section>;
}
