"""A2-EXT: misleading-evidence dose response and governance catch.

Pre-registration: sweep misleading evidence fractions from 0 to 1 and report
the crossover honestly. Governance uses the standalone conservation Check-A
component (recent action_accuracy < 0.75 over the last 100 verified records)
and the requested abstention proxy (post-investigation top-two probability
margin < 0.05). The full scorer is never called.

Tier: GEOMETRY-DERIVED + SIMULATED. Labels are nearest-centroid targets from
the latent truth vector; acquired evidence is simulated independently.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import deque
from pathlib import Path
from typing import Any, cast

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vld_adversarial_saves_hurts_v1 import (
    COPILOTS,
    SEEDS,
    investigator_for,
    load_geometry,
    make_case,
)


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "experiments" / "vld" / "results" / "adversarial_dose_response.json"
FRACTIONS = (0.00, 0.10, 0.20, 0.30, 0.50, 0.75, 1.00)
N_SCENARIOS = 250
BUDGET = 2
WINDOW = 100
THRESHOLD = 0.75
ABSTENTION_MARGIN = 0.05


def score(inv: Any, vector: np.ndarray) -> int:
    return int(inv.score(vector)[0])


def margin(inv: Any, vector: np.ndarray) -> float:
    _action, probabilities = inv.score(vector)
    return float(inv.margin(probabilities))


def q_dims(inv: Any, vector: np.ndarray, used: set[int]) -> list[int]:
    _action, probabilities = inv.score(vector)
    weights = np.full(vector.size, 0.5, dtype=np.float64)
    q = inv.compute_Q(vector, probabilities, used, K_weights=weights)
    return [int(index) for index in np.argsort(q)[::-1][:BUDGET]]


def dose_case(rng: random.Random, info: dict[str, Any], category: str, fraction: float) -> dict[str, Any]:
    base = make_case(rng, "misleading", info, category)
    inv = investigator_for(info, category)
    truth = np.asarray(base["truth"], dtype=np.float64)
    surface = truth.copy()
    target = score(inv, truth)
    alternatives = [i for i in range(inv.mu.shape[0]) if i != target]
    wrong = max(alternatives, key=lambda i: float(np.linalg.norm(inv.mu[target] - inv.mu[i])))
    changed = int(np.argmax(np.abs(inv.mu[target] - inv.mu[wrong])))
    surface[changed] = float(np.clip(inv.mu[wrong, changed] + rng.gauss(0.0, 0.008), 0.02, 0.98))
    selected = q_dims(inv, surface, set())
    evidence = truth.copy()
    for dim in selected:
        if rng.random() < fraction:
            evidence[dim] = float(np.clip(inv.mu[wrong, dim] + rng.gauss(0.0, 0.008), 0.02, 0.98))
    return {"category": category, "truth": truth, "surface": surface,
            "evidence": evidence, "target": target}


def run_case_with_margin(case: dict[str, Any], info: dict[str, Any]) -> dict[str, Any]:
    inv = investigator_for(info, str(case["category"]))
    vector = np.asarray(case["surface"], dtype=np.float64).copy()
    evidence = np.asarray(case["evidence"], dtype=np.float64)
    target = int(case["target"])
    pre = score(inv, vector)
    used: set[int] = set()
    for _ in range(min(BUDGET, vector.size)):
        dims = q_dims(inv, vector, used)
        if not dims:
            break
        dim = dims[0]
        used.add(dim)
        vector[dim] = evidence[dim]
    post = score(inv, vector)
    return {"pre_correct": pre == target, "post_correct": post == target,
            "saved": pre != target and post == target,
            "hurt": pre == target and post != target,
            "post_margin": margin(inv, vector)}


def counts(runs: list[dict[str, Any]]) -> dict[str, Any]:
    saves = sum(int(r["saved"]) for r in runs)
    hurts = sum(int(r["hurt"]) for r in runs)
    neutral_correct = sum(int(r["pre_correct"] and r["post_correct"]) for r in runs)
    neutral_wrong = sum(int(not r["pre_correct"] and not r["post_correct"]) for r in runs)
    return {"saves": saves, "hurts": hurts, "neutral_correct": neutral_correct,
            "neutral_wrong": neutral_wrong, "ratio": f"{saves}:{hurts}"}


def dose_once(geometry: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for copilot in COPILOTS:
        info = geometry[copilot]
        categories = list(info["all_category_mu"].keys())
        copilot_out: dict[str, Any] = {}
        for fraction in FRACTIONS:
            per_seed: dict[str, Any] = {}
            all_runs: list[dict[str, Any]] = []
            for seed in SEEDS:
                rng = random.Random(seed)
                runs = [run_case_with_margin(dose_case(rng, info, categories[i % len(categories)], fraction), info)
                        for i in range(N_SCENARIOS)]
                per_seed[str(seed)] = counts(runs)
                all_runs.extend(runs)
            copilot_out[f"{fraction:.2f}"] = {"per_seed": per_seed, "aggregate": counts(all_runs)}
        out[copilot] = copilot_out
    return out


def gate_state(history: deque[bool]) -> bool:
    return len(history) >= WINDOW and sum(history) / len(history) < THRESHOLD


def governance_once(geometry: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for copilot in COPILOTS:
        info = geometry[copilot]
        categories = list(info["all_category_mu"].keys())
        total_hurts = gate_caught = abstention_caught = either_caught = 0
        for seed in SEEDS:
            rng = random.Random(seed + 10000)
            history: deque[bool] = deque(maxlen=WINDOW)
            for index in range(200):
                clean = make_case(rng, "boundary", info, categories[index % len(categories)])
                clean["surface"] = np.asarray(clean["truth"], dtype=np.float64)
                clean["evidence"] = np.asarray(clean["truth"], dtype=np.float64)
                clean["target"] = score(investigator_for(info, str(clean["category"])), clean["truth"])
                clean_run = run_case_with_margin(clean, info)
                history.append(bool(clean_run["post_correct"]))
            for index in range(N_SCENARIOS):
                tier = "misleading" if index % 2 == 0 else "adversarial_q"
                case = make_case(rng, tier, info, categories[index % len(categories)])
                run = run_case_with_margin(case, info)
                history.append(bool(run["post_correct"]))
                if not run["hurt"]:
                    continue
                total_hurts += 1
                gate = gate_state(history)
                abstain = float(run["post_margin"]) < ABSTENTION_MARGIN
                gate_caught += int(gate)
                abstention_caught += int(abstain)
                either_caught += int(gate or abstain)
        slipped = total_hurts - either_caught
        denom = max(total_hurts, 1)
        output[copilot] = {"total_hurts": total_hurts, "gate_caught": gate_caught,
                           "abstention_caught": abstention_caught, "either_caught": either_caught,
                           "slipped_through": slipped, "gate_catch_rate": gate_caught / denom,
                           "abstention_catch_rate": abstention_caught / denom,
                           "combined_catch_rate": either_caught / denom,
                           "abstention_method": "margin < 0.05",
                           "gate_method": "Check-A proxy: recent action_accuracy < 0.75 over last 100"}
    return output


def main() -> None:
    geometry = load_geometry()
    dose_a = dose_once(geometry)
    dose_b = dose_once(geometry)
    gov_a = governance_once(geometry)
    gov_b = governance_once(geometry)
    if json.dumps(dose_a, sort_keys=True) != json.dumps(dose_b, sort_keys=True) or json.dumps(gov_a, sort_keys=True) != json.dumps(gov_b, sort_keys=True):
        raise RuntimeError("determinism self-test failed")
    result: dict[str, Any] = {"dose_response": dose_a, "crossover": {}, "governance_catch": gov_a,
                              "metadata": {"seeds": list(SEEDS), "fractions": list(FRACTIONS),
                                            "gate_rule": "75%/last-100 (standalone Check-A proxy)",
                                            "clean_baseline_decisions": 200,
                                            "tier": "GEOMETRY-DERIVED + SIMULATED"}}
    for copilot in COPILOTS:
        rows = result["dose_response"][copilot]
        crossing = None
        for fraction in FRACTIONS:
            row = rows[f"{fraction:.2f}"]["aggregate"]
            if int(row["hurts"]) >= int(row["saves"]):
                crossing = fraction
                break
        result["crossover"][copilot] = {"crossover_fraction": crossing,
                                         "interpolation_note": "first swept fraction where hurts >= saves; exact crossover lies between adjacent tested fractions"}
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# A2-EXT — Dose response and governance catch", "", "Tier: GEOMETRY-DERIVED + SIMULATED.", "",
             "## Dose response", "", "| Fraction | " + " | ".join(f"{c} saves:hurts" for c in COPILOTS) + " |", "|---:|" + "---:|" * len(COPILOTS)]
    for fraction in FRACTIONS:
        lines.append("| " + f"{fraction:.2f}" + " | " + " | ".join(result["dose_response"][c][f"{fraction:.2f}"]["aggregate"]["ratio"] for c in COPILOTS) + " |")
    lines += ["", "## Crossover", ""]
    for c in COPILOTS:
        lines.append(f"- {c}: first hurts>=saves fraction = {result['crossover'][c]['crossover_fraction']}")
    lines += ["", "## Governance catch", "", "| Copilot | Hurts | Gate caught | Abstention caught | Either caught | Slipped | Combined rate |", "|---|---:|---:|---:|---:|---:|---:|"]
    for c in COPILOTS:
        g = gov_a[c]
        lines.append(f"| {c} | {g['total_hurts']} | {g['gate_caught']} | {g['abstention_caught']} | {g['either_caught']} | {g['slipped_through']} | {g['combined_catch_rate']:.1%} |")
    lines += ["", "The gate column is the standalone 75%/last-100 Check-A proxy; Check-B volume inputs were not available in this experiment. Abstention is the post-investigation margin < 0.05 proxy.", "", "Paper sentence: At misleading fractions below the reported crossover points, VLD maintains positive saves:hurts; of the adversarial hurts, the combined standalone gate or post-investigation abstention proxy caught the reported fraction, while the remainder slipped through."]
    (RESULT.parent / "adversarial_dose_response_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", RESULT)
    for c in COPILOTS:
        g = gov_a[c]
        print(f"{c}: crossover={result['crossover'][c]['crossover_fraction']} hurts={g['total_hurts']} caught={g['either_caught']} slipped={g['slipped_through']} rate={g['combined_catch_rate']:.3f}")
    print("dose_sha256=" + hashlib.sha256(json.dumps(dose_a, sort_keys=True).encode()).hexdigest())


if __name__ == "__main__":
    main()
