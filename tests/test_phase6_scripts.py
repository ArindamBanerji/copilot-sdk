from __future__ import annotations

import importlib

import pytest


def test_seed_604k_value_sum() -> None:
    seed = importlib.import_module("scripts.seed_604k_scenario")
    assert sum(entity["value_amount"] for entity in seed.SCENARIO_ENTITIES) == 604000.0


def test_seed_604k_entity_types() -> None:
    seed = importlib.import_module("scripts.seed_604k_scenario")
    entity_types = {entity["entity_type"] for entity in seed.SCENARIO_ENTITIES}
    assert entity_types == {"sap_change", "celonis_process", "operations_context"}


def test_seed_604k_cross_domain() -> None:
    seed = importlib.import_module("scripts.seed_604k_scenario")
    domains = {domain for _, domain in seed.SCENARIO_LINKS}
    assert len(domains) >= 2


def test_seed_604k_dry_run(capsys) -> None:
    seed = importlib.import_module("scripts.seed_604k_scenario")
    assert seed.main(["--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "no graph writes" in output
    assert "604000.0" in output


def test_trigger_warm_start_dry_run(capsys) -> None:
    trigger = importlib.import_module("scripts.trigger_warm_start")
    assert trigger.main(["--dry-run"]) == 0
    assert "no graph writes" in capsys.readouterr().out


def test_trigger_warm_start_requires_source_target() -> None:
    trigger = importlib.import_module("scripts.trigger_warm_start")
    with pytest.raises(SystemExit):
        trigger.main(["--apply", "--age-dsn", "unused"])
