"""Small, dependency-free report for the build-your-own template."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _line(values: list[float], color: str, width: int = 760, height: int = 240) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = max(hi - lo, 1e-9)
    points = []
    for index, value in enumerate(values):
        x = 40 + (width - 60) * index / max(len(values) - 1, 1)
        y = 20 + (height - 45) * (1 - (value - lo) / span)
        points.append(f"{x:.1f},{y:.1f}")
    return f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{" ".join(points)}" />'


def generate_report(results: dict[str, Any], output_dir: str | Path = ".") -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    arms = results["arms"]
    colors = {"governed_ci": "#1565c0", "reward_max": "#c62828", "hand_specified_reward": "#6a1b9a"}
    curves = "".join(
        _line(arms[name]["quality_curve"], colors.get(name, "#455a64"))
        for name in arms
    )
    rows = []
    for name, arm in arms.items():
        final = arm["quality_curve"][-1] if arm["quality_curve"] else 0.0
        high = arm["high_risk_quality_curve"][-1] if arm["high_risk_quality_curve"] else 0.0
        rows.append(
            f"<tr><td>{html.escape(name)}</td><td>{final:.1%}</td>"
            f"<td>{high:.1%}</td><td>{len(arm['promotions'])}</td><td>{len(arm['rejections'])}</td></tr>"
        )
    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Build Your Own Copilot</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#263238}}.card{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:1rem;margin:1rem 0}}body{{background:#f5f7fa}}svg{{background:#fff;border:1px solid #ddd;width:100%}}table{{width:100%;border-collapse:collapse}}th,td{{padding:.5rem;border-bottom:1px solid #ddd;text-align:left}}.ci{{color:#1565c0}}.rm{{color:#c62828}}</style></head>
<body><h1>Build Your Own Copilot: {html.escape(results['domain'])}</h1>
<p>Same synthetic metadata stream, with governed and ungoverned decision architectures.</p>
<div class="card"><h2>Compounding quality</h2><svg viewBox="0 0 760 240" role="img" aria-label="quality curves">{curves}</svg>
<p><span class="ci">Blue: governed CI</span> · <span class="rm">Red: reward-max</span> · Purple: hand-specified reward. X-axis: decisions; Y-axis: rolling verified quality.</p></div>
<div class="card"><h2>Conservation and safety</h2><p>Governed learning records conservation state and evaluates the poisoned rule through the promotion gate. Reward-max has no conservation gate.</p>
<table><thead><tr><th>Arm</th><th>Final quality</th><th>High-risk quality</th><th>Promotions</th><th>Rejections</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<div class="card"><h2>Oracle boundary</h2><p>The generator emits category and factor metadata only. Verified actions come from the separate oracle adapter and are never produced by the generator.</p></div>
</body></html>"""
    report_path = output / "report.html"
    report_path.write_text(html_doc, encoding="utf-8")
    return report_path


__all__ = ["generate_report"]
