"""D1: one simulated verification and a changed next S2P-SC2 decision."""
from __future__ import annotations
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace
from typing import Any
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "s2p-copilot/backend"))
OUT = ROOT / "experiments/vld/results/recursion_trace_example.md"


def load_file(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run() -> None:
    np.random.seed(42)
    module = load_file("d1_investigation", ROOT / "copilot_sdk/scoring/investigation.py")
    preseed = importlib.import_module("app.vld_preseed")
    providers = importlib.import_module("app.evidence_provider")
    data = preseed.seed_vld_s2p_showcase({})
    invoice = next(r for r in data["invoices"] if r["invoice_id"] == "VLD-S2P-2")
    info = json.loads((ROOT / "real_centroids_v1.json").read_text())["copilots"]["s2p"]
    names, actions, category = info["factor_names"], info["action_names"], invoice["category"]
    v0 = np.array([invoice["factors"][n] for n in names])
    mu = np.array(info["all_category_mu"][category])
    inv = module.VLDInvestigator(mu, info["sigma"], names, tau=info["tau"], action_names=actions)
    provider = providers.S2PEvidenceProvider(data, invoice["invoice_id"])
    conn = sqlite3.connect(":memory:")
    store = module.KUtilityStore(SimpleNamespace(conn=conn), len(names))
    # Explicit planted near-boundary starting state; no invented prior verifications.
    conn.execute("INSERT INTO k_utility VALUES (?, ?, ?, ?)", (category, 5, .62, 0))
    conn.commit()
    before = store.get_weights(category).copy()

    def episode(label: str, budget: int, weights: Any) -> Any:
        return inv.investigate(label, category, v0, provider, budget=budget,
                               K_weights=weights, gated_sources=set(), delta=0, max_flips=100)

    control = episode("NEXT-INVOICE-frozen-counterfactual", 2, before)
    acquired = episode("VERIFICATION-INVOICE-A", 3, before)
    contract = provider.read_evidence(invoice["invoice_id"], 0, names[0])
    volume = provider.read_evidence(invoice["invoice_id"], 5, names[5])
    assert contract and volume
    assert contract["clause"] == "Bulk pricing pass-through activates above 2x forecast volume."
    assert acquired.final_action == actions.index("auto_approve")
    store.update_weights(category, acquired, correct=True)
    after = store.get_weights(category).copy()
    next_trace = episode("NEXT-INVOICE-B-updated", 2, after)
    assert actions[control.final_action] == "flag_leakage"
    assert actions[next_trace.final_action] == "auto_approve"
    assert [s.dimension for s in control.steps] == [0, 1]
    assert [s.dimension for s in acquired.steps] == [0, 1, 5]
    assert [s.dimension for s in next_trace.steps] == [0, 5]
    np.testing.assert_allclose(after-before, [.02, .02, 0, 0, 0, .04, 0, 0], atol=1e-14)
    np.testing.assert_array_equal(inv.mu, mu)
    fmt = lambda value: json.dumps(value, ensure_ascii=False)
    lines = [
        "# D1 — Verified-outcome recursion trace", "",
        "Date: September 14, 2026 · random_state=42", "",
        "**Tier: REAL_COMPONENT geometry + SIMULATED verification; PLANTED FIXTURE starting state and evidence.**",
        "Executed locally with production VLDInvestigator.compute_Q/investigate, KUtilityStore.update_weights, "
        "and S2PEvidenceProvider against exported production geometry and the existing in-memory S2P-SC2 preseed. "
        "No operational invoice, signed contract, human verification, application database write, or live AGE claim.",
        "", "## Outcome and experimental isolation", "",
        "One actual in-memory verification callback updates K. The next identical-feature invoice at B=2 changes "
        "from flag_leakage (frozen counterfactual, reads 0→1) to auto_approve (updated K, reads 0→5). "
        "The preceding acquisition episode explicitly uses B=3 to acquire dim 5. Repeating the B=2 cold-start case "
        "cannot discover an unread factor by itself.", "",
        "Initial K5=.62 is a **planted near-boundary warm state**, not a measured learning history. "
        "It is reachable from .5 by six +.02 non-flip credits, but those six events were not executed or claimed here. "
        "The prepaper's recommended K5=1.0 is a different planted state. This example uses .62→.66; "
        "one verification does not produce .5→1.0.", "",
        "Investigation and the K update leave μ unchanged: **Δμ=0 for every cell (5×8)**; Δσ=0. "
        "This records K-only RGI, not centroid learning. No conservation gate is invoked by this local KUtilityStore "
        "callback. A1's gate/lifecycle findings remain open; this trace does not establish production safety.",
        "", "## Source geometry and initial state", "",
        f"Category supplied: {category}. Category classification is not evaluated.",
        f"Factor order: {fmt(names)}.", f"Action order: {fmt(actions)}.",
        f"v0 (factor vector, not action probabilities): {fmt(v0.tolist())}.",
        f"Initial action probabilities: {fmt(inv.score(v0)[1].tolist())}.",
        f"σ={fmt(info['sigma'])}; τ={info['tau']}. Export uses unit-sigma fallback.",
        f"K before verification: {fmt(before.tolist())}.", "",
        "μ rows, in the action/factor order above:", "~~~json", json.dumps(mu.tolist(), indent=2), "~~~",
        "", "## Contract entitlement and provenance", "",
        f"Contract: {contract['contract_ref']}; source=contract_db; value={contract['value']}; "
        f"confidence={contract['confidence']}.", "",
        f"> {contract['clause']}", "",
        f"Volume: source={volume['source']}; value={volume['value']}; confidence={volume['confidence']}; "
        f"volume_multiplier={volume['volume_multiplier']}. Explanation: {volume['explanation']}", "",
        "The fixture's 3× volume exceeds its 2× clause trigger: the simulated approval rationale. "
        "**There is no commodity-index entitlement clause in this source fixture.** "
        "The commodity_index_correlation factor is populated with contract/volume context, not a computed index "
        "correlation. The bulk-volume clause above is verbatim; no index clause has been invented. "
        "Neither correlation nor a high normalized factor proves entitlement. The investigator does not parse or "
        "enforce the clause: the simulated verifier supplies the contractual interpretation.", "",
        "Sources: ../s2p-copilot/backend/app/vld_preseed.py and evidence_provider.py. "
        "Provider results include fixture clause and source metadata. Reads use ungated coordinate replacement; "
        "confidence is recorded, not used as damping.",
    ]

    def append_trace(title: str, trace: Any, weights: Any) -> None:
        lines.extend(["", f"## {title}", "",
                      f"Decision {trace.decision_id}; budget={trace.budget}; "
                      f"surface={actions[trace.surface_action]}; final={actions[trace.final_action]}; "
                      f"halt={trace.halt_reason}."])
        attempted: set[int] = set()
        for step in trace.steps:
            v = np.array(step.v_before)
            _, probs = inv.score(v)
            a1, a2 = np.argsort(probs)[::-1][:2]
            precision = 1.0 / (100.0 * np.maximum(inv.sigma**2, .001))
            discriminative = np.abs(mu[a1]-mu[a2])
            leverage = np.abs((v-mu[a1])**2-(v-mu[a2])**2)
            base = precision+discriminative+leverage
            q = inv.compute_Q(v, probs, attempted, weights)
            valid = [d for d in range(len(names)) if d not in attempted]
            np.testing.assert_allclose(q[valid], (base*weights)[valid], atol=1e-14)
            evidence = provider.read_evidence(invoice["invoice_id"], step.dimension, step.factor_name)
            lines.extend(["", f"### Read {step.step}: {step.factor_name}", "",
                          f"v_before: {fmt(step.v_before)}.",
                          f"Top actions: {actions[int(a1)]}, {actions[int(a2)]}.", "",
                          "| Dim / factor | Precision | Discriminative | Leverage | Base Q | K | Weighted Q |",
                          "|---|---:|---:|---:|---:|---:|---:|"])
            for d, name in enumerate(names):
                weighted = "excluded" if d in attempted else f"{q[d]:.8f}"
                lines.append(f"| {d} / {name} | {precision[d]:.8f} | {discriminative[d]:.8f} | "
                             f"{leverage[d]:.8f} | {base[d]:.8f} | {weights[d]:.8f} | {weighted} |")
            lines.extend(["", f"Evidence payload: {fmt(evidence)}.",
                          f"v_after: {fmt(step.v_after)}.",
                          f"Action: **{actions[step.action_before]} → {actions[step.action_after]}**; "
                          f"flipped={step.flipped}; status={step.status}."])
            attempted.add(step.dimension)

    append_trace("1. Frozen B=2 counterfactual for the subsequent invoice", control, before)
    append_trace("2. Acquisition episode A before verification (B=3)", acquired, before)
    lines.extend(["", "## 3. Verification event and actual update", "",
                  "Event ID: SIM-VERIFY-A-42. Source: deterministic simulated invoice reviewer using "
                  "CTR-MERIDIAN-BULK and its preseed's 3× volume evidence. Verified action=auto_approve; "
                  "the acquisition's final action matches, so correct=True.", "",
                  "Actual call: KUtilityStore.update_weights(category, acquired_trace, correct=True) "
                  "(copilot_sdk/scoring/investigation.py:441–477). It credits each acquired dimension +.02, "
                  "doubled to +.04 when that step flipped the action, capped at 3.0. This differs from "
                  "GAP-2's flat +.02 informative-read credit.", "",
                  f"K before: {fmt(before.tolist())}.", f"K after: {fmt(after.tolist())}.",
                  f"ΔK: {fmt((after-before).round(10).tolist())}.",
                  "Δμ and Δσ: all zeros. Only the in-memory K table was written.",
                  f"Stored (dimension, weight, n_updates): "
                  f"{fmt(conn.execute('SELECT dimension, weight, n_updates FROM k_utility ORDER BY dimension').fetchall())}."])
    append_trace("4. Subsequent similar invoice B with updated K (B=2)", next_trace, after)
    lines.extend(["", "## Arithmetic reconciliation and causal comparison", "",
                  "For amount_variance_ratio (dim 1), initial unweighted Q=.1998, rounded to .200. "
                  "At K1=.5 its weighted score is .1998×.5=.0999, rounded to .100. After the contract read, "
                  "the top-two actions and dim-1 input are unchanged, so its base Q remains .1998. "
                  "This is **base versus K-weighted Q**, not a first-read recomputation that halves the score.", "",
                  "Before verification, dim 5 has .16×.62=.0992 < dim 1's .1998×.5=.0999. "
                  "After verification, dim 5 has .16×.66=.1056 > dim 1's .1998×.52=.103896. "
                  "The next B=2 episode reads 0→5 and changes the action. The counterfactual and next episode "
                  "share exactly v0, μ, σ, τ, providers and B=2; only K differs.", "",
                  "No population routing_quality, category_accuracy or action_accuracy is inferred from this single trace.",
                  "", "## Reproduction and source hashes", "",
                  "Run python -B scripts/d1_recursion_trace_v1.py. random_state=42; deterministic trace."])
    for p in [ROOT/"real_centroids_v1.json", ROOT/"copilot_sdk/scoring/investigation.py",
              ROOT.parent/"s2p-copilot/backend/app/vld_preseed.py",
              ROOT.parent/"s2p-copilot/backend/app/evidence_provider.py"]:
        lines.append(f"- {p.relative_to(ROOT.parent).as_posix()}: {hashlib.sha256(p.read_bytes()).hexdigest()}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps({"tier": "REAL_COMPONENT + SIMULATED; PLANTED FIXTURE",
                      "before_action": actions[control.final_action], "after_action": actions[next_trace.final_action],
                      "delta_k": (after-before).tolist(), "mu_changed": False,
                      "clause": contract["clause"], "output": str(OUT)}))
    conn.close()


if __name__ == "__main__":
    run()

