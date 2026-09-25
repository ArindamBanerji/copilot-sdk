"""VLD-ASTRA-SWEEP: real Python components, offline data, no application startup.

Run: python tests/vld_validation_report.py

Each domain runs in a fresh interpreter to isolate the five `app` packages.
Existing SQLite databases are opened mode=ro and backed up into a real in-memory
SQLiteGraphStore. SOC has no local checkpoint: its real CompoundingScorer uses
the bootstrap prior, explicitly labelled below. These are NOT live AGE exports.
Temporary outboxes isolate the constructor's otherwise persistent side effects.
No scorer, provider, preseed, or application function is patched or mocked.
"""

from __future__ import annotations

import ast
from contextlib import redirect_stdout
from dataclasses import asdict
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from typing import Any

SDK = Path(__file__).resolve().parents[1]
WORKSPACE = SDK.parent
DOMAINS = ("soc", "trading", "purchasing", "dataops", "s2p")
BACKENDS = {
    "soc": WORKSPACE / "gen-ai-roi-demo-v4-v50/backend",
    "s2p": WORKSPACE / "s2p-copilot/backend",
    **{name: SDK / f"apps/{name}/backend" for name in DOMAINS[1:4]},
}
PROVIDERS = {
    "soc": "SOCEvidenceProvider", "trading": "TradingEvidenceProvider",
    "purchasing": "PurchasingEvidenceProvider", "dataops": "DataOpsEvidenceProvider",
    "s2p": "S2PEvidenceProvider",
}
# Narrative dimensions, in canonical factor order; source references are emitted.
NARRATIVE_DIMS: dict[str, tuple[list[int], list[int], list[int]]] = {
    "soc": ([0], [2, 0], []),
    "trading": ([2, 1], [2, 1], []),
    "purchasing": ([5, 4], [4, 3], []),
    "dataops": ([0, 3], [2, 3], []),
    # S2P-2 is K-dependent. The default no-K/unit-sigma route is 0 -> 1;
    # the learned-K claim is 0 -> 5 and is covered by the domain evidence test.
    "s2p": ([0, 3], [0, 1], []),
}


def reference(path: Path, needle: str) -> str:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    hits = [i for i, line in enumerate(lines, 1) if needle in line]
    if not hits:
        raise ValueError(f"Source contract changed: {path}: missing {needle!r}")
    return f"{path.relative_to(WORKSPACE).as_posix()}:{hits[0]}"


def resolve_gated_sources(node: ast.expr, tree: ast.Module) -> list[str]:
    """Read literal gates and imported starred sets without starting app.main."""
    values = []
    elements = node.elts if isinstance(node, ast.Set) else [ast.Starred(value=node)]
    for element in elements:
        if not isinstance(element, ast.Starred):
            values.append(ast.literal_eval(element))
            continue
        if isinstance(element.value, ast.Name):
            name = element.value.id
            imports = [(statement, alias) for statement in tree.body
                       if isinstance(statement, ast.ImportFrom)
                       for alias in statement.names if (alias.asname or alias.name) == name]
            if len(imports) != 1:
                raise ValueError(f"Cannot resolve imported gate set {name!r}")
            statement, alias = imports[0]
            module = "." * statement.level + (statement.module or "")
            expanded = getattr(importlib.import_module(module, package="app"), alias.name)
        else:
            expanded = ast.literal_eval(element.value)
        if not isinstance(expanded, (set, frozenset, list, tuple)):
            raise ValueError("Expanded gate sources must be a collection of strings")
        values.extend(expanded)
    if not all(isinstance(value, str) for value in values):
        raise ValueError("Gate sources must be strings")
    return sorted(set(values))


def wiring(domain: str) -> dict[str, Any]:
    path = BACKENDS[domain] / "app/main.py"
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "create_investigation_router"]
    if len(calls) != 1:
        raise ValueError(f"Expected one investigation router in {path}, found {len(calls)}")
    call = calls[0]
    kw = {item.arg: item.value for item in call.keywords}
    call_source = ast.get_source_segment(source, call) or ""
    k_node = kw.get("k_store")
    k_wired = (
        (k_node is not None and not (isinstance(k_node, ast.Constant) and k_node.value is None))
        or "_vld_k_router_kwargs" in call_source
        or ("KUtilityStore" in source and '"k_store"' in source)
    )
    classifier = kw.get("classifier")
    classifier_wired = (
        (classifier is not None and not (isinstance(classifier, ast.Constant) and classifier.value is None))
        or "_vld_classifier_router_kwargs" in call_source
        or "classifier=SituationClassifier" in call_source
        or ("SituationClassifier" in source and '"classifier"' in source)
    )
    model_path = None
    if classifier is not None and not (isinstance(classifier, ast.Constant) and classifier.value is None):
        if not isinstance(classifier, ast.Call) or not isinstance(classifier.func, ast.Name) or classifier.func.id != "SituationClassifier":
            raise ValueError("Classifier wiring changed; inspect its factory before claiming model status")
        if classifier.args:
            model_path = ast.literal_eval(classifier.args[0])
        for arg in classifier.keywords:
            if arg.arg == "model_path":
                model_path = ast.literal_eval(arg.value)
    return {
        "source": f"{path.relative_to(WORKSPACE).as_posix()}:{call.lineno}",
        "k_store_wired": k_wired, "classifier_wired": classifier_wired,
        "model_path": model_path,
        "default_budget": ast.literal_eval(kw["default_budget"]) if "default_budget" in kw else 2,
        "gated_sources": resolve_gated_sources(kw["gated_sources"], tree) if "gated_sources" in kw else [],
    }


def load_showcases(domain: str):
    seed = importlib.import_module("app.vld_preseed")
    ep = importlib.import_module("app.evidence_provider")
    if domain == "soc":
        seed.seed_vld_showcase(None)
        rows, source, key = seed.SHOWCASE_ALERTS, None, "alert_id"
    elif domain == "trading":
        seed.seed_vld_trading_showcase(None)
        rows, source, key = seed.SHOWCASE_TRADES, None, "trade_id"
    elif domain == "purchasing":
        source = seed.seed_vld_purchasing_showcase()
        rows, key = list(source["orders"].values()), "order_id"
    elif domain == "dataops":
        source = seed.seed_vld_dataops_showcase(ep.build_dataops_evidence_source(BACKENDS[domain] / "data"))
        rows, key = [source["alerts"][identifier] for identifier in source["vld_showcase_alert_ids"]], "alert_id"
    else:
        source = seed.seed_vld_s2p_showcase()
        rows, key = source["invoices"], "invoice_id"
    return rows, source, key, getattr(ep, PROVIDERS[domain])


def record_reads(provider, operation):
    """Observe real method returns, including None, without replacing the provider."""
    observed = []
    code = provider.read_evidence.__func__.__code__
    previous = sys.getprofile()

    def profiler(frame, event, arg):
        if event == "return" and frame.f_code is code and frame.f_locals.get("self") is provider:
            observed.append({"dimension": int(frame.f_locals["dimension"]),
                             "factor_name": str(frame.f_locals["factor_name"]),
                             "evidence": arg})

    try:
        sys.setprofile(profiler)
        result = operation()
    finally:
        sys.setprofile(previous)
    return result, observed


def centroid_tensor_hash(tensor) -> str:
    import numpy as np

    return hashlib.sha256(np.asarray(tensor, dtype=np.float64).tobytes()).hexdigest()


def restore_l5_centroids_for_export(domain: str, scorer: Any, store: Any) -> dict[str, Any]:
    """Apply the same validated L5 centroid overlay used at startup."""

    before = getattr(scorer, "_scorer", scorer).centroids
    rows = store.get_centroids(domain) if callable(getattr(store, "get_centroids", None)) else []
    applied = 0
    if rows:
        load_centroids = getattr(scorer, "load_centroids_from_l5", None)
        if not callable(load_centroids):
            raise ValueError(f"{domain}: scorer cannot apply L5 centroid rows")
        applied = len(rows) if load_centroids(rows) else 0
    after = getattr(scorer, "_scorer", scorer).centroids
    return {
        "pre_restore_hash": centroid_tensor_hash(before),
        "post_restore_hash": centroid_tensor_hash(after),
        "l5_rows_total": len(rows),
        "l5_rows_applied": applied,
    }


def one_dimension_sensitivity(investigator, vector, target: int) -> list[dict[str, Any]]:
    """Diagnostic grid on FINAL factors, NOT fabricated evidence or a routed replay."""
    import numpy as np
    candidates = []
    for dimension, name in enumerate(investigator.factor_names):
        possible = []
        for value in np.linspace(0.0, 1.0, 101):
            alternative = np.asarray(vector, dtype=float).copy()
            alternative[dimension] = value
            action, probabilities = investigator.score(alternative)
            if action == target and investigator.margin(probabilities) > 0.05:
                possible.append(float(value))
        if possible:
            closest = min(possible, key=lambda value: abs(value - vector[dimension]))
            candidates.append({"dimension": dimension, "factor_name": name,
                               "current_final_factor": float(vector[dimension]),
                               "nearest_grid_factor": closest,
                               "absolute_change": abs(closest - float(vector[dimension]))})
    return sorted(candidates, key=lambda row: row["absolute_change"])


def collect_domain(domain: str) -> dict[str, Any]:
    import numpy as np
    from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
    from copilot_sdk.scoring.scorer import CompoundingScorer
    from copilot_sdk.scoring.investigation import EvidenceProvider, VLDInvestigator
    from copilot_sdk.scoring.situation_classifier import SituationClassifier
    from copilot_sdk.backend.investigation_router import (
        _read_action_centroids, _read_centroid_tensor, _read_sigma, _read_tau,
        create_investigation_router, InvestigationRequest,
    )

    runtime = wiring(domain)
    if runtime["model_path"] is not None:
        raise RuntimeError("A classifier model is now configured: resolve its application-relative path explicitly")
    rows, evidence_source, id_key, provider_class = load_showcases(domain)
    database = (BACKENDS[domain] / ("app/data/s2p.db" if domain == "s2p" else f"data/{domain}.db"))
    store = SQLiteGraphStore(":memory:", domain=domain)
    provenance: dict[str, Any] = {"live_age_verified": False, "database": None, "checkpoint_count": 0}
    try:
        if database.exists():
            with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as connection:
                connection.backup(store.connection)
            provenance["database"] = str(database)
        checkpoints = store.get_centroid_checkpoints(domain, include_v2=True, limit=None)
        provenance["checkpoint_count"] = len(checkpoints)
        provenance["latest_checkpoint"] = ({key: checkpoints[0].get(key) for key in
                                             ("id", "created_at", "factor_names_hash")} if checkpoints else None)
        before_tensor = store.load_latest_centroids(domain)
        # Same real factory used by application proxies/adapters. Test profile
        # authorizes the isolated store; learning and application startup are not run.
        scorer = CompoundingScorer.from_preset(domain, db_path=":memory:", graph_store=store,
                                               profile="test", enable_rl=False)
        l5_restore = restore_l5_centroids_for_export(domain, scorer, store)
        tensor = _read_centroid_tensor(scorer)
        shape = scorer._preset.shape
        names, actions, categories = map(list, (shape.factor_names, shape.action_names, shape.category_names))
        if tensor.shape != (len(categories), len(actions), len(names)):
            raise ValueError(f"Stored centroid shape {tensor.shape} does not match preset {shape}")
        restored = before_tensor is not None and np.array_equal(tensor, before_tensor)
        provenance["centroid_source"] = "local SQLite checkpoint" if restored else "real preset bootstrap prior"
        provenance["identical_action_centroids_by_category"] = {
            category: len({tuple(action) for action in tensor[index]}) == 1
            for index, category in enumerate(categories)
        }
        provenance["evidence_scope"] = (
            "real registered showcase evidence; no backing graph/data client; unregistered reads are offline-unavailable"
            if domain in {"soc", "trading"} else
            "real fixture loader plus in-memory showcase seed" if domain == "dataops" else
            "real in-memory showcase seed; same source type supplied by application startup"
        )
        provenance["construction"] = "CompoundingScorer.from_preset(profile='test', enable_rl=False) plus startup-equivalent L5 centroid overlay"
        provenance.update(l5_restore)
        provenance["source"] = reference(SDK / "copilot_sdk/scoring/scorer.py", "centroids = graph_store.load_latest_centroids")
        provenance["l5_restore_source"] = reference(SDK / "copilot_sdk/scoring/startup_restore.py", "def _restore_centroids")
        sigma, tau = _read_sigma(scorer, len(names)), _read_tau(scorer)
        sigma_exposed = any(getattr(owner, attr, None) is not None
                            for owner in (scorer, scorer.gae_scorer) for attr in ("sigma", "_sigma"))
        provenance["sigma_source"] = "scorer" if sigma_exposed else "router unit-vector fallback (not learned sigma)"
        provenance["sigma_reference"] = reference(SDK / "copilot_sdk/backend/investigation_router.py", "return np.ones(d")
        provenance["decisions"] = store.count_decisions(domain)
        provenance["verified_decisions"] = len(store.get_verified_decisions(domain))
        tables = {row[0] for row in store.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        runtime["k_has_data"] = (store.connection.execute("SELECT COUNT(*) FROM k_utility WHERE n_updates > 0").fetchone()[0] > 0
                                  if "k_utility" in tables else False)
        runtime["k_store_exercised"] = False
        classifier = SituationClassifier() if runtime["classifier_wired"] else None
        runtime["model_loaded"] = bool(classifier is not None and classifier.is_available)
        runtime["fallback"] = "heuristic d_min classifier" if classifier else "fixed default budget; no classifier"
        results = []
        for index, row in enumerate(rows):
            identifier, category = str(row[id_key]), str(row["category"])
            vector = np.asarray(row["surface_factors"] if "surface_factors" in row
                                else [row["factors"][name] for name in names], dtype=float)
            mu = _read_action_centroids(scorer, category)
            investigator = VLDInvestigator(mu, sigma, names, tau=tau)
            provider = provider_class(evidence_source, identifier)
            expected = row.get("expected_vld_action", row.get("expected_action"))
            surface_claim = row["surface_action"]
            if expected not in actions or surface_claim not in actions:
                raise ValueError(f"{identifier}: preseed action labels absent from {actions}")
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            k_dependent = bool(row.get("k_dependent") or metadata.get("k_dependent"))
            evidence = {str(dim): provider.read_evidence(identifier, dim, name) for dim, name in enumerate(names)}
            trace, reads = record_reads(provider, lambda: investigator.investigate(
                identifier, category, vector, provider, budget=2, gated_sources=set(runtime["gated_sources"])))
            unit_k_trace = unit_k_reads = learned_k_trace = learned_k_reads = None
            learned_k_weights = metadata.get("learned_k_weights") if isinstance(metadata.get("learned_k_weights"), list) else None
            if k_dependent:
                unit_provider = provider_class(evidence_source, identifier)
                unit_k_trace, unit_k_reads = record_reads(unit_provider, lambda: investigator.investigate(
                    identifier, category, vector, unit_provider, budget=2,
                    K_weights=np.full(len(names), 0.5, dtype=float),
                    gated_sources=set(runtime["gated_sources"])))
                if learned_k_weights is not None:
                    learned_provider = provider_class(evidence_source, identifier)
                    learned_k_trace, learned_k_reads = record_reads(learned_provider, lambda: investigator.investigate(
                        identifier, category, vector, learned_provider, budget=2,
                        K_weights=np.asarray(learned_k_weights, dtype=float),
                        gated_sources=set(runtime["gated_sources"])))
            # Exercise the real router handler with the same production components.
            # Calling the handler directly avoids TestClient's background thread
            # and permits recording calls without modifying any provider method.
            router = create_investigation_router(lambda: scorer, lambda decision_id: provider,
                                                  classifier=classifier, factor_names=names,
                                                  default_budget=runtime["default_budget"],
                                                  gated_sources=set(runtime["gated_sources"]))
            endpoint = next(route.endpoint for route in router.routes if route.path.endswith("/investigate"))
            response = endpoint(InvestigationRequest(decision_id=identifier, category=category,
                                                     factor_vector=vector.tolist(), budget=2))
            factor_dict = {name: float(vector[pos]) for pos, name in enumerate(names)}
            read_only = scorer.score_read_only(factor_dict, category)
            read_only_action = actions[int(read_only.action_index)]
            auto_budget = row.get("budget")
            auto_response, auto_reads = record_reads(provider, lambda: endpoint(InvestigationRequest(
                decision_id=identifier, category=category, factor_vector=vector.tolist(), budget=auto_budget)))
            classifier_provider = provider_class(evidence_source, identifier)
            classifier_response, classifier_reads = record_reads(classifier_provider, lambda: endpoint(InvestigationRequest(
                decision_id=identifier, category=category, factor_vector=vector.tolist(), budget=None)))
            final_vector = trace.steps[-1].v_after if trace.steps else vector.tolist()
            needed = list(NARRATIVE_DIMS[domain][index])
            required_nonempty = [dim for dim in needed if not (identifier == "VLD-SOC-2" and dim == 2)]
            missing = [dim for dim in required_nonempty if evidence[str(dim)] is None]
            actual_surface, actual_final = actions[trace.surface_action], actions[trace.final_action]
            read_dimensions = [read["dimension"] for read in reads]
            narrative_match = (read_dimensions[:len(needed)] == needed if needed else True)
            if identifier == "VLD-SOC-2":
                narrative_match = (len(reads) >= 2 and reads[0]["dimension"] == 2
                                   and reads[0]["evidence"] is None and reads[1]["dimension"] == 0)
            tier_labels = ["PLANTED"]
            tier_labels.insert(0, "K_DEPENDENT" if k_dependent else "REAL_COMPONENT")
            seed_path = BACKENDS[domain] / "app/vld_preseed.py"
            result = {
                "scenario": identifier, "category": category, "factor_vector": vector.tolist(),
                "claimed_surface_action": surface_claim, "claimed_vld_action": expected,
                "claimed_flip": surface_claim != expected, "is_s1": "S1" in identifier,
                "surface_action": actual_surface, "final_action": actual_final,
                "surface_margin": trace.surface_margin, "final_margin": trace.final_margin,
                "k_dependent": k_dependent, "evidence_tier": tier_labels,
                "learned_k_weights": learned_k_weights,
                "unit_k_action": (actions[unit_k_trace.final_action] if unit_k_trace is not None else None),
                "unit_k_margin": (unit_k_trace.final_margin if unit_k_trace is not None else None),
                "unit_k_reads": unit_k_reads,
                "learned_k_action": (actions[learned_k_trace.final_action] if learned_k_trace is not None else None),
                "learned_k_margin": (learned_k_trace.final_margin if learned_k_trace is not None else None),
                "learned_k_reads": learned_k_reads,
                "learned_k_steps": ([asdict(step) for step in learned_k_trace.steps] if learned_k_trace is not None else None),
                "score_read_only_surface_action": read_only_action,
                "scorer_parity": read_only_action == actual_surface and response["surface_action"] == trace.surface_action,
                "classifier_response": classifier_response, "classifier_reads": classifier_reads,
                "s1_classifier_budget_zero": (classifier_response["budget_used"] == 0 if "S1" in identifier else None),
                "flip": actual_surface != actual_final,
                "match": actual_surface == surface_claim and actual_final == expected,
                "hurt": actual_surface == expected and actual_final != expected,
                "fragile": surface_claim != expected and trace.final_margin <= 0.05,
                "very_fragile": surface_claim != expected and trace.final_margin < 0.02,
                "steps": [asdict(step) for step in trace.steps], "reads": reads,
                "evidence": evidence, "evidence_dims": needed, "missing_required_evidence": missing,
                "narrative_reads_match": narrative_match,
                "protocol": isinstance(provider, EvidenceProvider), "router_response": response,
                "auto_response": auto_response, "auto_reads": auto_reads,
                "source": reference(seed_path, identifier),
                "provider_source": reference(BACKENDS[domain] / "app/evidence_provider.py", "def read_evidence("),
                "counterfactual_final_factor_grid": (one_dimension_sensitivity(investigator, final_vector, actions.index(expected))
                                                       if actual_final != expected else []),
            }
            results.append(result)
        return {"domain": domain, "error": None, "wiring": runtime, "provenance": provenance,
                "scenarios": results, "mu": tensor[0].tolist(), "mu_category": categories[0],
                "all_category_mu": {name: tensor[index].tolist() for index, name in enumerate(categories)},
                "pre_restore_hash": l5_restore["pre_restore_hash"],
                "post_restore_hash": l5_restore["post_restore_hash"],
                "l5_rows_total": l5_restore["l5_rows_total"],
                "l5_rows_applied": l5_restore["l5_rows_applied"],
                "sigma": sigma.tolist(), "tau": tau, "tensor_shape": list(tensor.shape),
                "factor_names": names, "action_names": actions, "category_names": categories,
                "n_actions": len(actions), "n_factors": len(names)}
    finally:
        store.close()


def worker(domain: str) -> dict[str, Any]:
    sys.path[:0] = [str(BACKENDS[domain]), str(SDK), str(WORKSPACE / "ci-platform")]
    # The only temporary persistence is an isolated constructor outbox, not a
    # production store. The TemporaryDirectory is removed on normal/error exit.
    with tempfile.TemporaryDirectory(prefix="vld-astra-") as scratch:
        previous = os.environ.get("CI_PERSISTENCE_OUTBOX_PATH")
        os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = str(Path(scratch) / "outbox.db")
        try:
            return collect_domain(domain)
        except Exception as exc:
            return {"domain": domain, "error": f"{type(exc).__name__}: {exc}", "scenarios": []}
        finally:
            if previous is None:
                os.environ.pop("CI_PERSISTENCE_OUTBOX_PATH", None)
            else:
                os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = previous


@lru_cache(maxsize=1)
def collect_all() -> dict[str, dict[str, Any]]:
    results = {}
    for domain in DOMAINS:
        try:
            process = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--worker", domain],
                                     cwd=SDK, text=True, encoding="utf-8", capture_output=True, timeout=90,
                                     env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
            if process.returncode:
                raise RuntimeError(f"worker exit {process.returncode}: {process.stderr[-1500:]}")
            results[domain] = json.loads(process.stdout)
        except Exception as exc:
            results[domain] = {"domain": domain, "error": f"{type(exc).__name__}: {exc}", "scenarios": []}
    return results


def mock_inventory() -> list[dict[str, str]]:
    """Inventory real source call sites; never invent a d1/cat -> showcase join."""
    inventory = []
    paths = [SDK / "tests", *(root / "tests" for root in BACKENDS.values())]
    for root in paths:
        for path in sorted(root.rglob("test_*.py")):
            if path.name == "test_vld_integration.py":
                continue
            source = path.read_text(encoding="utf-8-sig")
            if "MockEvidenceProvider" not in source:
                continue
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "MockEvidenceProvider":
                    continue
                owners = [owner for owner in ast.walk(tree) if isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and owner.end_lineno is not None
                          and owner.lineno <= node.lineno <= owner.end_lineno]
                owner = min(owners, key=lambda item: (item.end_lineno or item.lineno) - item.lineno) if owners else None
                owner_names = {item.name for item in owners}
                consumers = [f"{item.name}:{item.lineno}" for item in ast.walk(tree)
                             if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                             and item.name.startswith("test_")
                             and any(arg.arg in owner_names for arg in item.args.args)]
                test_label = owner.name if owner else "module"
                if consumers:
                    test_label += "; fixture consumers: " + ", ".join(consumers)
                inventory.append({"copilot": "SDK generic", "test": owner.name if owner else "module",
                                  "source": f"{path.relative_to(WORKSPACE).as_posix()}:{node.lineno}",
                                  "mock": ast.unparse(node.args[0]) if node.args else "unspecified",
                                  "real": "N/A: generic d1/cat and synthetic factor names; no real scenario key",
                                  "delta": "N/A", "flag": "UNMAPPED; substitution pass/fail not established"})
                inventory[-1]["test"] = test_label
                if owner is not None and owner.name == "test_evidence_provider_protocol_runtime":
                    inventory[-1]["flag"] = "Protocol assertion passes for all five real classes; numeric comparison N/A"
    return inventory


def verdict(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = [row for result in results.values() for row in result["scenarios"]]
    complete = len(rows) == 15 and all(not result["error"] and len(result["scenarios"]) == 3 for result in results.values())
    claimed = [row for row in rows if row["claimed_flip"]]
    def row_matches(row):
        if row["k_dependent"]:
            return (row["unit_k_action"] == row["surface_action"]
                    and row["learned_k_action"] == row["claimed_vld_action"])
        return row["match"]
    def row_stable(row):
        if row["k_dependent"]:
            return bool(row["learned_k_margin"] is not None and row["learned_k_margin"] > 0.05)
        return row["final_margin"] > 0.05
    match = complete and len(claimed) == 10 and all(row_matches(row) for row in rows)
    stable = complete and len(claimed) == 10 and all(row_stable(row) for row in claimed)
    hurts = sum(row["hurt"] for row in rows)
    paper = match and stable and hurts == 0
    return {"ALL_FLIPS_MATCH": match, "ALL_MARGINS_STABLE": stable,
            "MOCK_DIVERGENCE_COUNT": sum(isinstance(item["delta"], (int, float)) and item["delta"] > 0.1
                                         for item in mock_inventory()),
            "MOCK_COMPARISON_STATUS": "generic mock cases unmapped; numeric count is not a clean bill",
            "K_STORE_EXERCISED": any(result.get("wiring", {}).get("k_store_exercised", False) for result in results.values()),
            "CLASSIFIER_MODEL_LOADED": any(result.get("wiring", {}).get("model_loaded", False) for result in results.values()),
            "HURTS": hurts if complete else None, "COMPLETE": complete,
            "ALL_NARRATIVE_READS_MATCH": complete and all(row["narrative_reads_match"] for row in rows),
            "ALL_S1_BUDGETS_ZERO": complete and all(row["auto_response"]["budget_used"] == 0 and row["s1_classifier_budget_zero"] for row in rows if row["is_s1"]),
            "ALL_SCORER_PARITY": complete and all(row["scorer_parity"] for row in rows),
            "PAPER_READY": paper, "DEMO_READY": paper and not any(row["fragile"] for row in rows),
            "LIVE_AGE_VALIDATED": False}


def table(headers, rows):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        print("| " + " | ".join(cell(value) for value in row) + " |")
    print()


def print_report(results):
    print("# VLD-ASTRA-SWEEP — offline real-component validation\n")
    print(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
    print("Scope: real CompoundingScorer and EvidenceProvider code with local checkpoint snapshots and real showcase seed functions. "
          "No live AGE or running-app state is certified. Ground truth below means the preseed's claimed action, not an independently verified outcome. "
          "All scenario matrix runs request budget=2; omitted-budget router behavior is shown separately.\n")
    print("Authority note: MAP VLD Addendum v12 was not found. The supplied sweep prompt defines the gate; "
          "the historical mock audit is `copilot-sdk/docs/quality/frontend_wiring_and_mock_audit.md:21`.\n")
    print("## 1 — Per-copilot scenario matrix\n")
    for domain, result in results.items():
        print(f"### {domain}\n")
        if result["error"]:
            print(f"P0 WIRING: {result['error']}. All three scenarios unavailable.\n")
            continue
        p = result["provenance"]
        print(f"Centroids: **{p['centroid_source']}**, shape {result['tensor_shape']}; "
              f"{p['checkpoint_count']} checkpoints, {p['decisions']} decisions, {p['verified_decisions']} verified. "
              f"L5 rows applied: {p.get('l5_rows_applied', 'n/a')}/{p.get('l5_rows_total', 'n/a')}; "
              f"pre/post hashes: {p.get('pre_restore_hash', '')[:12]} / {p.get('post_restore_hash', '')[:12]}. "
              f"Sigma: {p['sigma_source']}; tau={result['tau']}. Sources: `{p['source']}`, `{p['sigma_reference']}`.\n")
        print(f"Database: `{p['database']}`; latest checkpoint: `{p['latest_checkpoint']}`. "
              f"Construction: {p['construction']}.\n")
        print(f"Evidence scope: {p['evidence_scope']}. Identical action centroids by category: "
              f"`{json.dumps(p['identical_action_centroids_by_category'])}`. "
              "Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.\n")
        table(["Scenario", "Tier", "Surface act", "Surf margin", "VLD act", "VLD margin", "Flip?", "Claimed", "MATCH", "Steps taken"], [
            [r["scenario"], " + ".join(r["evidence_tier"]), r["surface_action"], f"{r['surface_margin']:.8f}", r["final_action"], f"{r['final_margin']:.8f}",
             r["flip"], f"{r['claimed_surface_action']} -> {r['claimed_vld_action']}", r["match"],
             "; ".join(f"{s['factor_name']}({s['v_before'][s['dimension']]:.4f}->{s['v_after'][s['dimension']]:.4f})" for s in r["steps"]) or "none"]
            for r in result["scenarios"]])
        for r in result["scenarios"]:
            print(f"**{r['scenario']}** — seed `{r['source']}`; provider `{r['provider_source']}`.\n")
            print("Real reads by dimension (including None): `" + json.dumps(r["evidence"], sort_keys=True) + "`\n")
            print("Attempted order: `" + json.dumps([{"dim": read["dimension"], "empty": read["evidence"] is None} for read in r["reads"]]) + "`. "
                  f"Narrative dimensions: {r['evidence_dims']}; missing required evidence: {r['missing_required_evidence']}. "
                  "Empty reads consume budget but are omitted from core trace steps "
                  "(`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).\n")
            auto = r["auto_response"]
            print(f"Omitted-budget router: situation={auto['situation']}, budget={auto['budget_used']}, "
                  f"attempts={len(r['auto_reads'])}, final={result['action_names'][auto['final_action']]}. "
                  f"Fragile at <=0.05: {r['fragile']}; below 0.02: {r['very_fragile']}.\n")
            if not r["narrative_reads_match"]:
                print("**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. "
                      "An action match alone does not validate the demo's evidence story.\n")
            if r["is_s1"] and (r["surface_margin"] <= 0.3 or auto["budget_used"] != 0):
                print(f"**P0 S1 CONTRACT:** surface margin={r['surface_margin']:.8f}; omitted-budget allocation={auto['budget_used']}, "
                      f"situation={auto['situation']}. Claimed high-margin/no-investigation behavior is not satisfied.\n")
            if not r["match"]:
                print(f"**P0 PRESEED MISMATCH:** claimed {r['claimed_surface_action']} -> {r['claimed_vld_action']}; "
                      f"actual {r['surface_action']} -> {r['final_action']}.\n")
                print("One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; "
                      "NOT real evidence, NOT a routed replay or proposed seed fix): `" + json.dumps(r["counterfactual_final_factor_grid"]) + "`. "
                      "An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. "
                      "Surface mismatches cannot be repaired by evidence read after surface scoring.\n")
            if r["missing_required_evidence"]:
                print(f"**P1 EVIDENCE GAP:** required nonempty dimensions {r['missing_required_evidence']}.\n")
    print("## 2 — Summary\n")
    summary = []
    for name, result in results.items():
        rows = result["scenarios"]
        summary.append([name, len(rows), sum(r["claimed_flip"] for r in rows), sum(r["flip"] for r in rows),
                        sum(r["match"] for r in rows), sum(not r["match"] for r in rows), sum(r["fragile"] for r in rows)])
    summary.append(["TOTAL", *[sum(row[i] for row in summary) for i in range(1, 7)]])
    table(["Copilot", "Scenarios", "Flips claimed", "Flips actual", "Match", "Mismatch", "Fragile"], summary)
    print("## 3 — K store and classifier status\n")
    table(["Copilot", "K store wired", "K has data (local)", "Classifier wired", "Model loaded", "Fallback", "Source"], [
        [name, *[r.get("wiring", {}).get(key, "UNKNOWN") for key in
                 ("k_store_wired", "k_has_data", "classifier_wired", "model_loaded", "fallback", "source")]] for name, r in results.items()])
    print("Classifier heuristic: `copilot-sdk/copilot_sdk/scoring/situation_classifier.py:122`; model load: line 95. "
          "SOC/Trading have no classifier; high margin alone does not suppress their default budget. "
          "K updates require a connected SQL store (`copilot-sdk/copilot_sdk/scoring/investigation.py:194`).\n")
    print("## 4 — Mock divergence inventory\n")
    print("The only MockEvidenceProvider call sites found in SDK/app/SOC/S2P test directories use synthetic SDK d1/cat inputs. "
          "Those inputs have no real scenario join, so a numerical delta or substituted-test pass claim would be fabricated. "
          "All call sites are listed below, including the client fixture used by router tests.\n")
    table(["Copilot", "Test/source", "Dim/mock payload", "Real value", "Delta", "Flag"], [
        [r["copilot"], f"{r['test']} ({r['source']})", r["mock"], r["real"], r["delta"], r["flag"]] for r in mock_inventory()])
    print("The five domain evidence suites already use real provider classes. Their significant substitutions concern geometry, sigma, "
          "K weights, or S1 vectors; replacing a provider alone would leave those substitutions intact.\n")
    gaps = [
        ("soc", "test_vld_soc1_scenario_flips_monitor_to_escalate", "hand-built mu and sigma=0.1"),
        ("soc", "test_vld_soc2_empty_branch_then_recompute_flips", "hand-built mu/sigma; budget=3"),
        ("soc", "test_s1_no_investigation_budget_zero", "replaces showcase vector with centroid; classifier absent in app"),
        ("soc", "test_router_investigate_alert", "monkeypatches real scorer with FakeScorer"),
        ("trading", "test_thesis_reversal_flips_strong_to_partial", "post-regen trend_following mu and sigma=0.1"),
        ("trading", "test_concentration_risk_flips_strong_to_partial", "post-regen trend_following mu and dimension-specific sigma"),
        ("trading", "test_thesis_reversal_trace_order", "hand-built mu and sigma"),
        ("trading", "test_s1_conservation_no_investigation", "centroid replaces showcase vector; classifier absent in app"),
        ("trading", "test_investigation_endpoint", "monkeypatches scorer with FakeScorer"),
        ("purchasing", "test_demand_spike", "hand-built mu/sigma/tau and injected K weights"),
        ("purchasing", "test_vendor_cascade", "hand-built mu/sigma/tau and injected K weights"),
        ("purchasing", "test_demand_spike_trace_order", "hand-built mu/sigma/tau and injected K weights"),
        ("purchasing", "test_s1_conservation", "hand-built geometry"),
        ("dataops", "test_vld_do1_three_systems", "preset mu, injected K weights and preset tau"),
        ("dataops", "test_vld_do2_known_pattern_new_twist", "preset mu, injected K weights and preset tau"),
        ("dataops", "test_s1_conservation_skip", "centroid replaces showcase vector"),
        ("s2p", "test_vld_s2p1_supplier_it_knew", "domain-config mu/tau and injected K weights"),
        ("s2p", "test_vld_s2p2_price_spike_context", "domain-config mu/tau and injected K weights"),
        ("s2p", "test_investigation_endpoint", "custom Scorer wrapper over config; asserts response structure"),
    ]
    table(["Copilot", "Test", "Actual substitution", "Source"], [
        [domain, name, gap, reference(BACKENDS[domain] / f"tests/test_{domain}_evidence.py", f"def {name}(")]
        for domain, name, gap in gaps])
    print("Provider-value comparison: SOC/Trading seeded values equal their registered real-provider values; "
          "Purchasing/DataOps/S2P tests read the same real seeded source. No comparable numeric mock-provider divergence >0.1 was established. "
          "UNMAPPED entries remain unmeasured, not zero-distance observations.\n")
    print("## 5 — Gate verdict\n")
    for key, value in verdict(results).items():
        print(f"- **{key}:** {value}")
    print("\nPAPER_READY/DEMO_READY apply only to the prompt's 15 showcase contracts. They do not establish "
          "empirical routing accuracy, independent ground truth, or live AGE fidelity. Missing domains fail completeness.\n")
    print("Baseline at implementation gate: SDK 3402 passed; VLD core 30, DataOps 14, Trading 13, Purchasing 13 passed. "
          "These are recorded pre-sweep results, not tests rerun by this report.\n")
    for relative in ("copilot_sdk/scoring/investigation.py", "copilot_sdk/backend/investigation_router.py"):
        print(f"- Current SHA-256 `{relative}`: `{hashlib.sha256((SDK / relative).read_bytes()).hexdigest()}`")


if __name__ == "__main__":
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")
    if len(sys.argv) == 3 and sys.argv[1] == "--worker" and sys.argv[2] in DOMAINS:
        with redirect_stdout(sys.stderr):
            payload = worker(sys.argv[2])
        print(json.dumps(payload, allow_nan=False))
    else:
        print_report(collect_all())
