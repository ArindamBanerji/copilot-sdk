"""Execute one archived JM harness while forcing publication PNG output."""

from __future__ import annotations

import argparse
import os
import runpy
from pathlib import Path
from typing import Any, Callable

from matplotlib.figure import Figure


ROOT = Path(__file__).resolve().parent
ARCHIVED_SCRIPTS = {
    "E-JM-1": "e_jm_1_personnel_change.py",
    "E-JM-2": "e_jm_2_inversion_prevalence.py",
    "E-JM-3": "e_jm_3_cross_domain_transfer.py",
    "E-JM-4": "e_jm_4_conservation_vs_unconstrained.py",
    "E-JM-4b": "e_jm_4b_recalibration.py",
    "E-JM-5": "e_jm_5_weight_convergence.py",
    "E-JM-6": "e_jm_6_compounding_trajectory.py",
    "E-JM-6b": "e_jm_6b_baseline_ci.py",
    "E-JM-7": "e_jm_7_cross_type.py",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", choices=ARCHIVED_SCRIPTS)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Set PYTHONHASHSEED=0 for deterministic archived hash seeds")

    original_savefig: Callable[..., Any] = Figure.savefig

    def savefig_300(self: Figure, *save_args: Any, **save_kwargs: Any) -> Any:
        save_kwargs["dpi"] = 300
        save_kwargs.setdefault("facecolor", "white")
        return original_savefig(self, *save_args, **save_kwargs)

    Figure.savefig = savefig_300  # type: ignore[method-assign,assignment]
    os.chdir(ROOT)
    runpy.run_path(str(ROOT / ARCHIVED_SCRIPTS[args.experiment]), run_name="__main__")


if __name__ == "__main__":
    main()
