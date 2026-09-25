"""VLD investigation primitives for score-conditioned evidence reads."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable, Optional, Protocol, runtime_checkable

import numpy as np
from copilot_sdk.config.graph_config import resolve_profile


@dataclass
class InvestigationStep:
    step: int
    dimension: int
    factor_name: str
    evidence_value: float | None
    evidence_confidence: float
    evidence_source: str
    v_before: list[float]
    v_after: list[float]
    action_before: int
    action_after: int
    margin_before: float
    margin_after: float
    flipped: bool
    status: str = "acquired"
    halt_reason: str | None = None


@dataclass
class EpisodeSnapshot:
    centroids: np.ndarray
    sigma: np.ndarray
    tau: float
    k_weights: np.ndarray | None
    factor_names: list[str]
    action_names: list[str]
    category: str
    geometry_hash: str
    conservation_status: str
    timestamp: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "geometry_hash": self.geometry_hash,
            "tau": self.tau,
            "k_weights": None if self.k_weights is None else self.k_weights.tolist(),
            "factor_names": list(self.factor_names),
            "action_names": list(self.action_names),
            "category": self.category,
            "conservation_status": self.conservation_status,
            "timestamp": self.timestamp,
        }


@dataclass
class InvestigationTrace:
    decision_id: str
    category: str
    budget: int
    steps: list[InvestigationStep]
    surface_action: int
    surface_margin: float
    final_action: int
    final_margin: float
    snapshot: EpisodeSnapshot | None = None
    contrast: dict[str, Any] | None = None
    halt_reason: str | None = None


@runtime_checkable
class EvidenceProvider(Protocol):
    def read_evidence(
        self, decision_id: str, dimension: int, factor_name: str
    ) -> Optional[dict[str, Any]]:
        """Return {value, confidence, source} for one dimension, or None."""
        ...


class VLDInvestigator:
    """Read-only VLD loop over action centroids and per-dimension sigma."""

    def __init__(self, mu: Any, sigma: Any, factor_names: list[str], tau: float = 0.1, action_names: list[str] | None = None):
        self.mu = np.asarray(mu, dtype=np.float64).copy()
        if self.mu.ndim != 2:
            raise ValueError("VLDInvestigator mu must have shape (actions, factors)")
        self.sigma = np.asarray(sigma, dtype=np.float64).copy()
        if self.sigma.shape != (self.mu.shape[1],):
            raise ValueError(f"sigma shape {self.sigma.shape} != ({self.mu.shape[1]},)")
        if len(factor_names) != self.mu.shape[1]:
            raise ValueError("factor_names length must match centroid factor dimension")
        if tau <= 0:
            raise ValueError("tau must be positive")
        self.factor_names = list(factor_names)
        self.action_names = list(action_names or [f"action_{i}" for i in range(self.mu.shape[0])])
        if len(self.action_names) != self.mu.shape[0]:
            raise ValueError("action_names length must match centroid action dimension")
        self.tau = float(tau)

    def score(self, v: np.ndarray) -> tuple[int, np.ndarray]:
        vector = self._vector(v)
        precision = 1.0 / np.maximum(self.sigma**2, 0.001)
        dists = np.sum(precision.reshape(1, -1) * (vector.reshape(1, -1) - self.mu) ** 2, axis=1)
        logits = -dists / self.tau
        logits = logits - np.max(logits)
        exp = np.exp(logits)
        probs: np.ndarray = exp / np.sum(exp)
        return int(np.argmax(probs)), probs

    def margin(self, P: np.ndarray) -> float:
        probs = np.asarray(P, dtype=np.float64)
        if probs.size < 2:
            return 1.0
        ranked = np.sort(probs)[::-1]
        return round(float(ranked[0] - ranked[1]), 14)

    def predict(
        self,
        v: Any,
        category: str,
        score_fn: Callable[[np.ndarray, str], Any] | None = None,
    ) -> tuple[int, np.ndarray, float]:
        """Score via the supplied production scorer function, or the legacy fallback."""

        vector = self._vector(v)
        if score_fn is None:
            action, probs = self.score(vector)
            return action, probs, self.margin(probs)
        return self._normalize_prediction(score_fn(vector.copy(), str(category)))

    def _normalize_prediction(self, result: Any) -> tuple[int, np.ndarray, float]:
        if isinstance(result, tuple):
            if len(result) == 3:
                action_index, probabilities, margin = result
            elif len(result) == 2:
                action_index, probabilities = result
                margin = None
            else:
                raise ValueError("score_fn tuple result must have 2 or 3 elements")
        elif isinstance(result, dict):
            action_index = result.get("action_index", result.get("action"))
            probabilities = result.get("probabilities", result.get("action_probabilities"))
            margin = result.get("margin")
        else:
            action_index = getattr(result, "action_index", getattr(result, "action", None))
            probabilities = getattr(result, "probabilities", getattr(result, "action_probabilities", None))
            margin = getattr(result, "margin", None)
        if action_index is None:
            raise ValueError("score_fn result must include action_index")
        if probabilities is None:
            raise ValueError("score_fn result must include probabilities")
        probs = np.asarray(probabilities, dtype=np.float64)
        if probs.shape != (self.mu.shape[0],):
            raise ValueError("score_fn probabilities shape must match number of actions")
        if not np.all(np.isfinite(probs)):
            raise ValueError("score_fn probabilities must be finite")
        total = float(np.sum(probs))
        if total <= 0.0:
            raise ValueError("score_fn probabilities must have positive sum")
        probs = probs / total
        normalized_margin = self.margin(probs) if margin is None else round(float(margin), 14)
        return int(action_index), probs, normalized_margin

    def compute_Q(
        self,
        v: Any,
        P: Any,
        enriched_set: set[int] | None = None,
        K_weights: Any | None = None,
    ) -> np.ndarray:
        vector = self._vector(v)
        probs = np.asarray(P, dtype=np.float64)
        if probs.shape != (self.mu.shape[0],):
            raise ValueError("P shape must match number of actions")
        enriched = set(enriched_set or set())
        ranked = np.argsort(probs)[::-1]
        a1 = int(ranked[0])
        a2 = int(ranked[1]) if ranked.size > 1 else a1
        weights = None if K_weights is None else np.asarray(K_weights, dtype=np.float64)
        if weights is not None and weights.shape != (self.mu.shape[1],):
            raise ValueError("K_weights shape must match factor dimension")
        q: np.ndarray = np.zeros(self.mu.shape[1], dtype=np.float64)
        for k in range(self.mu.shape[1]):
            if k in enriched:
                q[k] = -1.0
                continue
            precision = (1.0 / max(float(self.sigma[k] ** 2), 0.001)) / 100.0
            discriminative = abs(float(self.mu[a1, k] - self.mu[a2, k]))
            leverage = abs(float((vector[k] - self.mu[a1, k]) ** 2 - (vector[k] - self.mu[a2, k]) ** 2))
            q[k] = precision + discriminative + leverage
            if weights is not None:
                q[k] *= float(weights[k])
        return q

    def investigate(
        self,
        decision_id: str,
        category: str,
        v_surface: Any,
        evidence_provider: EvidenceProvider,
        budget: int = 2,
        K_weights: Any | None = None,
        gated_sources: set[str] | None = None,
        score_fn: Callable[[np.ndarray, str], Any] | None = None,
        delta: float = 0.01,
        max_flips: int = 2,
        conservation_status: str = "not_evaluated_read_only",
    ) -> InvestigationTrace:
        v0 = self._vector(v_surface).copy()
        v = v0.copy()
        budget = max(0, int(budget))
        delta = max(0.0, float(delta))
        max_flips = max(1, int(max_flips))
        gated = set(gated_sources or set())
        frozen_k = None if K_weights is None else np.asarray(K_weights, dtype=np.float64).copy()
        if frozen_k is not None and frozen_k.shape != (self.mu.shape[1],):
            raise ValueError("K_weights shape must match factor dimension")
        snapshot = EpisodeSnapshot(
            centroids=self.mu.copy(),
            sigma=self.sigma.copy(),
            tau=float(self.tau),
            k_weights=None if frozen_k is None else frozen_k.copy(),
            factor_names=list(self.factor_names),
            action_names=list(self.action_names),
            category=str(category),
            geometry_hash=_geometry_hash(self.mu, self.sigma, self.tau),
            conservation_status=str(conservation_status),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        enriched: set[int] = set()
        surface_action, surface_p, surface_margin = self.predict(v0, category, score_fn)
        contrast = _contrast_dict(surface_action, surface_p, surface_margin, snapshot)
        action_sequence: list[int] = [surface_action]
        flip_count = 0
        acquired_count = 0
        halt_reason = "budget_exhausted" if budget > 0 else "budget_exhausted"
        steps: list[InvestigationStep] = []
        for step_index in range(budget):
            action_before, p_before, margin_before = self.predict(v, category, score_fn)
            q = self.compute_Q(v, p_before, enriched, frozen_k)
            k_star = int(np.argmax(q))
            if float(q[k_star]) <= 0.0:
                halt_reason = "budget_exhausted"
                break
            before = v.copy()
            error_source = "none"
            try:
                evidence = evidence_provider.read_evidence(decision_id, k_star, self.factor_names[k_star])
                status = "empty" if evidence is None else "acquired"
            except Exception as exc:
                evidence = None
                status = "error"
                error_source = f"error:{exc.__class__.__name__}"
            enriched.add(k_star)
            if evidence is None:
                step_halt = "budget_exhausted" if step_index == budget - 1 else None
                if step_halt is not None:
                    halt_reason = step_halt
                steps.append(
                    InvestigationStep(
                        step=len(steps),
                        dimension=k_star,
                        factor_name=self.factor_names[k_star],
                        evidence_value=None,
                        evidence_confidence=0.0,
                        evidence_source=error_source if status == "error" else "none",
                        v_before=before.tolist(),
                        v_after=v.copy().tolist(),
                        action_before=action_before,
                        action_after=action_before,
                        margin_before=margin_before,
                        margin_after=margin_before,
                        flipped=False,
                        status=status,
                        halt_reason=step_halt,
                    )
                )
                if step_halt is not None:
                    break
                continue
            raw_value = float(evidence.get("value", before[k_star]))
            value = max(0.0, min(1.0, raw_value))
            confidence = max(0.0, min(1.0, float(evidence.get("confidence", 1.0))))
            source = str(evidence.get("source", "unknown"))
            if source in gated:
                v[k_star] = confidence * value + (1.0 - confidence) * before[k_star]
            else:
                v[k_star] = value
            residual = _normalized_residual(v, before)
            acquired_count += 1
            action_after, _p_after, margin_after = self.predict(v, category, score_fn)
            if action_after != action_sequence[-1]:
                flip_count += 1
            action_sequence.append(action_after)
            step_halt = None
            if acquired_count >= 2 and residual < delta:
                halt_reason = "residual_below_threshold"
                step_halt = halt_reason
            elif _oscillated(action_sequence) or flip_count >= max_flips:
                halt_reason = "oscillation_detected"
                step_halt = halt_reason
            elif step_index == budget - 1:
                halt_reason = "budget_exhausted"
                step_halt = halt_reason
            steps.append(
                InvestigationStep(
                    step=len(steps),
                    dimension=k_star,
                    factor_name=self.factor_names[k_star],
                    evidence_value=value,
                    evidence_confidence=confidence,
                    evidence_source=source,
                    v_before=before.tolist(),
                    v_after=v.copy().tolist(),
                    action_before=action_before,
                    action_after=action_after,
                    margin_before=margin_before,
                    margin_after=margin_after,
                    flipped=action_before != action_after,
                    status="acquired",
                    halt_reason=step_halt,
                )
            )
            if step_halt is not None:
                break
        final_action, _final_p, final_margin = self.predict(v, category, score_fn)
        if steps and steps[-1].halt_reason is None:
            steps[-1].halt_reason = halt_reason
        return InvestigationTrace(
            decision_id=str(decision_id),
            category=str(category),
            budget=budget,
            steps=steps,
            surface_action=surface_action,
            surface_margin=surface_margin,
            final_action=final_action,
            final_margin=final_margin,
            snapshot=snapshot,
            contrast=contrast,
            halt_reason=halt_reason,
        )

    def _vector(self, v: Any) -> np.ndarray:
        vector: np.ndarray = np.asarray(v, dtype=np.float64)
        if vector.shape != (self.mu.shape[1],):
            raise ValueError(f"factor vector shape {vector.shape} != ({self.mu.shape[1]},)")
        if not np.all(np.isfinite(vector)):
            raise ValueError("factor vector must contain only finite values")
        return vector


def _geometry_hash(mu: np.ndarray, sigma: np.ndarray, tau: float) -> str:
    payload = {
        "centroids": np.asarray(mu, dtype=np.float64).tolist(),
        "sigma": np.asarray(sigma, dtype=np.float64).tolist(),
        "tau": float(tau),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _contrast_dict(action: int, probs: np.ndarray, margin: float, snapshot: EpisodeSnapshot) -> dict[str, Any]:
    action_name = snapshot.action_names[action] if 0 <= int(action) < len(snapshot.action_names) else str(action)
    return {
        "action": int(action),
        "action_name": action_name,
        "margin": float(margin),
        "probabilities": [float(x) for x in np.asarray(probs, dtype=np.float64).tolist()],
        "geometry_hash": snapshot.geometry_hash,
        "note": "Single-pass result using same geometry snapshot, budget=0",
    }


def _normalized_residual(current: np.ndarray, previous: np.ndarray) -> float:
    numerator = float(np.sqrt(np.sum((current - previous) ** 2)))
    denominator = float(np.sqrt(np.sum(current**2) + 1.0e-10))
    return numerator / denominator


def _oscillated(actions: list[int]) -> bool:
    if len(actions) < 3:
        return False
    return actions[-1] == actions[-3] and actions[-1] != actions[-2]


def _trace_to_dict(trace: InvestigationTrace) -> dict[str, Any]:
    return {
        "decision_id": trace.decision_id,
        "category": trace.category,
        "budget": trace.budget,
        "steps": [asdict(step) for step in trace.steps],
        "surface_action": trace.surface_action,
        "surface_margin": trace.surface_margin,
        "final_action": trace.final_action,
        "final_margin": trace.final_margin,
        "snapshot": trace.snapshot.public_dict() if trace.snapshot is not None else None,
        "contrast": dict(trace.contrast or {}),
        "halt_reason": trace.halt_reason,
    }


class KUtilityStore:
    """Per-category, per-dimension VLD utility weights stored on an injected connection."""

    def __init__(self, decision_store: Any, d: int, profile: str | None = None):
        self.decision_store = decision_store
        self.d = int(d)
        if self.d <= 0:
            raise ValueError("d must be positive")
        conn = getattr(decision_store, "conn", None) or getattr(decision_store, "_conn", None)
        if conn is None:
            raise AttributeError("decision_store must expose conn or _conn")
        if profile is not None and resolve_profile(profile, domain="") == "production":
            module_name = type(conn).__module__.lower()
            if "sqlite" in module_name or isinstance(conn, __import__("sqlite3").Connection):
                raise RuntimeError(
                    "Production KUtilityStore requires a graph-backed connection; "
                    "SQLite is test/offline only"
                )
        self.conn: Any = conn
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS k_utility (
                category TEXT NOT NULL,
                dimension INTEGER NOT NULL,
                weight REAL DEFAULT 0.5,
                n_updates INTEGER DEFAULT 0,
                PRIMARY KEY (category, dimension)
            )
            """
        )
        self.conn.commit()

    def get_weights(self, category: str) -> np.ndarray:
        rows: Any = self.conn.execute(
            "SELECT dimension, weight FROM k_utility WHERE category = ?",
            (str(category),),
        ).fetchall()
        weights: np.ndarray = np.full(self.d, 0.5, dtype=np.float64)
        for dim, weight in rows:
            index = int(dim)
            if 0 <= index < self.d:
                weights[index] = float(weight)
        return weights

    def update_weights(
        self,
        category: str,
        trace: InvestigationTrace,
        correct: bool,
        lr_pos: float = 0.02,
        lr_neg: float = 0.005,
    ) -> None:
        weights = self.get_weights(category)
        updates = CounterLike()
        for step in trace.steps:
            dim = int(step.dimension)
            if not 0 <= dim < self.d:
                continue
            if correct:
                weights[dim] = min(3.0, weights[dim] + float(lr_pos) * (2.0 if step.flipped else 1.0))
            else:
                weights[dim] = max(0.1, weights[dim] - float(lr_neg))
            updates.increment(dim)
        for dim, count in updates.items():
            self.conn.execute(
                """
                INSERT INTO k_utility(category, dimension, weight, n_updates)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(category, dimension) DO UPDATE SET
                    weight = excluded.weight,
                    n_updates = k_utility.n_updates + excluded.n_updates
                """,
                (str(category), int(dim), float(weights[dim]), int(count)),
            )
        self.conn.commit()


class CounterLike:
    def __init__(self) -> None:
        self._counts: dict[int, int] = {}

    def increment(self, key: int) -> None:
        self._counts[key] = self._counts.get(key, 0) + 1

    def items(self):
        return self._counts.items()


class _CallableEvidenceProvider:
    def __init__(self, func: Callable[..., Any]):
        self._func = func

    def read_evidence(self, decision_id: str, dimension: int, factor_name: str) -> Optional[dict[str, Any]]:
        result = self._func(decision_id, dimension, factor_name)
        if result is None:
            return None
        if not isinstance(result, dict):
            raise ValueError("callable evidence_provider must return a dict or None")
        return result


def investigate(
    *,
    factors: Any,
    category: str,
    budget: int,
    evidence_provider: EvidenceProvider | Callable[..., Any],
    score_fn: Callable[[np.ndarray, str], Any] | None = None,
    mu: Any | None = None,
    sigma: Any | None = None,
    tau: float = 0.1,
    factor_names: list[str] | None = None,
    k_weights: Any | None = None,
    K_weights: Any | None = None,
    gated_sources: set[str] | None = None,
    decision_id: str = "ad-hoc",
    delta: float = 0.01,
    max_flips: int = 2,
) -> dict[str, Any]:
    """Compatibility wrapper returning a serializable investigation trace."""

    if mu is None:
        raise ValueError("mu is required when using the module-level investigate wrapper")
    mu_arr = np.asarray(mu, dtype=np.float64)
    if mu_arr.ndim != 2:
        raise ValueError("mu must have shape (actions, factors)")
    sigma_arr = np.ones(mu_arr.shape[1], dtype=np.float64) if sigma is None else np.asarray(sigma, dtype=np.float64)
    names = list(factor_names or [f"dim_{i}" for i in range(mu_arr.shape[1])])
    provider = evidence_provider if hasattr(evidence_provider, "read_evidence") else _CallableEvidenceProvider(evidence_provider)
    trace = VLDInvestigator(mu_arr, sigma_arr, names, tau=tau).investigate(
        decision_id,
        category,
        factors,
        provider,
        budget=budget,
        K_weights=K_weights if K_weights is not None else k_weights,
        gated_sources=gated_sources,
        score_fn=score_fn,
        delta=delta,
        max_flips=max_flips,
    )
    return _trace_to_dict(trace)


__all__ = [
    "EvidenceProvider",
    "investigate",
    "InvestigationStep",
    "EpisodeSnapshot",
    "InvestigationTrace",
    "KUtilityStore",
    "VLDInvestigator",
]
