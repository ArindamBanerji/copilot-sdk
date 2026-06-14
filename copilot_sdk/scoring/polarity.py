"""Factor polarity metadata for display interpretation."""

from __future__ import annotations


class Polarity:
    """Factor polarity metadata for display/interpretation.

    POSITIVE (1): Higher value = better/favorable outcome.
    NEGATIVE (-1): Higher value = worse/concerning outcome.
    NEUTRAL (0): No inherent direction - value is contextual.

    This is DISPLAY metadata only. The scorer's L2 kernel computes
    distance from centroid regardless of polarity. Polarity affects
    how NL templates and frontend components describe factor values.
    """

    POSITIVE = 1
    NEGATIVE = -1
    NEUTRAL = 0


def get_factor_polarities(domain: str) -> dict[str, int]:
    """Return {factor_name: polarity} for a domain.

    Reads from the preset's factor_polarities attribute if present.
    Falls back to NEUTRAL (0) for all factors if not defined.
    Unknown domain returns empty dict.
    """
    from copilot_sdk.scoring.presets import PRESET_REGISTRY

    preset_cls = PRESET_REGISTRY.get(domain)
    if preset_cls is None:
        return {}

    preset = preset_cls()
    polarities = getattr(preset, "factor_polarities", None)
    if polarities is not None:
        return dict(polarities)

    return {name: Polarity.NEUTRAL for name in preset.shape.factor_names}


def interpret_factor(
    name: str,
    value: float,
    polarity: int,
    threshold_high: float = 0.7,
    threshold_low: float = 0.3,
) -> str:
    """Generate human-readable interpretation of a factor value.

    Returns strings like:
      POSITIVE + 0.85 -> "high (favorable)"
      POSITIVE + 0.15 -> "low (concerning)"
      NEGATIVE + 0.85 -> "high (concerning)"
      NEGATIVE + 0.15 -> "low (favorable)"
      NEUTRAL  + 0.85 -> "high"
      any      + 0.50 -> "moderate"
    """
    if value >= threshold_high:
        level = "high"
    elif value <= threshold_low:
        level = "low"
    else:
        return "moderate"

    if polarity == Polarity.NEUTRAL:
        return level

    if polarity == Polarity.POSITIVE:
        qualifier = "favorable" if level == "high" else "concerning"
    else:
        qualifier = "concerning" if level == "high" else "favorable"

    return f"{level} ({qualifier})"
