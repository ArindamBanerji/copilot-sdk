"""Process-mining export ingestion utilities."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class _ActivityStats:
    activity: str
    resource: str | None
    count: int
    total_duration_ms: float

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / max(self.count, 1)


class ProcessExportIngester:
    """Ingest process-mining export into the S2P context graph."""

    def ingest(self, export_data: list[dict]) -> dict:
        """Map process events to context graph entities."""

        events = [_normalize_event(event) for event in export_data if isinstance(event, dict)]
        cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
        activities: Counter[str] = Counter()
        resources: Counter[str] = Counter()
        variants: Counter[str] = Counter()
        activity_resource: dict[tuple[str, str | None], list[float]] = defaultdict(list)

        for event in events:
            case_id = event["case_id"]
            cases[case_id].append(event)
            activities[event["activity"]] += 1
            if event["resource"]:
                resources[event["resource"]] += 1
            if event["variant"]:
                variants[event["variant"]] += 1
            activity_resource[(event["activity"], event["resource"])].append(event["duration_ms"])

        bottlenecks = sorted(
            (
                _ActivityStats(
                    activity=activity,
                    resource=resource,
                    count=len(durations),
                    total_duration_ms=sum(durations),
                )
                for (activity, resource), durations in activity_resource.items()
            ),
            key=lambda item: (item.avg_duration_ms, item.total_duration_ms),
            reverse=True,
        )[:3]

        relationships = []
        for case_id, case_events in cases.items():
            ordered = sorted(case_events, key=lambda item: item["timestamp"])
            for event in ordered:
                relationships.append(
                    {
                        "from": f"process_instance:{case_id}",
                        "to": f"activity:{event['activity']}",
                        "type": "HAS_ACTIVITY",
                    }
                )
                if event["resource"]:
                    relationships.append(
                        {
                            "from": f"activity:{event['activity']}",
                            "to": f"resource:{event['resource']}",
                            "type": "PERFORMED_BY",
                        }
                    )

        return {
            "cases_ingested": len(cases),
            "activities_found": len(activities),
            "resources_found": len(resources),
            "events_ingested": len(events),
            "bottleneck_activities": [
                {
                    "activity": item.activity,
                    "resource": item.resource,
                    "count": item.count,
                    "avg_duration_ms": round(item.avg_duration_ms, 4),
                    "avg_duration_hours": round(item.avg_duration_ms / 3_600_000.0, 4),
                    "total_duration_ms": round(item.total_duration_ms, 4),
                }
                for item in bottlenecks
            ],
            "variant_distribution": dict(sorted(variants.items())),
            "context_graph": {
                "entities": {
                    "process_instances": sorted(cases),
                    "activities": sorted(activities),
                    "resources": sorted(resources),
                },
                "relationships": relationships,
            },
            "provenance": "scraped_external",
        }


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    case_id = _text(event.get("case_id") or event.get("caseId") or event.get("case"))
    activity = _text(event.get("activity") or event.get("activity_name") or event.get("activityName"))
    return {
        "case_id": case_id or "unknown-case",
        "activity": activity or "unknown-activity",
        "timestamp": _text(event.get("timestamp") or event.get("time") or ""),
        "resource": _optional_text(event.get("resource") or event.get("team") or event.get("owner")),
        "duration_ms": _duration_ms(event.get("duration_ms", event.get("durationMs", 0.0))),
        "variant": _optional_text(event.get("variant")),
        "cost": _optional_number(event.get("cost")),
    }


def _text(value: Any) -> str:
    return str(value or "").strip()


def _optional_text(value: Any) -> str | None:
    text = _text(value)
    return text or None


def _duration_ms(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(parsed, 0.0)


def _optional_number(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed
