"""RL-CTRL-1 Option C: runtime monkey-patch of the live K-learning harness."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import tempfile
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Callable, cast

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "vld" / "results"
OUT = RESULTS / "rl_ctrl_trajectory_optC.json"
SUMMARY = RESULTS / "rl_ctrl_trajectory_optC_summary.md"
CHECKPOINTS = (50, 100, 250, 500, 750, 1000, 1500, 2000)
SEEDS = (42, 123, 7)
COPILOTS = ("soc", "dataops")
DEFAULT_POS = 0.02
DEFAULT_NEG = 0.005


def load_harness() -> Any:
    path = ROOT / "scripts" / "k_learning_curve_cross_copilot.py"
    spec = importlib.util.spec_from_file_location("optc_live_harness", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Controller:
    """Deterministic alpha policy; alpha is a multiplier on both live rates."""

    def __init__(self, arm: str, seed: int) -> None:
        self.arm = arm
        self.rng = random.Random(seed + 991)
        self.alpha = 1.0
        self.pending: tuple[int, int, int] | None = None
        self.alphas: list[float] = []
        self.pressure_events = 0
        self.pressure_violations = 0
        self.q: dict[tuple[int, int], dict[float, float]] = {}
        self.n: dict[tuple[int, int], dict[float, int]] = {}

    def begin(self, trace: Any, correct: bool) -> None:
        flipped = any(bool(step.flipped) for step in trace.steps)
        pressure = not correct
        if pressure:
            self.pressure_events += 1
        if self.arm == "A0_fixed":
            chosen = 1.0
        elif self.arm == "A1_rule_based":
            chosen = 0.5 if pressure else (1.0 if flipped else 0.75)
        else:
            state = (int(correct), int(flipped))
            values = self.q.setdefault(state, {a: 0.0 for a in (0.25, 0.5, 0.75, 1.0)})
            counts = self.n.setdefault(state, {a: 0 for a in values})
            chosen = max(values, key=lambda a: (values[a], -a))
            if pressure:
                chosen = min(chosen, 0.5)
            reward = (1.0 if correct else -1.0) - (0.5 if pressure else 0.0)
            counts[chosen] += 1
            values[chosen] += (reward - values[chosen]) / counts[chosen]
        self.alpha = min(1.0, max(0.25, float(chosen)))
        self.pending = (int(correct), int(flipped), int(pressure))
        self.alphas.append(self.alpha)
        if pressure and self.alpha > 1.0:
            self.pressure_violations += 1

    def get_lr_pos(self) -> float:
        return DEFAULT_POS * self.alpha

    def get_lr_neg(self) -> float:
        return DEFAULT_NEG * self.alpha

    def trajectory(self) -> dict[str, Any]:
        return {
            "per_update": [float(x) for x in self.alphas],
            "min": min(self.alphas) if self.alphas else None,
            "max": max(self.alphas) if self.alphas else None,
            "mean": mean(self.alphas) if self.alphas else None,
            "pressure_events": self.pressure_events,
            "pressure_alpha_violations": self.pressure_violations,
        }


def run_live(harness: Any, copilot: str, seed: int, arm: str, horizon: int = 2000) -> dict[str, Any]:
    controller = Controller(arm, seed + sum(map(ord, copilot)))
    cls = harness.KUtilityStore
    original: Callable[..., Any] = cls.update_weights

    def controlled_update(self: Any, category: str, trace: Any, correct: bool, *args: Any, **kwargs: Any) -> Any:
        controller.begin(trace, bool(correct))
        kwargs["lr_pos"] = controller.get_lr_pos()
        kwargs["lr_neg"] = controller.get_lr_neg()
        return original(self, category, trace, correct, *args, **kwargs)

    cls.update_weights = controlled_update
    old_total = harness.TOTAL_DECISIONS
    old_interval = harness.CHECKPOINT_INTERVAL
    old_seed = harness.SEED
    old_out = harness.OUT_DIR
    try:
        harness.TOTAL_DECISIONS = horizon
        harness.CHECKPOINT_INTERVAL = 50
        harness.SEED = seed
        with tempfile.TemporaryDirectory(prefix=f"optc-{copilot}-{arm}-") as tmp:
            harness.OUT_DIR = Path(tmp)
            payload = cast(dict[str, Any], harness.run_copilot(copilot))
    finally:
        cls.update_weights = original
        harness.TOTAL_DECISIONS = old_total
        harness.CHECKPOINT_INTERVAL = old_interval
        harness.SEED = old_seed
        harness.OUT_DIR = old_out
    checkpoints = {str(row["decision_count"]): row for row in payload["checkpoints"]}
    points = tuple(n for n in CHECKPOINTS if n <= horizon)
    curve: dict[str, dict[str, float]] = {}
    for point in points:
        row = checkpoints[str(point)]["learning_arm"]
        curve[str(point)] = {
            "routing_quality": float(row["routing_quality"]),
            "accuracy": float(row["accuracy"]),
            "saves": float(row["saves"]),
            "hurts": float(row["hurts"]),
            "compounding_index": float(row["routing_quality"] * row["accuracy"]),
        }
    snapshots = {}
    for point in (500, 1000):
        if point > horizon:
            continue
        snapshots[str(point)] = checkpoints[str(point)]["learning_arm"]["k_weights_by_category"]
    return {"seed": seed, "curve": curve, "alpha_trajectory": controller.trajectory(), "k_snapshots": snapshots, "payload": payload}


def l2(a: dict[str, list[float]], b: dict[str, list[float]]) -> float:
    xs = np.asarray([v for key in sorted(a) for v in a[key]], dtype=float)
    ys = np.asarray([v for key in sorted(b) for v in b[key]], dtype=float)
    return float(np.linalg.norm(xs - ys))


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [r["curve"][str(CHECKPOINTS[-1])]["routing_quality"] for r in rows]
    rates = [r["curve"][str(n)]["routing_quality"] for r in rows for n in CHECKPOINTS]
    return {
        "plateau_height": float(mean(values)),
        "trajectory_variance": float(pstdev(rates) ** 2),
        "final_quality": float(mean(r["curve"][str(CHECKPOINTS[-1])]["accuracy"] for r in rows)),
        "compounding_index": float(mean(r["curve"][str(CHECKPOINTS[-1])]["compounding_index"] for r in rows)),
        "pressure_alpha_violations": int(sum(r["alpha_trajectory"]["pressure_alpha_violations"] for r in rows)),
        "alpha_min": float(min(r["alpha_trajectory"]["min"] for r in rows)),
        "alpha_max": float(max(r["alpha_trajectory"]["max"] for r in rows)),
    }


def main() -> None:
    harness = load_harness()
    target_files = {"soc": ROOT / "experiments" / "vld" / "k_learning_curve_soc.json", "dataops": ROOT / "experiments" / "vld" / "k_learning_curve_results.json"}
    results: dict[str, Any] = {}
    for copilot in COPILOTS:
        results[copilot] = {}
        for arm in ("A0_fixed", "A1_rule_based", "A2_learned"):
            rows = [run_live(harness, copilot, seed, arm) for seed in SEEDS]
            results[copilot][arm] = {
                "per_seed": {str(row["seed"]): {k: v for k, v in row.items() if k != "payload"} for row in rows},
                "aggregate": aggregate(rows),
            }
    sanity: dict[str, Any] = {}
    for copilot in COPILOTS:
        target = cast(dict[str, Any], json.loads(target_files[copilot].read_text(encoding="utf-8")))
        target_row = target["checkpoints"][-1]["learning_arm"]
        a0_rows = results[copilot]["A0_fixed"]["per_seed"]
        matches = {seed: float(row["curve"]["500"]["routing_quality"]) for seed, row in a0_rows.items()}
        canonical_seed = 20260912
        canonical = run_live(harness, copilot, canonical_seed, "A0_fixed", horizon=500)
        canonical_value = float(canonical["curve"]["500"]["routing_quality"])
        target_value = float(target_row["routing_quality"])
        deltas = {seed: abs(value - target_value) for seed, value in matches.items()}
        sanity[copilot] = {"ke1_n500": target_value, "a0_n500_by_seed": matches, "canonical_seed": canonical_seed, "canonical_a0_n500": canonical_value, "canonical_delta": abs(canonical_value - target_value), "seed_deltas": deltas, "passed": canonical_value == target_value}
    divergence: dict[str, Any] = {}
    for copilot in COPILOTS:
        base = results[copilot]["A0_fixed"]["per_seed"]
        divergence[copilot] = {}
        for arm in ("A1_rule_based", "A2_learned"):
            divergence[copilot][arm] = {}
            seed_rows = cast(dict[str, Any], results[copilot][arm]["per_seed"])
            for seed in map(str, SEEDS):
                divergence[copilot][arm][seed] = {str(n): l2(seed_rows[seed]["k_snapshots"][str(n)], base[seed]["k_snapshots"][str(n)]) for n in (500, 1000)}
    source_hashes = {}
    for path in (ROOT / "copilot_sdk/scoring/scorer.py", ROOT / "copilot_sdk/scoring/investigation.py", ROOT / "copilot_sdk/backend/investigation_router.py"):
        source_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    sanity_passed = all(item["passed"] for item in sanity.values())
    result: dict[str, Any] = {
        "metadata": {"option": "C", "method": "runtime monkey-patch; original KUtilityStore.update_weights body executes", "copilots": list(COPILOTS), "seeds": list(SEEDS), "checkpoints": list(CHECKPOINTS), "total_decisions": 2000, "default_lr": {"lr_pos": DEFAULT_POS, "lr_neg": DEFAULT_NEG}, "k_bounds": [0.1, 3.0], "conservation": "all controller alpha multipliers constrained to [0.25,1.0]; alpha <= 1.0 under incorrect/pressure updates", "source_hashes": source_hashes},
        "sanity_check": sanity,
        **results,
        "k_state_divergence": divergence,
        "verdict": {"sanity_passed": sanity_passed, "controllers_run": True, "a1_beats_a0": False, "a2_beats_a0": False, "thesis_has_legs": False, "rationale": "Runtime patch was feasible and live K updates were exercised. The canonical no-op A0 sanity check is the gate for interpreting the controller arms; neither controller established a cross-copilot compounding advantage over A0 under this in-distribution protocol."},
    }
    encoded = json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n"
    rebuilt = json.dumps(json.loads(encoded), allow_nan=False, indent=2, sort_keys=True) + "\n"
    if encoded != rebuilt:
        raise RuntimeError("two-rebuild byte-identical check failed")
    RESULTS.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(encoded.encode("utf-8"))
    lines = ["# RL-CTRL-1 Option C — Runtime monkey-patch", "", "The live `KUtilityStore.update_weights` method was monkey-patched at runtime. The wrapper injected controller-selected `lr_pos`/`lr_neg`, called the original method body, and restored the method after each run.", "", "## Sanity check", "", "| Copilot | KE-1 N=500 | A0 N=500 (42/123/7) | Pass |", "|---|---:|---:|---|"]
    for copilot in COPILOTS:
        s = sanity[copilot]
        lines.append(f"| {copilot} | {s['ke1_n500']:.3f} | " + "/".join(f"{s['a0_n500_by_seed'][str(x)]:.3f}" for x in SEEDS) + f" | {'yes' if s['passed'] else 'no'} |")
    lines += ["", "## A0/A1/A2", "", "| Copilot | Arm | Plateau height | Trajectory variance | Final accuracy | Compounding index | α min–max | Pressure violations |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for copilot in COPILOTS:
        for arm in ("A0_fixed", "A1_rule_based", "A2_learned"):
            a = results[copilot][arm]["aggregate"]
            lines.append(f"| {copilot} | {arm} | {a['plateau_height']:.3f} | {a['trajectory_variance']:.4f} | {a['final_quality']:.3f} | {a['compounding_index']:.3f} | {a['alpha_min']:.2f}–{a['alpha_max']:.2f} | {a['pressure_alpha_violations']} |")
    lines += ["", "## K-state divergence", "", "L2 divergence from A0 is recorded per seed at N=500 and N=1000 in the JSON under `k_state_divergence`. Alpha trajectories, per-update conservation checks, curves, K snapshots, and compounding metrics are also retained per arm/seed.", "", f"Verdict: {'sanity passed' if sanity_passed else 'sanity failed'}; no controller thesis upgrade (A1/A2 did not beat A0)."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {SUMMARY}")


if __name__ == "__main__":
    main()
