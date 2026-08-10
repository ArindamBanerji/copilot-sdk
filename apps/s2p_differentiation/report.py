"""Dependency-free APP-4B dashboard generated from ``report.json``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _payload_for_display(result: dict[str, Any]) -> dict[str, Any]:
    payload = dict(result)
    payload["display"] = {
        "epsilon_firm": 0.20,
        "measurement_state_ladder": [
            "COLD_START",
            "CALIBRATING",
            "LEARNING",
            "CONVERGING",
            "INSTRUMENT_VALIDATED",
        ],
        "epsilon_firm_note": "S2P oracle configuration used by APP-4A.",
    }
    return payload


def write_report(result: dict[str, Any], output_dir: str | Path = ".") -> tuple[Path, Path]:
    """Write the JSON data and the file-safe five-tab HTML dashboard."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "report.json"
    html_path = output / "report.html"
    payload = _payload_for_display(result)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # The inline copy makes file:// opening work; the page also attempts to
    # fetch report.json, so the same artifact works when served statically.
    embedded = json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")
    html_path.write_text(_dashboard_html(embedded), encoding="utf-8")
    return json_path, html_path


def generate_report(result: dict[str, Any], output_dir: str | Path = ".") -> tuple[Path, Path]:
    """Compatibility alias for callers that use the APP-4 report verb."""

    return write_report(result, output_dir)


def _dashboard_html(embedded_json: str) -> str:
    return r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>S2P Differentiation — Governed vs Ungoverned</title>
<style>
:root{--ink:#172033;--muted:#637083;--paper:#fff;--wash:#f3f6fa;--navy:#172554;--blue:#1565c0;--red:#c62828;--purple:#6a1b9a;--green:#2e7d32;--amber:#e65100;--line:#dce3ec}
*{box-sizing:border-box}body{margin:0;background:var(--wash);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}.header{background:linear-gradient(120deg,#172554,#283593);color:#fff;padding:28px max(24px,calc((100% - 1180px)/2))}.header h1{margin:0 0 6px;font-size:clamp(24px,4vw,38px)}.header p{color:#dbe4ff;margin:0}.tabs{background:#283593;display:flex;overflow-x:auto;padding:0 max(12px,calc((100% - 1180px)/2))}.tab{border:0;background:none;color:#c5d0f5;cursor:pointer;font:inherit;font-weight:650;padding:15px 18px;white-space:nowrap;border-bottom:3px solid transparent}.tab:hover,.tab.active{color:#fff;border-bottom-color:#ffc107}.main{max-width:1180px;margin:auto;padding:20px 18px 48px}.panel{display:none}.panel.active{display:block}.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;box-shadow:0 2px 8px #1720330d;margin:16px 0;padding:20px}.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}.metric{border-left:4px solid var(--blue);padding:12px 14px;background:#f8fbff;border-radius:8px}.metric strong{display:block;font-size:25px}.metric small,.muted{color:var(--muted)}.ci{color:var(--blue)}.reward{color:var(--red)}.hand{color:var(--purple)}.good{color:var(--green)}.bad{color:var(--red)}.warn{color:var(--amber)}.chart{overflow-x:auto}.chart svg{display:block;min-width:680px;width:100%;height:auto}.legend{display:flex;flex-wrap:wrap;gap:16px;margin:8px 0 0}.legend span{font-weight:650}.swatch{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:5px;vertical-align:-1px}table{border-collapse:collapse;width:100%;background:var(--paper)}th,td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}th{background:#f7f9fc;color:#39465a}tr:last-child td{border-bottom:0}.scroll{overflow:auto}.pill{display:inline-block;border-radius:999px;padding:3px 9px;font-weight:700;font-size:12px}.pill.green{background:#e8f5e9;color:var(--green)}.pill.red{background:#ffebee;color:var(--red)}.pill.amber{background:#fff3e0;color:var(--amber)}.pill.gray{background:#eef1f5;color:#536174}.callout{border-left:4px solid #ffc107;background:#fffdf3;padding:12px 15px}.status-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}.status-card{border:1px solid var(--line);border-radius:10px;padding:15px}.status-card h3{margin-top:0}.small{font-size:12px}.axis{fill:#637083;font-size:12px}.gridline{stroke:#e6ebf2;stroke-width:1}.plotline{fill:none;stroke-width:3;stroke-linejoin:round;stroke-linecap:round}.dashed{stroke-dasharray:6 5}.hidden{display:none}
</style>
</head>
<body>
<header class="header"><h1>S2P Differentiation</h1><p>Three arms. Same decisions. Same oracle. The difference is the architecture.</p></header>
<nav class="tabs" aria-label="APP-4B dashboard tabs">
 <button class="tab" data-tab="compounding">Compounding Curve</button>
 <button class="tab" data-tab="tg1">T-G1 Demo</button>
 <button class="tab" data-tab="safety">Safety Divergence</button>
 <button class="tab" data-tab="conservation">Conservation</button>
 <button class="tab" data-tab="metrics">Metrics</button>
</nav>
<main class="main">
 <section id="compounding" class="panel active"></section>
 <section id="tg1" class="panel"></section>
 <section id="safety" class="panel"></section>
 <section id="conservation" class="panel"></section>
 <section id="metrics" class="panel"></section>
</main>
<script>
const INLINE_REPORT = __REPORT_JSON__;
let REPORT = INLINE_REPORT;
const COLORS = {ci:'#1565c0', reward:'#c62828', hand:'#6a1b9a', baseline:'#7b8798'};
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = value => `${(Number(value || 0) * 100).toFixed(1)}%`;
const num = (value, digits=3) => value == null ? '—' : Number(value).toFixed(digits);
function arm(key){return REPORT[key] || {name:key,decisions:[],quality_curve:[],high_severity_quality_curve:[],conservation_states:[],promotions:[],rejections:[],iks_values:[],centroid_distances:[],gt_distances:[]}}
function label(key){return key==='arm_1_ci'?'CI — governed':key==='arm_2_reward_max'?'Reward-max — ungoverned':'Hand-specified reward'}
function svgChart(series, opts={}) {
 const W=940,H=360,L=62,R=22,T=22,B=48, iw=W-L-R, ih=H-T-B;
 const all=series.flatMap(s=>s.values.map(Number)).filter(Number.isFinite); const lo=opts.min ?? (opts.percent ? 0 : (Math.min(...all,0)*1.05)); const hi=opts.max ?? (opts.percent ? 1 : (Math.max(...all,1)*1.05));
 const x=n=>L+(n/Math.max(opts.length||1,1))*iw, y=v=>T+(1-(v-lo)/Math.max(hi-lo,1e-9))*ih;
 let out=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.aria||'line chart')}">`;
 for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4;const yy=y(v);out+=`<line class="gridline" x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}"/><text class="axis" x="${L-9}" y="${yy+4}" text-anchor="end">${opts.percent?(v*100).toFixed(0)+'%':v.toFixed(2)}</text>`}
 out+=`<line stroke="#8290a3" x1="${L}" x2="${L}" y1="${T}" y2="${H-B}"/><line stroke="#8290a3" x1="${L}" x2="${W-R}" y1="${H-B}" y2="${H-B}"/>`;
 for(let i=0;i<=4;i++){const n=Math.round((opts.length||1)*i/4);out+=`<text class="axis" x="${x(n)}" y="${H-B+22}" text-anchor="middle">${n}</text>`}
 if(opts.verticalAt!=null){const xx=x(opts.verticalAt);out+=`<line class="dashed" stroke="#e65100" x1="${xx}" x2="${xx}" y1="${T}" y2="${H-B}"/><text class="axis" fill="#e65100" x="${Math.min(xx+5,W-160)}" y="${T+14}">${esc(opts.verticalLabel||'disruption')}</text>`}
 if(opts.horizontalAt!=null){const yy=y(opts.horizontalAt);out+=`<line class="dashed" stroke="#7b8798" x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}"/><text class="axis" x="${W-R-4}" y="${yy-5}" text-anchor="end">frozen baseline</text>`}
 series.forEach(s=>{const vals=s.values;const points=vals.map((v,i)=>`${x(i+1)},${y(Number(v))}`).join(' ');out+=`<polyline class="plotline" stroke="${s.color}" points="${points}"/>`});
 out+=`<text class="axis" x="${(L+W-R)/2}" y="${H-5}" text-anchor="middle">verified decisions (V)</text><text class="axis" transform="translate(16 ${(T+H-B)/2}) rotate(-90)" text-anchor="middle">${esc(opts.yLabel||'value')}</text></svg>`;return out;
}
function legend(){return `<div class="legend"><span class="ci"><i class="swatch" style="background:${COLORS.ci}"></i>CI governed</span><span class="reward"><i class="swatch" style="background:${COLORS.reward}"></i>Reward-max</span><span class="hand"><i class="swatch" style="background:${COLORS.hand}"></i>Hand-specified</span></div>`}
function metricCard(title,value,detail,klass=''){return `<div class="metric ${klass}"><small>${esc(title)}</small><strong>${esc(value)}</strong><span class="muted">${esc(detail||'')}</span></div>`}
function renderCompounding(){const ci=arm('arm_1_ci'),rm=arm('arm_2_reward_max'),hand=arm('arm_3_hand_specified'),m=REPORT.metadata||{};const baseline=ci.quality_curve?.[0]||0;const disruption=m.poisoned_rule?.injected_at||null;document.getElementById('compounding').innerHTML=`<div class="card"><h2>The compounding curve</h2><p class="muted">Decision quality over verified decisions. The vertical marker is the poisoned-rule injection; the horizontal line is the initial governed accuracy.</p><div class="chart">${svgChart([{values:ci.quality_curve,color:COLORS.ci},{values:rm.quality_curve,color:COLORS.reward},{values:hand.quality_curve,color:COLORS.hand}],{percent:true,length:ci.quality_curve.length,verticalAt:disruption,verticalLabel:'safety injection',horizontalAt:baseline,yLabel:'decision quality (%)',aria:'three-arm compounding quality curve'})}</div>${legend()}</div><div class="grid">${metricCard('CI final quality',pct(ci.quality_curve.at(-1)),`vs ${pct(rm.quality_curve.at(-1))} reward-max`,'ci')}${metricCard('Reward-max final quality',pct(rm.quality_curve.at(-1)),`high severity ${pct(rm.high_severity_quality_curve.at(-1))}`,'reward')}${metricCard('Hand-specified final quality',pct(hand.quality_curve.at(-1)),'frozen objective','hand')}</div>`}
function renderTg1(){const t=REPORT.tg1||{},ci=arm('arm_1_ci');const rows=ci.decisions.slice(0,5).map((d,i)=>`<tr><td>${i+1}</td><td>${esc(d.category)}</td><td>${esc(d.action)}</td><td class="good">unchanged</td><td>${esc(d.actual_action)}</td></tr>`).join('');document.getElementById('tg1').innerHTML=`<div class="card"><h2>T-G1 — decision ≠ reward-maximizer</h2><p>The reward configuration changes on a fixed input. CI's centroid decision path remains invariant; the reward-max baseline follows its reward objective and flips.</p><div class="grid"><div class="metric"><small>CI action</small><strong class="${t.ci_action_unchanged?'good':'bad'}">${t.ci_action_unchanged?'UNCHANGED':'CHANGED'}</strong><span>${esc(t.ci_before?.action)} → ${esc(t.ci_after?.action)}</span></div><div class="metric"><small>CI probabilities</small><strong class="${t.ci_probabilities_unchanged?'good':'bad'}">${t.ci_probabilities_unchanged?'UNCHANGED':'CHANGED'}</strong><span>centroid output is reward-independent</span></div><div class="metric"><small>Reward-max action</small><strong class="${t.reward_max_action_flipped?'bad':'good'}">${t.reward_max_action_flipped?'FLIPS':'UNCHANGED'}</strong><span>${esc(t.reward_max_before)} → ${esc(t.reward_max_after)}</span></div></div></div><div class="card"><h3>Fixed-input action probabilities</h3><table><thead><tr><th>Arm</th><th>Before</th><th>After</th></tr></thead><tbody><tr><td>CI</td><td><code>${esc(JSON.stringify(t.ci_before?.probabilities||[]))}</code></td><td><code>${esc(JSON.stringify(t.ci_after?.probabilities||[]))}</code></td></tr><tr><td>Reward-max</td><td>${esc(t.reward_max_before)}</td><td>${esc(t.reward_max_after)}</td></tr></tbody></table></div><div class="card"><h3>Decision feed samples</h3><p class="muted">These are the first five shared S2P decisions; the T-G1 proof above is the fixed-input swap.</p><div class="scroll"><table><thead><tr><th>V</th><th>Category</th><th>CI action</th><th>Reward swap</th><th>Oracle action</th></tr></thead><tbody>${rows}</tbody></table></div></div>`}
function eventRows(){const ci=arm('arm_1_ci'),rm=arm('arm_2_reward_max');const reject=ci.rejections.map(e=>`<tr><td>CI</td><td>REJECTED</td><td>${esc(e.candidate_id||'poisoned rule')}</td><td class="bad">${esc(e.reason||e.engine_reason||'conservation_not_green')}</td><td>${esc(e.message||'Conservation gate blocked promotion')}</td></tr>`).join('');const promote=rm.promotions.map(e=>`<tr><td>Reward-max</td><td class="bad">PROMOTED</td><td>${esc(e.variant_id)}</td><td>${esc(e.reason)}</td><td>aggregate +${Number(e.aggregate_improvement||0)*100}%</td></tr>`).join('');return reject+promote}
function renderSafety(){const rm=arm('arm_2_reward_max'),ci=arm('arm_1_ci');const poison=REPORT.metadata?.poisoned_rule||{};document.getElementById('safety').innerHTML=`<div class="card"><h2>Safety divergence — the inverted demo</h2><p>The same candidate looks attractive in aggregate but regresses the high-severity slice. Governance rejects the rule before activation; the ungoverned reward-max arm promotes it.</p><div class="callout"><b>Poisoned rule:</b> aggregate uplift +${Number(poison.aggregate_improvement||0)*100}% · high-severity delta ${Number(poison.high_severity_delta||0)*100}% · injected at V=${esc(poison.injected_at)}</div><div class="scroll"><table><thead><tr><th>Arm</th><th>Decision</th><th>Variant</th><th>Reason</th><th>Evidence</th></tr></thead><tbody><tr><td>CI</td><td>ACTIVE BASELINE</td><td>s2p-baseline</td><td>governed</td><td>initial policy remains active</td></tr>${eventRows()}</tbody></table></div></div><div class="card"><h3>High-severity quality after promotion</h3><div class="chart">${svgChart([{values:ci.high_severity_quality_curve,color:COLORS.ci},{values:rm.high_severity_quality_curve,color:COLORS.reward}],{percent:true,length:rm.high_severity_quality_curve.length,verticalAt:poison.injected_at,verticalLabel:'promotion',yLabel:'high-severity quality (%)',aria:'high-severity safety divergence chart'})}</div><div class="legend"><span class="ci"><i class="swatch" style="background:${COLORS.ci}"></i>CI remains governed</span><span class="reward"><i class="swatch" style="background:${COLORS.reward}"></i>Reward-max collapses</span></div></div>`}
function stateTable(state){const s=state||{};return `<table><tbody><tr><th>Status</th><td><span class="pill ${String(s.status||'').toLowerCase()}">${esc(s.status||'—')}</span></td></tr><tr><th>α</th><td>${num(s.alpha)}</td></tr><tr><th>q</th><td>${pct(s.q)}</td></tr><tr><th>V</th><td>${esc(s.V??s.verified_count??'—')}</td></tr><tr><th>θ_min</th><td>${num(s.theta_min)}</td></tr><tr><th>Signal / headroom</th><td>${num(s.signal)} / ${num(s.headroom)}</td></tr><tr><th>Reason</th><td>${esc(s.reason||'Ungoverned arm — no conservation gate')}</td></tr></tbody></table>`}
function renderConservation(){const ci=arm('arm_1_ci'),rm=arm('arm_2_reward_max'),hand=arm('arm_3_hand_specified');document.getElementById('conservation').innerHTML=`<div class="card"><h2>Conservation panel</h2><p class="muted">The governed arm exposes live conservation evidence. Reward-max intentionally has no conservation gate.</p><div class="status-grid"><div class="status-card"><h3 class="ci">CI governed</h3>${stateTable(ci.conservation_states.at(-1))}</div><div class="status-card"><h3 class="reward">Reward-max</h3>${stateTable({status:'UNGOVERNED'})}</div><div class="status-card"><h3 class="hand">Hand-specified</h3>${stateTable(hand.conservation_states.at(-1))}</div></div></div><div class="card"><h3>Conservation signal timeline</h3><div class="chart">${svgChart([{values:ci.conservation_states.map(s=>Number(s.signal||0)),color:COLORS.ci},{values:hand.conservation_states.map(s=>Number(s.signal||0)),color:COLORS.hand}],{length:ci.conservation_states.length,yLabel:'signal',aria:'conservation signal timeline'})}</div></div>`}
function renderMetrics(){const ci=arm('arm_1_ci'),hand=arm('arm_3_hand_specified'),d=REPORT.display||{};document.getElementById('metrics').innerHTML=`<div class="card"><h2>Metrics dashboard</h2><div class="grid">${metricCard('ε_firm',num(d.epsilon_firm),'oracle configuration','ci')}${metricCard('IKS final',num(ci.iks_values.at(-1)),'CI canonical-prior health','ci')}${metricCard('Centroid → canonical',num(ci.centroid_distances.at(-1)),'learning signal','ci')}${metricCard('Centroid → ground truth',num(ci.gt_distances.at(-1)),'oracle-only convergence proof','good')}</div></div><div class="card"><h3>Centroid distances</h3><p class="muted">Canonical distance is the production learning signal; ground-truth distance is oracle-only.</p><div class="chart">${svgChart([{values:ci.centroid_distances,color:COLORS.blue||COLORS.ci},{values:ci.gt_distances,color:'#2e7d32'},{values:hand.centroid_distances,color:COLORS.hand}],{length:ci.centroid_distances.length,yLabel:'Frobenius distance',aria:'centroid distance chart'})}</div><div class="legend"><span class="ci"><i class="swatch" style="background:${COLORS.ci}"></i>CI → canonical</span><span class="good"><i class="swatch" style="background:#2e7d32"></i>CI → ground truth</span><span class="hand"><i class="swatch" style="background:${COLORS.hand}"></i>Hand → canonical</span></div></div><div class="card"><h3>Measurement-state ladder</h3><div class="grid">${(d.measurement_state_ladder||[]).map((state,i)=>`<div class="metric"><small>Stage ${i+1}</small><strong>${esc(state)}</strong><span class="muted">${i===0?'initial evidence':i===d.measurement_state_ladder.length-1?'validated measurement':'progression state'}</span></div>`).join('')}</div></div>`}
function showTab(id, button){document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));const selected=button||document.querySelector(`[data-tab="${id}"]`);if(selected)selected.classList.add('active');document.getElementById(id).classList.add('active')}
function render(){renderCompounding();renderTg1();renderSafety();renderConservation();renderMetrics();showTab('compounding')}
document.querySelectorAll('.tab').forEach(button=>button.addEventListener('click',()=>showTab(button.dataset.tab,button)));
fetch('report.json').then(r=>r.ok?r.json():Promise.reject()).then(data=>{REPORT=data;render()}).catch(()=>render());
</script>
</body></html>'''.replace("__REPORT_JSON__", embedded_json)
