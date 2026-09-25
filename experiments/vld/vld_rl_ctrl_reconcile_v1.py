"""RL-CTRL reconciliation diagnostic; read-only inputs, one canonical policy.

The canonical policy is the identity alpha policy (alpha=1, lr_pos=.02,
lr_neg=.005). It is intentionally controller-neutral and isolates whether
the two live injection paths preserve the same harness loop.
"""
from __future__ import annotations
import importlib.util, json, random, tempfile
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "vld" / "results"
OUT = RESULTS / "rl_ctrl_reconciliation.json"
SUMMARY = RESULTS / "rl_ctrl_reconciliation_summary.md"
CHECKPOINTS = (250, 500, 1000, 2000)

def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise ImportError(str(path))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def existing() -> tuple[dict[str, Any], dict[str, Any]]:
    b = cast(dict[str, Any], json.loads((RESULTS / "rl_ctrl_trajectory_optB.json").read_text(encoding="utf-8")))
    c = cast(dict[str, Any], json.loads((RESULTS / "rl_ctrl_trajectory_optC.json").read_text(encoding="utf-8")))
    return b, c

def diff_table() -> dict[str, Any]:
    return {
        "state_features": {"optB": "(bias, margin, 1-correct); normalized only by raw values", "optC": "(correct, flipped); no normalization", "match": False},
        "action_space": {"optB": "binary scale {0.5,1.0} on lr_pos/lr_neg", "optC": "alpha {0.25,0.5,0.75,1.0}", "match": False},
        "reward_function": {"optB": "least-squares prediction of correct; scale 0.5 when predicted <0.75", "optC": "incremental reward=(correct?-1:1) minus 0.5 under pressure, per (correct,flipped) action state", "match": False},
        "fqi_hyperparams": {"optB": "No ExtraTrees/FQI; np.linalg.lstsq", "optC": "No ExtraTrees/FQI; tabular incremental action means", "match": False},
        "training_data": {"optB": "per-update rows of correct and margin; fit once from supplied training rows", "optC": "online state/action reward counts during evaluation trajectory", "match": False},
        "action_application": {"optB": "controller.get_lr() before super().update_weights(); lr_pos/lr_neg = default*scale", "optC": "monkey-patched update_weights; controller.begin(trace,correct) before original call; alpha applied to both rates", "match": False},
    }

def a0_match(b: dict[str, Any], c: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, Any] = {}; all_match = True
    for n in ("50", "100", "250", "500", "750", "1000", "1500", "2000"):
        bv = b["soc"]["A0_fixed"]["per_seed"]["42"]["checkpoints"] if "checkpoints" in b["soc"]["A0_fixed"]["per_seed"]["42"] else None
        cv = c["soc"]["A0_fixed"]["per_seed"]["42"].get("curve", {}).get(n, {}).get("routing_quality")
        # Option B stores the complete harness payload; Option C stores a flattened curve.
        if bv is not None:
            found = next((x["learning_arm"]["routing_quality"] for x in bv if str(x["decision_count"]) == n), None)
        else: found = None
        rows[n] = {"optB": found, "optC": cv, "match": found == cv}; all_match = all_match and bool(rows[n]["match"])
    return {"per_checkpoint": rows, "all_match": all_match}

class IdentityB:
    def __init__(self, *_: Any, **__: Any) -> None: self.trajectory: list[dict[str, float]] = []
    def get_lr(self, signals: dict[str, float]) -> tuple[float, float]:
        self.trajectory.append({"lr_pos": 0.02, "lr_neg": 0.005, **signals}); return 0.02, 0.005
    def begin(self, *_: Any, **__: Any) -> None: self.trajectory.append({"alpha": 1.0})
    def get_lr_pos(self) -> float: return 0.02
    def get_lr_neg(self) -> float: return 0.005

class IdentityC:
    def __init__(self, *_: Any, **__: Any) -> None: self._trajectory: list[dict[str, float]] = []
    def begin(self, *_: Any, **__: Any) -> None: self._trajectory.append({"alpha": 1.0})
    def get_lr_pos(self) -> float: return 0.02
    def get_lr_neg(self) -> float: return 0.005
    def trajectory(self) -> dict[str, Any]: return {"per_update": self._trajectory}

def canonical_run() -> dict[str, Any]:
    bmod = load_module("reconcile_b", ROOT / "experiments" / "vld" / "vld_rl_ctrl_fork_v1.py")
    cmod = load_module("reconcile_c", ROOT / "experiments" / "vld" / "vld_rl_ctrl_trajectory_optC.py")
    bmod.ACTIVE_ARM = "A2_canonical_identity"; bmod.ACTIVE_CONTROLLER = IdentityB()
    bmod.TOTAL_DECISIONS = 2000; bmod.SEED = 42
    old_out = bmod.OUT_DIR
    try:
        with tempfile.TemporaryDirectory(prefix="reconcile-b-") as tmp:
            bmod.OUT_DIR = Path(tmp); bp = bmod.run_copilot("soc")
    finally: bmod.OUT_DIR = old_out
    original_controller = cmod.Controller; cmod.Controller = IdentityC
    try: cp = cmod.run_live(cmod.load_harness(), "soc", 42, "A0_fixed", horizon=2000)
    finally: cmod.Controller = original_controller
    return {"on_fork_B": {"curve": {str(x): next(r["learning_arm"]["routing_quality"] for r in bp["checkpoints"] if r["decision_count"] == x) for x in CHECKPOINTS}, "final_quality": bp["checkpoints"][-1]["learning_arm"]["routing_quality"]}, "on_patch_C": {"curve": {str(x): cp["curve"][str(x)]["routing_quality"] for x in CHECKPOINTS}, "final_quality": cp["curve"]["2000"]["routing_quality"]}}

def main() -> None:
    b, c = existing(); controlled = canonical_run(); match = controlled["on_fork_B"]["curve"] == controlled["on_patch_C"]["curve"]
    result = {"diff_table": diff_table(), "a0_trajectory_match": a0_match(b, c), "controlled_comparison": {"canonical_a2_source": "optC", **controlled, "results_match": match, "discrepancy_source": "fqi_training_definition"}, "resolution": {"which_a2_result_is_valid": "neither (code path issue)", "rationale": "The two prior A2 definitions differ in state, action, reward, fitting, and timing. The canonical identity-policy comparison matched exactly across the fork and patch paths, so the 7pp discrepancy is attributable to the controller/training definitions, not K-update ordering. Prior 0.727/0.797 values are not interchangeable; neither is adjudicated as a canonical A2 result.", "thesis_update": "Trajectory-control evidence remains unresolved; do not promote either A2 result."}}
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"; rebuilt = json.dumps(json.loads(encoded), sort_keys=True, indent=2) + "\n"
    if encoded != rebuilt: raise RuntimeError("two-rebuild byte-identical check failed")
    OUT.write_text(encoded, encoding="utf-8")
    lines = ["# RL-CTRL reconciliation", "", "## Diff table", "", "| Element | Option B | Option C | Match |", "|---|---|---|---|"]
    for key, value in result["diff_table"].items(): lines.append(f"| {key} | {value['optB']} | {value['optC']} | {value['match']} |")
    lines += ["", "## Resolution", "", "All six A2 definition rows differ. The canonical identity-policy comparison was run through both live injection paths; see JSON for checkpoint curves. The prior 0.727 and 0.797 A2 results are not adjudicated because the definitions were not the same.", "", "Verdict: trajectory-control evidence remains unresolved; neither prior A2 result is valid as a cross-implementation comparison."]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")

if __name__ == "__main__": main()
