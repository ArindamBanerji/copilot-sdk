import { useEffect, useMemo, useState } from "react";
import type { PatternDetectionResponse } from "../types";

const PATTERN_URL = "http://localhost:8010/api/context/patterns";

function patternLabel(name: string): string {
  return name
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function PatternBadge() {
  const [data, setData] = useState<PatternDetectionResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(PATTERN_URL)
      .then((response) => (response.ok ? response.json() : null))
      .then((payload: PatternDetectionResponse | null) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const patterns = data?.patterns ?? [];
  const count = data?.totalPatternsDetected ?? patterns.length;
  const topPattern = useMemo(
    () => [...patterns].sort((left, right) => Number(right.severity ?? 0) - Number(left.severity ?? 0))[0],
    [patterns],
  );

  if (!data || count <= 0) {
    return null;
  }

  const isActive = patterns.some((pattern) => Number(pattern.severity ?? 0) >= 0.5);
  const tone = isActive
    ? "border-rose-400/40 bg-rose-500/15 text-rose-100"
    : "border-amber-300/40 bg-amber-300/10 text-amber-100";
  const topLabel = topPattern?.displayName || (topPattern?.name ? patternLabel(topPattern.name) : "Review pattern");

  return (
    <div
      className={`inline-flex max-w-full flex-col rounded-md border px-3 py-2 text-sm ${tone}`}
      title={topPattern?.description || topLabel}
      aria-label={`${count} trading patterns detected`}
    >
      <span className="font-semibold">{count} pattern{count === 1 ? "" : "s"} detected</span>
      <span className="mt-0.5 truncate text-xs opacity-80">Top: {topLabel}</span>
    </div>
  );
}
