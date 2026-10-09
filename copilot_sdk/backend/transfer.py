"""Transfer detection and fingerprint persistence through GraphStore."""

from __future__ import annotations

import math
import time
from uuid import uuid4
from typing import Any, Mapping

from copilot_sdk.graph.protocol import ProtocolV2GraphStore


LEARNED_SIGMA_THRESHOLD = 0.15
UNLEARNED_SIGMA_THRESHOLD = 0.30


def save_fingerprint(
    domain: str,
    fingerprint_data: Mapping[str, Any],
    *,
    graph_store: ProtocolV2GraphStore,
    source_url: str | None = None,
) -> str:
    normalized_domain = _safe_domain(domain)
    fingerprint = _json_safe(dict(fingerprint_data))
    fingerprint_id = f"exported-fingerprint:{normalized_domain}:{uuid4().hex}"
    graph_store.write_fingerprint(
        fingerprint_id=fingerprint_id, domain=normalized_domain,
        factor_names=list(fingerprint.get("factor_names", [])),
        factor_stats=fingerprint,
        skipped_incompatible=int(fingerprint.get("skipped_incompatible", 0)),
        window=int(fingerprint.get("window", 0)),
        metadata={"source_url": source_url, "provenance": "graph",
                  "exported_at": time.time(), "export_tick": time.perf_counter_ns()},
    )
    return fingerprint_id


def load_fingerprints(*, graph_store: ProtocolV2GraphStore) -> dict[str, Any]:
    loaded, warnings = load_fingerprints_with_warnings(graph_store=graph_store)
    if warnings:
        raise ValueError(f"Invalid graph fingerprints: {warnings}")
    return loaded


def load_fingerprints_with_warnings(
    *, graph_store: ProtocolV2GraphStore,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    loaded: dict[str, Any] = {}
    warnings: list[dict[str, str]] = []
    # High-resolution ticks retain publication order when epoch clocks tie.
    # The ID makes legacy records without ticks deterministic as well.
    for payload in sorted(graph_store.list_fingerprints(), key=lambda row: (
        float((row.get("metadata") or {}).get("exported_at", 0.0)),
        int((row.get("metadata") or {}).get("export_tick", 0)),
        str(row.get("fingerprint_id", "")),
    )):
        domain = str(payload.get("domain") or "").strip()
        if not domain or not isinstance(payload.get("fingerprint"), dict):
            warnings.append({"fingerprint_id": str(payload.get("fingerprint_id", "")),
                             "warning": "invalid graph fingerprint: domain and fingerprint mapping required"})
            continue
        loaded[_safe_domain(domain)] = dict(payload)
    return loaded, warnings


class TransferDetector:
    def __init__(
        self,
        *,
        source_sigma_max: float = LEARNED_SIGMA_THRESHOLD,
        target_sigma_min: float = UNLEARNED_SIGMA_THRESHOLD,
    ) -> None:
        self.source_sigma_max = float(source_sigma_max)
        self.target_sigma_min = float(target_sigma_min)

    def detect(
        self,
        own_fingerprint: Mapping[str, Any] | None,
        other_fingerprints: Mapping[str, Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        fingerprints: dict[str, Mapping[str, Any]] = {}
        if own_fingerprint:
            own_domain = _fingerprint_domain(own_fingerprint, "own")
            fingerprints[own_domain] = own_fingerprint
        for fallback_domain, fingerprint in sorted(other_fingerprints.items()):
            if isinstance(fingerprint, Mapping):
                fingerprints[_fingerprint_domain(fingerprint, fallback_domain)] = fingerprint
        return detect_transfer_opportunities(
            fingerprints,
            source_sigma_max=self.source_sigma_max,
            target_sigma_min=self.target_sigma_min,
        )


def detect_transfer_opportunities(
    fingerprints: Mapping[str, Mapping[str, Any]],
    *,
    source_sigma_max: float = LEARNED_SIGMA_THRESHOLD,
    target_sigma_min: float = UNLEARNED_SIGMA_THRESHOLD,
) -> list[dict[str, Any]]:
    sigma_by_domain = {
        _safe_domain(domain): _factor_sigma_map(fingerprint)
        for domain, fingerprint in fingerprints.items()
        if isinstance(fingerprint, Mapping)
    }
    opportunities: list[dict[str, Any]] = []
    for source_domain in sorted(sigma_by_domain):
        source_sigmas = sigma_by_domain[source_domain]
        for target_domain in sorted(sigma_by_domain):
            if source_domain == target_domain:
                continue
            target_sigmas = sigma_by_domain[target_domain]
            for factor in sorted(set(source_sigmas) & set(target_sigmas)):
                source_sigma = source_sigmas[factor]
                target_sigma = target_sigmas[factor]
                if source_sigma < source_sigma_max and target_sigma > target_sigma_min:
                    opportunities.append(
                        {
                            "source_domain": source_domain,
                            "target_domain": target_domain,
                            "factor": factor,
                            "source_sigma": source_sigma,
                            "target_sigma": target_sigma,
                            "direction": f"{source_domain}->{target_domain}",
                            "recommendation": "warm_start_factor",
                            "reason": (
                                f"{source_domain} has learned {factor} "
                                f"while {target_domain} remains noisy"
                            ),
                        }
                    )
    return opportunities


def _fingerprint_domain(fingerprint: Mapping[str, Any], fallback: str) -> str:
    return _safe_domain(fingerprint.get("domain") or fallback)


def _safe_domain(value: Any) -> str:
    domain = str(value or "").strip().lower()
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in domain) or "unknown"


def _factor_sigma_map(fingerprint: Mapping[str, Any]) -> dict[str, float]:
    payload = fingerprint.get("fingerprint")
    if not isinstance(payload, Mapping):
        payload = fingerprint
    factors = payload.get("factors") if isinstance(payload, Mapping) else None
    if not isinstance(factors, list):
        return {}
    sigmas: dict[str, float] = {}
    for factor in factors:
        if not isinstance(factor, Mapping):
            continue
        name = str(factor.get("name") or "").strip()
        sigma = _finite_float(factor.get("sigma"))
        if name and sigma is not None:
            sigmas[name] = sigma
    return sigmas


def _finite_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return round(numeric, 6)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value
