"""Populate day-zero readiness entries for measurement-gated features."""

from .readiness import DayZeroReadiness


def populate_default_readiness() -> list[DayZeroReadiness]:
    """Day-zero readiness entries for all measurement-gated features."""
    entries: list[DayZeroReadiness] = []

    entries.append(
        DayZeroReadiness(
            feature="P73-par-intelligence",
            copilot="purchasing",
            populated=True,
            proven=False,
            instrumented=False,
            real_path_committed=True,
            labels_honest=True,
        )
    )
    entries.append(
        DayZeroReadiness(
            feature="P74-iks-scorecard",
            copilot="purchasing",
            populated=True,
            proven=False,
            instrumented=False,
            real_path_committed=True,
            labels_honest=True,
        )
    )
    entries.append(
        DayZeroReadiness(
            feature="P75-trust-analysis",
            copilot="purchasing",
            populated=True,
            proven=False,
            instrumented=False,
            real_path_committed=True,
            labels_honest=True,
        )
    )
    entries.append(
        DayZeroReadiness(
            feature="SOC-campaign-intelligence",
            copilot="soc",
            populated=True,
            proven=True,
            instrumented=True,
            real_path_committed=True,
            labels_honest=True,
        )
    )
    entries.append(
        DayZeroReadiness(
            feature="S2P-supplier-enrichment",
            copilot="s2p",
            populated=True,
            proven=False,
            instrumented=True,
            real_path_committed=True,
            labels_honest=True,
        )
    )
    entries.append(
        DayZeroReadiness(
            feature="P53-trust-radar",
            copilot="trading",
            populated=True,
            proven=False,
            instrumented=False,
            real_path_committed=True,
            labels_honest=True,
        )
    )
    entries.append(
        DayZeroReadiness(
            feature="P34-intelligence-map",
            copilot="dataops",
            populated=True,
            proven=False,
            instrumented=False,
            real_path_committed=True,
            labels_honest=True,
        )
    )

    return entries
