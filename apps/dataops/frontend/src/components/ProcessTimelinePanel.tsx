import { useEffect, useMemo, useState } from "react";
import { fetchProcessData } from "../api";
import type { ProcessActivity, ProcessData } from "../types";
import { CelonisBadge } from "./CelonisBadge";
import { SAPDataBadge } from "./SAPDataBadge";

function activityName(activity: ProcessActivity) {
  return activity.name ?? activity.activity ?? "Process activity";
}

function activityDuration(activity: ProcessActivity) {
  return activity.durationHours ?? activity.avgDurationHours ?? 0;
}

function isBottleneck(activity: ProcessActivity) {
  return activity.bottleneck === true || /match invoice to gr/i.test(activityName(activity));
}

export function ProcessTimelinePanel() {
  const [processData, setProcessData] = useState<ProcessData | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchProcessData().then((data) => {
      if (!cancelled) {
        setProcessData(data);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const activities = processData?.activities ?? [];
  const maxDuration = useMemo(
    () => Math.max(1, ...activities.map((activity) => activityDuration(activity))),
    [activities]
  );
  const live = `${processData?.source ?? ""}`.toLowerCase().includes("live");

  return (
    <section className="rounded-md border border-white/10 bg-white/[0.04] p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-purple-200/75">
            Process Timeline
          </p>
          <h2 className="mt-1 text-xl font-semibold text-white">
            {processData?.processModel ?? "Purchase-to-Pay"}
          </h2>
          <p className="mt-1 text-sm text-slate-300">
            {processData?.variant ?? "Standard variant"} · {processData?.totalCases ?? 0} cases ·{" "}
            {processData?.variantFrequency ?? 0} variant frequency
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <CelonisBadge
            kmName={processData?.processModel}
            variantCount={processData?.variantFrequency}
            live={live}
          />
          <SAPDataBadge variantText={processData?.variant} />
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {activities.length === 0 ? (
          <p className="text-sm text-slate-400">Process activity data is loading from cache.</p>
        ) : (
          activities.map((activity, index) => {
            const duration = activityDuration(activity);
            const bottleneck = isBottleneck(activity);
            const width = Math.max(8, Math.round((duration / maxDuration) * 100));

            return (
              <div
                key={`${activityName(activity)}-${index}`}
                className="grid gap-2 md:grid-cols-[190px_1fr_92px] md:items-center"
              >
                <div>
                  <p className="text-sm font-medium text-white">{activityName(activity)}</p>
                  {bottleneck ? (
                    <p className="text-xs text-amber-200">
                      bottleneck {activity.bottleneckCause ? `· ${activity.bottleneckCause}` : ""}
                    </p>
                  ) : null}
                </div>
                <div className="h-3 rounded-md bg-slate-800">
                  <div
                    className={`h-3 rounded-md ${bottleneck ? "bg-amber-400" : "bg-purple-400"}`}
                    style={{ width: `${width}%` }}
                  />
                </div>
                <p className="text-right text-sm text-slate-300">{duration.toFixed(1)}h</p>
              </div>
            );
          })
        )}
      </div>

      <div className="mt-5 rounded-md border border-amber-300/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
        Match Invoice to GR bottleneck: $8,400/day processing cost at this rate.
      </div>
    </section>
  );
}
