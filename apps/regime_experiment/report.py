"""JSON and dependency-free HTML report for EXP-REGIME."""

from __future__ import annotations

import html
import json
import math
from pathlib import Path
from typing import Any


COLORS = {"cold": "#616161", "A": "#1565c0", "B": "#6a1b9a", "C": "#2e7d32"}


def _json_safe(value: Any) -> Any:
    """Keep a report valid JSON even when a strategy converges at step zero."""

    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _line(values: list[float], width: int, height: int, maximum: float) -> str:
    if not values:
        return ""
    points = []
    for index, value in enumerate(values):
        x = 45 + (index / max(len(values) - 1, 1)) * (width - 65)
        y = 20 + (1.0 - min(max(float(value) / maximum, 0.0), 1.0)) * (height - 45)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def generate_report(results: dict[str, Any], output_dir: str | Path = ".") -> tuple[Path, Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / "report.json"
    html_path = destination / "report.html"
    json_path.write_text(
        json.dumps(_json_safe(results), indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )

    arms = results.get("arms", {})
    maximum = max((max(a.get("gt_distances", [0.0])) for a in arms.values()), default=1.0)
    maximum = max(float(maximum), float(results.get("threshold", 0.15)), 0.01)
    width, height = 900, 430
    paths = []
    legend = []
    rows = []
    for name, arm in arms.items():
        strategy = str(arm.get("strategy", ""))
        color = COLORS.get(strategy, "#455a64")
        points = _line(arm.get("gt_distances", []), width, height, maximum)
        if points:
            paths.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{points}"/>')
        gamma = arm.get("gamma_regime")
        gamma_text = "∞" if gamma == float("inf") else ("—" if gamma is None else f"{float(gamma):.3f}")
        legend.append(f'<span style="color:{color}">● {html.escape(name)} ({html.escape(strategy)})</span>')
        rows.append(
            "<tr>"
            f"<td>{html.escape(name)}</td><td>{html.escape(strategy)}</td>"
            f"<td>{arm.get('convergence_step', 'none')}</td><td>{gamma_text}</td>"
            f"<td>{arm.get('checkpoints_by_regime', {})}</td>"
            "</tr>"
        )
    threshold_y = 20 + (1.0 - min(float(results.get("threshold", 0.15)) / maximum, 1.0)) * (height - 45)
    break_x = 45
    body = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>EXP-REGIME γ_regime bake-off</title>
<style>body{{font-family:system-ui,sans-serif;background:#f5f7fa;color:#263238;margin:0}}main{{max-width:1100px;margin:auto;padding:28px}}.card{{background:white;border-radius:10px;padding:20px;margin:16px 0;box-shadow:0 1px 4px #0002}}h1{{margin-top:0}}svg{{width:100%;border:1px solid #ddd;background:#fff}}table{{border-collapse:collapse;width:100%}}td,th{{padding:9px;border-bottom:1px solid #ddd;text-align:left}}.legend span{{margin-right:18px}}.decision{{padding:12px;background:#e8f5e9;border-left:4px solid #2e7d32}}</style></head>
<body><main><h1>EXP-REGIME: A/B/C γ_regime bake-off</h1>
<p>Same generated decision stream, same phase oracles, four model-state arms. The metric is explicitly distinct from ε_firm.</p>
<div class="card"><h2>Ground-truth convergence after regime break</h2>
<p>Lower is better. Distance is normalized Frobenius distance to the phase-2 oracle centroids; canonical distance is not used.</p>
<svg viewBox="0 0 {width} {height}" role="img" aria-label="Post-break ground truth distance curves">
<line x1="45" y1="{height-25}" x2="{width-20}" y2="{height-25}" stroke="#333"/><line x1="45" y1="20" x2="45" y2="{height-25}" stroke="#333"/>
<line x1="{break_x}" y1="20" x2="{break_x}" y2="{height-25}" stroke="#999" stroke-dasharray="5,5"/><text x="50" y="35" font-size="12">regime break</text>
<line x1="45" y1="{threshold_y:.1f}" x2="{width-20}" y2="{threshold_y:.1f}" stroke="#ef6c00" stroke-dasharray="4,4"/><text x="55" y="{threshold_y-5:.1f}" font-size="12">threshold {float(results.get('threshold', 0.15)):.3f}</text>
{''.join(paths)}<text x="{width/2}" y="{height-3}" text-anchor="middle">post-break verified decisions</text><text x="12" y="{height/2}" transform="rotate(-90 12 {height/2})">GT distance</text></svg>
<p class="legend">{''.join(legend)}</p></div>
<div class="card"><h2>γ_regime results</h2><table><tr><th>Arm</th><th>Strategy</th><th>Convergence step</th><th>γ_regime</th><th>Evidence depth</th></tr>{''.join(rows)}</table></div>
<div class="card"><h2>Evidence and decision</h2><p>Decisions: {html.escape(str(results.get('decisions_per_regime')))}. Checkpoints are counted by regime and are not inferred from untagged legacy records.</p>
<p class="decision"><strong>Winner:</strong> {html.escape(str(results.get('winner') or 'none'))} — <strong>TRD-S7 recommendation:</strong> {html.escape(str(results.get('recommendation')))}. This recommendation changes only if the measured γ_regime exceeds 1 with adequate evidence.</p></div>
</main></body></html>"""
    html_path.write_text(body, encoding="utf-8")
    return json_path, html_path
