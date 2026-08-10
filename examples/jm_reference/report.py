"""Offline report generator for the JM Reference App.

The output contains raw JSON plus a self-contained HTML document.  Charts use
inline SVG only, so the report works without a server, JavaScript, or network.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Sequence


def generate_report(
    traj_a: dict[str, Any],
    traj_b: dict[str, Any],
    output_dir: str | Path = ".",
) -> dict[str, str]:
    """Write ``report.json`` and ``report.html`` and return their paths."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    report_data = {
        "schema_version": 1,
        "run_a": traj_a,
        "run_b": traj_b,
        "comparison": _compare(traj_a, traj_b),
    }
    json_path = output / "report.json"
    html_path = output / "report.html"
    json_path.write_text(json.dumps(report_data, indent=2, default=str), encoding="utf-8")
    html_path.write_text(_render_html(traj_a, traj_b), encoding="utf-8")
    print(f"Report written to {json_path} and {html_path}")
    return {"json": str(json_path), "html": str(html_path)}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _compare(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Return the two-run comparison used by the JSON report."""

    def accuracy(trajectory: dict[str, Any]) -> float:
        decisions = trajectory.get("decisions", [])
        if not decisions:
            return 0.0
        return 100.0 * sum(bool(item.get("correct")) for item in decisions) / len(decisions)

    return {
        "run_a_final_distance": a.get("final_distance"),
        "run_b_final_distance": b.get("final_distance"),
        "run_a_final_gt_distance": a.get("final_gt_distance"),
        "run_b_final_gt_distance": b.get("final_gt_distance"),
        "run_a_final_iks": a.get("final_iks"),
        "run_b_final_iks": b.get("final_iks"),
        "run_a_correct_pct": accuracy(a),
        "run_b_correct_pct": accuracy(b),
        "run_a_epsilon_firm": a.get("final_epsilon_firm"),
        "run_b_epsilon_firm": b.get("final_epsilon_firm"),
    }


def _svg_line_chart(
    first: Sequence[Any],
    second: Sequence[Any],
    first_name: str,
    second_name: str,
    y_label: str,
    chart_id: str,
    disruption_step: int | None = None,
    colors: tuple[str, str] = ("#1565c0", "#ef6c00"),
) -> str:
    """Render two numeric series as a compact, responsive inline SVG."""

    width, height = 900, 280
    left, right, top, bottom = 58, 18, 20, 42
    series = [[_number(value) for value in values] for values in (first, second)]
    all_values = [value for values in series for value in values]
    max_value = max(all_values, default=1.0)
    min_value = min(all_values, default=0.0)
    if max_value == min_value:
        max_value = min_value + 1.0
    x_count = max(len(values) for values in series) if series else 1
    plot_width = width - left - right
    plot_height = height - top - bottom

    def point(index: int, value: float) -> str:
        x = left + (index / max(x_count - 1, 1)) * plot_width
        y = top + (1 - (value - min_value) / (max_value - min_value)) * plot_height
        return f"{x:.1f},{y:.1f}"

    lines = []
    for values, color in zip(series, colors):
        if values:
            lines.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="2" '
                f'points="{" ".join(point(i, value) for i, value in enumerate(values))}"/>'
            )
    disruption = ""
    if disruption_step is not None and x_count > 1:
        x = left + (disruption_step / max(x_count - 1, 1)) * plot_width
        disruption = (
            f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{height-bottom}" '
            'stroke="#c62828" stroke-dasharray="5 4"/>'
            f'<text x="{x + 5:.1f}" y="{top + 14}" fill="#c62828" font-size="12">'
            f'disruption {disruption_step}</text>'
        )
    return (
        f'<svg id="{html.escape(chart_id)}" viewBox="0 0 {width} {height}" '
        'role="img" aria-label="trajectory chart">'
        f'<line x1="{left}" x2="{left}" y1="{top}" y2="{height-bottom}" stroke="#777"/>'
        f'<line x1="{left}" x2="{width-right}" y1="{height-bottom}" y2="{height-bottom}" stroke="#777"/>'
        f'<text x="8" y="{top + plot_height/2:.1f}" fill="#444" font-size="12">{html.escape(y_label)}</text>'
        f'<text x="{width/2:.1f}" y="{height-8}" text-anchor="middle" fill="#444" font-size="12">decision</text>'
        + disruption
        + "".join(lines)
        + f'<text x="{width-210}" y="20" fill="{colors[0]}" font-size="12">● {html.escape(first_name)}</text>'
        + f'<text x="{width-210}" y="38" fill="{colors[1]}" font-size="12">● {html.escape(second_name)}</text>'
        + "</svg>"
    )


def _accuracy_series(decisions: Sequence[dict[str, Any]], window: int = 25) -> list[float]:
    values: list[float] = []
    for index in range(len(decisions)):
        sample = decisions[max(0, index - window + 1): index + 1]
        values.append(100.0 * sum(bool(item.get("correct")) for item in sample) / len(sample))
    return values


def _conservation_summary(states: Sequence[Any]) -> str:
    counts: dict[str, int] = {}
    for state in states:
        status = str(state.get("status", "UNKNOWN")) if isinstance(state, dict) else str(state)
        counts[status] = counts.get(status, 0) + 1
    if not counts:
        return "no observations"
    return ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))


def _measurement_summary(states: Sequence[Any]) -> tuple[str, str]:
    observed: list[str] = []
    provenances: list[str] = []
    for item in states:
        if not isinstance(item, dict):
            continue
        state = str(item.get("state", "0")).upper()
        if not observed or observed[-1] != state:
            observed.append(state)
        provenance = str(item.get("provenance", ""))
        if provenance and provenance not in provenances:
            provenances.append(provenance)
    return (
        " → ".join(observed) if observed else "0",
        ", ".join(provenances) if provenances else "none",
    )


def _render_html(traj_a: dict[str, Any], traj_b: dict[str, Any]) -> str:
    """Render all APP-1 compounding surfaces in one offline document."""

    a_eps = _number(traj_a.get("final_epsilon_firm"))
    b_eps = _number(traj_b.get("final_epsilon_firm"))
    disruption = traj_a.get("disruption_step")
    a_measurement, a_provenance = _measurement_summary(traj_a.get("measurement_states", []))
    b_measurement, b_provenance = _measurement_summary(traj_b.get("measurement_states", []))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JM Reference App — Compounding Report</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 1180px; margin: 0 auto; padding: 20px; color: #263238; }}
h1 {{ color: #1a237e; }} h2 {{ color: #283593; border-bottom: 2px solid #e8eaf6; padding-bottom: 8px; }}
.metrics {{ display: flex; flex-wrap: wrap; gap: 10px; }}
.metric {{ padding: 12px 18px; border-radius: 8px; background: #e8f5e9; }}
.metric.amber {{ background: #fff3e0; }} .chart {{ margin: 12px 0 28px; }}
svg {{ width: 100%; height: auto; min-height: 240px; }}
table {{ border-collapse: collapse; width: 100%; }} th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #f5f5f5; }} footer {{ margin-top: 30px; color: #546e7a; }}
</style>
</head>
<body>
<h1>Judgment Memory — Compounding Report</h1>
<p>Oracle-separated synthetic reference run; SQLite-backed, zero server.</p>
<div class="metrics">
<div class="metric">Run A ε_firm: <strong>{a_eps:.4f}</strong> ({'above' if a_eps > 0.128 else 'below'} 0.128)</div>
<div class="metric {'green' if b_eps <= 0.128 else 'amber'}">Run B ε_firm: <strong>{b_eps:.4f}</strong> ({'above' if b_eps > 0.128 else 'below'} 0.128)</div>
<div class="metric">Run A final IKS: <strong>{_number(traj_a.get('final_iks')):.1f}</strong></div>
<div class="metric amber">Run B final IKS: <strong>{_number(traj_b.get('final_iks')):.1f}</strong></div>
</div>

<h2>1a. Distance to Ground Truth (convergence proof — oracle only)</h2>
<p>Decreases as learned centroids converge toward correct answers. This oracle-only curve is not available to production scoring.</p>
<div class="chart">{_svg_line_chart(traj_a.get('gt_distances', []), traj_b.get('gt_distances', []), 'Run A', 'Run B', 'ground-truth distance', 'ground-truth-distance', disruption, ("#2e7d32", "#66bb6a"))}</div>

<h2>1b. Distance to Canonical Prior (learning signal — production available)</h2>
<p>Increases as the system learns its environment. This is the same centroid-drift basis used by IKS.</p>
<div class="chart">{_svg_line_chart(traj_a.get('centroid_distances', []), traj_b.get('centroid_distances', []), 'Run A', 'Run B', 'canonical distance', 'centroid-distance', disruption, ("#1565c0", "#42a5f5"))}</div>

<h2>2. Institutional Knowledge Score (IKS)</h2>
<div class="chart">{_svg_line_chart(traj_a.get('iks_values', []), traj_b.get('iks_values', []), 'Run A', 'Run B', 'IKS', 'iks', disruption)}</div>

<h2>3. Conservation Status</h2>
<table><tr><th>Run</th><th>Observed status counts</th><th>Final state</th></tr>
<tr><td>Run A</td><td>{html.escape(_conservation_summary(traj_a.get('conservation_states', [])))}</td><td>{html.escape(str((traj_a.get('conservation_states') or [{}])[-1]))}</td></tr>
<tr><td>Run B</td><td>{html.escape(_conservation_summary(traj_b.get('conservation_states', [])))}</td><td>{html.escape(str((traj_b.get('conservation_states') or [{}])[-1]))}</td></tr></table>

<h2>4. Measurement State</h2>
<p>Honesty ladder: 0 → INSTRUMENT_VALIDATED → ACCUMULATING → MEASURED. A measured state uses provenance <code>real_measured</code>; sample provenance is never accepted.</p>
<table><tr><th>Run</th><th>Observed ladder</th><th>Provenance observed</th></tr>
<tr><td>Run A</td><td>{html.escape(a_measurement)}</td><td>{html.escape(a_provenance)}</td></tr>
<tr><td>Run B</td><td>{html.escape(b_measurement)}</td><td>{html.escape(b_provenance)}</td></tr></table>

<h2>5. ε_firm Threshold</h2>
<p>Run A: {a_eps:.4f}; Run B: {b_eps:.4f}; threshold: 0.128. The two configurations intentionally demonstrate conditional re-convergence claims.</p>

<h2>6. Rolling Accuracy</h2>
<div class="chart">{_svg_line_chart(_accuracy_series(traj_a.get('decisions', [])), _accuracy_series(traj_b.get('decisions', [])), 'Run A', 'Run B', 'accuracy %', 'accuracy', disruption)}</div>

<h2>7. Evolution and Disruption</h2>
<p>Disruption decision: {html.escape(str(disruption))}. Agent evolution events observed: Run A {len(traj_a.get('evolution_events', []))}; Run B {len(traj_b.get('evolution_events', []))}.</p>
<footer>Generated by the JM Reference App. The generator emits factor vectors only; the oracle is the sole correctness authority.</footer>
</body>
</html>"""
