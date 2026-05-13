import { useEffect, useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchS2PTrajectory } from "../api";
import type { PerformanceTrajectoryResponse } from "../types";

export function TrajectoryChart() {
  const [data, setData] = useState<PerformanceTrajectoryResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchS2PTrajectory().then((response) => {
      if (!cancelled) setData(response);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const points = (data?.points ?? []).map((point, index) => ({
    index: index + 1,
    q: data?.current_q ?? data?.currentQ ?? 0,
    category: point.category ?? "checkpoint",
  }));

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Learning trajectory</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Centroid checkpoints</h2>
      {points.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No centroid trajectory yet. Score and verify invoices to see learning.</p>
      ) : (
        <div className="mt-5 h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points}>
              <XAxis dataKey="index" tickLine={false} />
              <YAxis domain={[0, 1]} tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} />
              <Tooltip formatter={(value) => `${Math.round(Number(value) * 100)}%`} />
              <Line type="monotone" dataKey="q" stroke="#d97706" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </article>
  );
}
