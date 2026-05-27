"""Read-only transfer detection from copilot fingerprint files."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Mapping


LEARNED_SIGMA_THRESHOLD = 0.15
UNLEARNED_SIGMA_THRESHOLD = 0.30


def fingerprint_dir(base_path: Path | str | None = None) -> Path:
    if base_path is not None:
        return Path(base_path)
    return Path(__file__).resolve().parents[1] / "data" / "fingerprints"


def save_fingerprint(
    domain: str,
    fingerprint_data: Mapping[str, Any],
    base_path: Path | str | None = None,
    *,
    source_url: str | None = None,
) -> Path:
    normalized_domain = _safe_domain(domain)
    directory = fingerprint_dir(base_path)
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "domain": normalized_domain,
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fingerprint": _json_safe(dict(fingerprint_data)),
    }
    if source_url:
        payload["source_url"] = str(source_url)
    path = directory / f"{normalized_domain}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_fingerprints(base_path: Path | str | None = None) -> dict[str, Any]:
    loaded, _warnings = load_fingerprints_with_warnings(base_path)
    return loaded


def load_fingerprints_with_warnings(
    base_path: Path | str | None = None,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    directory = fingerprint_dir(base_path)
    if not directory.exists():
        return {}, []

    loaded: dict[str, Any] = {}
    warnings: list[dict[str, str]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append({"file": path.name, "warning": f"skipped malformed fingerprint: {exc}"})
            continue
        if not isinstance(payload, dict):
            warnings.append({"file": path.name, "warning": "skipped non-object fingerprint"})
            continue
        domain = _safe_domain(payload.get("domain") or path.stem)
        loaded[domain] = payload
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
