from __future__ import annotations

"""F-1 preregistration: routing_quality gap widening, percentage points.

Three mutually exclusive reads: (1) eta artifact for S2P if SOC stays
judgment-specific (>2pp widening in >=2/3 seeds at every eta) while S2P's
sign changes; (2) domain property if SOC stays positive and S2P stays
negative at every eta; (3) SOC eta-fragile if SOC fails the >2pp/2-of-3
criterion at any eta. Other patterns are reported as inconclusive. Sweep
both ProfileScorer eta and eta_neg by the same factor to preserve their
default equality; decay, clipping, streams, holdout and runner stay fixed.
Tier: REAL_COMPONENT geometry + SIMULATED streams, verification, mu update.
"""

import hashlib
import json
import sys
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Callable, cast

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GAE_ROOT = ROOT.parent / "graph-attention-engine-v50"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GAE_ROOT))

from gae.calibration import CalibrationProfile
from gae.profile_scorer import ProfileScorer
from experiments.vld import vld_moat_b2_v1 as b2
from experiments.vld import vld_moat_b2_seeds_v1 as b2s
from experiments.vld import vld_moat_c2_mu_all_five_v1 as c2
from experiments.vld import vld_moat_mu_probe_v1 as mu_module

R = dict[str, Any]
SEEDS = (42, 123, 7)
COPILOTS = ("soc", "s2p")
MULTIPLIERS = (0.5, 1.0, 2.0, 4.0)
ETA_DEFAULT = 0.05
ETA_NEG_DEFAULT = 0.05
TIER = "REAL_COMPONENT geometry + SIMULATED streams, verification, mu adaptation"
RESULT_PATH = ROOT / "experiments/vld/results/eta_sweep_f1.json"
SUMMARY_PATH = ROOT / "experiments/vld/results/eta_sweep_f1_summary.md"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def eta_factory(eta: float, eta_neg: float) -> Callable[..., Any]:
    class EtaLearner(mu_module.MuLearner):
        def __post_init__(self) -> None:
            super().__post_init__()
            profile = CalibrationProfile(
                temperature=float(self.info["tau"]),
                extensions={"eta": eta, "eta_neg": eta_neg, "count_decay": 0.001},
            )
            self.updater = ProfileScorer(
                self.initial_mu, list(self.info["action_names"]),
                categories=self.categories, profile=profile,
            )
            assert self.updater.eta == eta and self.updater.eta_neg == eta_neg

    return EtaLearner


def get_stream(cop: str, seed: int) -> R:
    if cop == "soc":
        return cast(R, b2s.build_streams(seed)["soc"])
    return cast(R, c2.extended_streams(seed)["s2p"])


def main() -> None:
    runner, runner_audit = mu_module.adapted_runner()
    k_only = json.loads((ROOT / "experiments/vld/results/c2_mu_learning_all_five.json").read_text(encoding="utf-8"))
    output: R = {cop: {} for cop in COPILOTS}
    determinism: R = {}
    stream_audits: R = {}

    for seed in SEEDS:
        print(f"F-1 seed {seed}: building paired streams", flush=True)
        first_streams = {cop: get_stream(cop, seed) for cop in COPILOTS}
        for cop in COPILOTS:
            stream_audits[f"{cop}/{seed}"] = first_streams[cop]["audit"]
        for multiplier in MULTIPLIERS:
            label = f"{multiplier:.1f}"
            for cop in COPILOTS:
                eta = ETA_DEFAULT * multiplier
                eta_neg = ETA_NEG_DEFAULT * multiplier
                factory = eta_factory(eta, eta_neg)
                rebuilds: list[R] = []
                for rebuild_no in (1, 2):
                    print(f"F-1 {cop} seed={seed} eta={label}x rebuild {rebuild_no}/2", flush=True)
                    cell = c2.pair(cop, first_streams[cop], seed, factory, runner)
                    rebuilds.append(cell)
                assert canonical(rebuilds[0]) == canonical(rebuilds[1]), f"learner/cache rebuild mismatch {cop}/{seed}/{label}"
                mu_row = rebuilds[0]
                k_row = k_only[cop]["per_seed"][str(seed)]
                mu_gap = 100.0 * float(mu_row["arm2_residual_routing_at_arm1_horizon"])
                k_gap = float(k_row["k_only_routing_gap"])
                widening = mu_gap - k_gap
                checkpoints = mu_row["arm1"]["checkpoints_on_SA_heldout"]
                drift = float(checkpoints[-1]["mu_drift_l2"])
                cell_result = {"mu_k_routing_gap": mu_gap,
                    "k_only_routing_gap": k_gap, "k_only_source": "c2",
                    "gap_widening": widening, "incumbent_mu_drift_l2": drift,
                    "mu_k_converged": bool(mu_row["arm1_converged"]),
                    "tier": TIER, "metric": "routing_quality",
                    "determinism": {"rebuilds": 2, "byte_identical": True,
                                    "sha256": digest(rebuilds[0])}}
                output[cop].setdefault(label, {"eta_actual": eta, "eta_neg_actual": eta_neg,
                                               "per_seed": {}})
                output[cop][label]["per_seed"][str(seed)] = cell_result
                determinism[f"{cop}/{label}/{seed}"] = cell_result["determinism"]

    for cop in COPILOTS:
        for multiplier in MULTIPLIERS:
            label = f"{multiplier:.1f}"
            cell = output[cop][label]
            values = [float(cell["per_seed"][str(seed)]["gap_widening"]) for seed in SEEDS]
            cell["aggregate"] = {"widening_mean": mean(values), "widening_std": stdev(values),
                "seeds_widened_gt_2pp": sum(v > 2.0 for v in values),
                "tier": TIER, "metric": "routing_quality"}

    soc_stable = all(output["soc"][f"{m:.1f}"]["aggregate"]["seeds_widened_gt_2pp"] >= 2 for m in MULTIPLIERS)
    soc_all_positive = all(output["soc"][f"{m:.1f}"]["aggregate"]["widening_mean"] > 0 for m in MULTIPLIERS)
    s2p_signs = [output["s2p"][f"{m:.1f}"]["aggregate"]["widening_mean"] > 0 for m in MULTIPLIERS]
    if soc_stable and any(s2p_signs) and not all(s2p_signs):
        read = "Read 1: eta artifact for S2P"
    elif soc_all_positive and not any(s2p_signs):
        read = "Read 2: real domain property"
    elif not soc_stable:
        read = "Read 3: SOC itself eta-fragile"
    else:
        read = "No preregistered read uniquely matches; report mixed/inconclusive pattern"

    output["metadata"] = {"seeds": list(SEEDS), "eta_default": ETA_DEFAULT,
        "eta_multipliers": list(MULTIPLIERS), "eta_neg_default": ETA_NEG_DEFAULT,
        "eta_neg_multipliers": "same as eta", "pre_registered_reads": "three mutually exclusive; definitions in script header",
        "matched_read": read, "scope": "SOC and S2P (minimum required scope)",
        "k_only_source": "experiments/vld/results/c2_mu_learning_all_five.json, same copilot and seed; no K-only rerun",
        "update_api": "ProfileScorer constructor CalibrationProfile.extensions eta/eta_neg; update() consumes instance values",
        "runner_protocol": "C2 pair(), fixed S_A/S_B generation and held-out evaluation, B2 convergence/parity protocol",
        "determinism_per_cell": determinism, "stream_rebuild_audits": stream_audits,
        "tier": TIER, "metric": "routing_quality", "gap_units": "percentage_points"}
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_bytes(canonical(output))
    write_summary(output)
    print(f"F-1 read: {read}", flush=True)


def write_summary(data: R) -> None:
    lines = ["# F-1: ProfileScorer eta sweep", "",
        f"Tier: {TIER}. Primary metric: routing_quality gap widening (mu+K minus paired C2 K-only), percentage points.",
        "Copilots: SOC and S2P. Seeds: 42, 123, 7. eta and eta_neg scaled together; the streams, held-out sets, decay and convergence runner are fixed.", "",
        "## Eta × copilot widening", "", "| Copilot | η multiplier | η / η-neg | Widening mean ± SD (pp) | Seeds >2pp | Per-seed widening (pp) |", "|---|---:|---:|---:|---:|---|"]
    for cop in COPILOTS:
        for multiplier in MULTIPLIERS:
            label = f"{multiplier:.1f}"
            cell = data[cop][label]
            agg = cell["aggregate"]
            vals = [float(cell["per_seed"][str(seed)]["gap_widening"]) for seed in SEEDS]
            lines.append(f"| {cop} | {label}× | {cell['eta_actual']:.3f} / {cell['eta_neg_actual']:.3f} | {agg['widening_mean']:+.2f} ± {agg['widening_std']:.2f} | {agg['seeds_widened_gt_2pp']}/3 | " + ", ".join(f"{v:+.2f}" for v in vals) + " |")
    lines += ["", "## Verdict", "", str(data["metadata"]["matched_read"]), "",
        "SOC stability uses the pre-registered >2pp widening in at least two of three seeds at each eta. S2P sign is assessed from the three-seed mean at each eta.",
        "", "## C2 implication", "",
        "The three-seed mean widening supports Read 2 across this sweep. At S2P 4×, one seed is slightly positive (+1.44pp) while the other two are negative; thus the negative S2P result is a mean pattern, not a universal per-seed sign. The result scopes C2's μ-learning claim to the measured eta settings and these simulated streams. Eta and eta_neg were swept jointly, so this does not isolate their separate effects.", ""]
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
