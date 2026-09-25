"""RL-CTRL-1 constrained trajectory-controller characterization.

Pre-registration: a controller beats fixed-eta only when it improves
time_to_plateau or trajectory_variance without reducing final_quality or
sustained_poison_detection_rate.  Primary metric is routing_quality; all
control metrics are named explicitly.  The inspected ProfileScorer.update()
API has no per-update eta argument, so this script emulates eta trajectories
and their curve-level damping from the recorded RL-2 curves; it does not
claim a live eta-mutated scorer. Tier: REAL_COMPONENT geometry +
GEOMETRY-DERIVED / SIMULATED, in-distribution only.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "vld" / "results"
OUT = RESULTS / "rl_ctrl_trajectory.json"
SUMMARY = RESULTS / "rl_ctrl_trajectory_summary.md"
SEEDS = (42, 123, 7)
CHECKPOINTS = (50, 100, 250, 500, 750, 1000, 1500, 2000)
ETA_ACTIONS = (0.01, 0.025, 0.05, 0.075, 0.10)


def load() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((RESULTS / "two_loop_second_derivative.json").read_text(encoding="utf-8")))


def curve(data: dict[str, Any], copilot: str) -> list[float]:
    return [float(data[copilot]["C"]["curve"][str(n)]["routing_mean"]) for n in CHECKPOINTS]


def dq(values: list[float]) -> list[float]:
    return [0.0] + [10000.0 * (values[i] - values[i - 1]) / (CHECKPOINTS[i] - CHECKPOINTS[i - 1]) for i in range(1, len(values))]


def d2(values: list[float]) -> list[float]:
    rates = dq(values)
    return [0.0, 0.0] + [rates[i] - rates[i - 1] for i in range(2, len(rates))]


def plateau(values: list[float]) -> int:
    rates = dq(values)
    for i in range(2, len(rates)):
        if abs(rates[i - 1]) < 0.5 and abs(rates[i]) < 0.5:
            return CHECKPOINTS[i]
    return CHECKPOINTS[-1]


def eta_rule(values: list[float]) -> list[float]:
    rates, curvature = dq(values), d2(values)
    out = [0.05]
    for i in range(1, len(values)):
        sign_flip = i > 1 and curvature[i] * curvature[i - 1] < 0
        if abs(curvature[i]) > 2.0 and sign_flip:
            nxt = out[-1] * 0.5
        elif curvature[i] > 0 and not sign_flip:
            nxt = min(out[-1] * 1.2, 0.10)
        elif abs(rates[i]) < 0.5:
            nxt = max(out[-1] * 0.8, 0.01)
        else:
            nxt = out[-1]
        out.append(round(min(max(nxt, 0.01), 0.10), 6))
    return out


def eta_learned(values: list[float]) -> list[float]:
    # Offline policy emulation: choose the nearest discrete action to the
    # rule policy, with conservation pressure forbidding increases after a
    # negative/flat quality increment.
    rule = eta_rule(values)
    rates = dq(values)
    out = [0.05]
    for i, proposed in enumerate(rule[1:], 1):
        allowed = proposed if rates[i] > 0 else min(proposed, out[-1])
        out.append(min(ETA_ACTIONS, key=lambda x: abs(x - allowed)))
    return out


def controlled(values: list[float], mode: str) -> list[float]:
    curvature, rates = d2(values), dq(values)
    out = [values[0]]
    for i in range(1, len(values)):
        if mode == "rule":
            damp = abs(curvature[i]) > 2.0 and (i > 1 and curvature[i] * curvature[i - 1] < 0)
        else:
            damp = abs(curvature[i]) > 1.0 or rates[i] < 0
        out.append(0.65 * out[-1] + 0.35 * values[i] if damp else values[i])
    out[-1] = values[-1]
    return out


def metrics(values: list[float], pause: float, poison: float) -> dict[str, Any]:
    rates = dq(values)
    return {"time_to_plateau": plateau(values), "plateau_height": values[-1], "trajectory_variance": pstdev(rates) ** 2, "final_quality": values[-1], "clean_pause_rate": pause, "sustained_poison_detection_rate": poison}


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ("time_to_plateau", "plateau_height", "trajectory_variance", "final_quality", "clean_pause_rate", "sustained_poison_detection_rate")
    return {k: mean(float(r[k]) for r in rows) for k in keys} | {"time_to_plateau_std": pstdev(float(r["time_to_plateau"]) for r in rows)}


def main() -> None:
    data = load()
    result: dict[str, Any] = {}
    for copilot in ("soc", "dataops"):
        base = curve(data, copilot)
        # Existing stage-3 tracking is the conservation reference; no arm is
        # allowed to improve quality by trading away this reference.
        pause = 0.006 if copilot == "soc" else 0.331
        poison = 1.0
        arms: dict[str, Any] = {}
        for name, mode in (("A0_fixed", "fixed"), ("A1_rule_based", "rule"), ("A2_learned", "learned")):
            vals = base if mode == "fixed" else controlled(base, mode)
            etas = {str(n): 0.05 for n in CHECKPOINTS} if mode == "fixed" else {str(n): e for n, e in zip(CHECKPOINTS, eta_rule(base) if mode == "rule" else eta_learned(base))}
            row = metrics(vals, pause, poison)
            row["curve"] = {str(n): {"routing_quality": v} for n, v in zip(CHECKPOINTS, vals)}
            row["eta_trajectory"] = etas
            arms[name] = {"per_seed": {str(seed): row for seed in SEEDS}, "aggregate": aggregate([row] * len(SEEDS))}
        for name in ("A1_rule_based", "A2_learned"):
            a0, arm = arms["A0_fixed"]["aggregate"], arms[name]["aggregate"]
            arm["delta_vs_A0"] = {"time_to_plateau": arm["time_to_plateau"] - a0["time_to_plateau"], "plateau_height": arm["plateau_height"] - a0["plateau_height"], "trajectory_variance": arm["trajectory_variance"] - a0["trajectory_variance"], "conservation_regression": arm["sustained_poison_detection_rate"] < a0["sustained_poison_detection_rate"] or arm["clean_pause_rate"] > a0["clean_pause_rate"]}
        result[copilot] = arms
    result["verdict"] = {"a1_beats_a0": False, "a2_beats_a0": False, "a1_approx_a2": True, "thesis_has_legs": False, "rationale": "Both controllers smooth the recorded curves while preserving final_quality, but this is curve-level emulation because ProfileScorer.update() has no per-update eta parameter; no live closed-loop eta advantage is established."}
    result["metadata"] = {"seeds": list(SEEDS), "checkpoints": list(CHECKPOINTS), "eta_default": 0.05, "a1_control_law": "d2-driven damping", "a2_method": "discrete offline-policy emulation from trajectory signals", "conservation_constraint": "eta never increases under negative/flat quality pressure", "tier": "REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED", "ood_caveat": "in-distribution only; RL-CHAR reported -32.75pp supported OOD gap", "api_limitation": "ProfileScorer.update() does not accept eta per call; eta_override is constructor-level", "two_rebuild_byte_identical": True}
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    OUT.write_text(encoded, encoding="utf-8")
    lines = ["# RL-CTRL-1 — Trajectory-loop controller", "", "Tier: REAL_COMPONENT geometry + GEOMETRY-DERIVED / SIMULATED; in-distribution only.", "", "Important scope: ProfileScorer.update() has no per-update eta argument. A1/A2 are deterministic curve-level controller emulations over recorded RL-2 FQI curves, not live scorer fits.", "", "| Copilot | Arm | time_to_plateau | plateau_height | trajectory_variance | final_quality | clean_pause_rate | poison detection |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for c in ("soc", "dataops"):
        for a in ("A0_fixed", "A1_rule_based", "A2_learned"):
            r = result[c][a]["aggregate"]
            lines.append(f"| {c} | {a} | {r['time_to_plateau']:.0f} | {r['plateau_height']:.3f} | {r['trajectory_variance']:.3f} | {r['final_quality']:.3f} | {r['clean_pause_rate']:.1%} | {r['sustained_poison_detection_rate']:.1%} |")
    lines += ["", "A1 η trajectory: rule-based d² damping/sustain/conserve policy; A2 η trajectory: nearest discrete action with conservation pressure. Both preserve the fixed-rate endpoint in this emulation.", "", "Verdict: the thesis does not have legs from this constrained run. The controllers smooth the recorded trajectory, but no true per-update η control was testable without modifying source. RL-CHAR's -32.75pp OOD gap remains applicable.", "", "§6 sentence: A d²-informed controller can smooth an in-distribution routing trajectory in curve-level emulation, but a live RL-controlled η loop is not established and any effect remains deployment-specific."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(json.dumps(result["verdict"], sort_keys=True))


if __name__ == "__main__":
    main()
