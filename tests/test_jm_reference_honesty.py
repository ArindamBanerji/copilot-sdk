"""APP-1A acceptance tests for oracle separation and epsilon regimes."""

import ast
import inspect

import numpy as np

from examples.jm_reference import generator
from examples.jm_reference.config import (
    RUN_A_GENERATOR,
    RUN_A_ORACLE,
    RUN_B_ORACLE,
)
from examples.jm_reference.generator import GeneratorConfig, SyntheticGenerator
from examples.jm_reference.oracle import GroundTruthOracle, OracleConfig


def test_oracle_separation() -> None:
    """The generator has no path to a correctness label."""

    source = inspect.getsource(generator)
    tree = ast.parse(source)
    forbidden_names = {"is_correct", "label_correct", "GroundTruthOracle", "oracle"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in forbidden_names
        if isinstance(node, ast.Attribute):
            assert node.attr not in {"is_correct", "label_correct"}
    assert "oracle" not in source.lower().split("import")


def test_generator_deterministic() -> None:
    first = SyntheticGenerator(GeneratorConfig(seed=42))
    second = SyntheticGenerator(GeneratorConfig(seed=42))
    for _ in range(50):
        assert first.generate() == second.generate()


def test_generator_emits_no_label() -> None:
    category, factors = SyntheticGenerator(GeneratorConfig(seed=42)).generate()
    assert isinstance(category, str)
    assert isinstance(factors, dict)
    assert "is_correct" not in factors
    assert "correct" not in factors
    assert "label" not in factors


def test_generator_variance_above_002() -> None:
    generator_instance = SyntheticGenerator(GeneratorConfig(seed=42, n_decisions=100))
    batch = [generator_instance.generate() for _ in range(100)]
    values = np.array(
        [[record[1][key] for key in sorted(record[1])] for record in batch]
    )
    per_factor_variance = values.var(axis=0)
    assert all(value > 0.02 for value in per_factor_variance), per_factor_variance


def test_oracle_labels_by_distance() -> None:
    oracle = GroundTruthOracle(
        OracleConfig(seed=99, n_categories=3, n_actions=3, n_factors=4)
    )
    centroids = oracle.ground_truth_centroids
    vector = {f"factor_{i}": float(centroids[0, 0, i]) for i in range(4)}
    assert oracle.label_correct(0, 0, vector)


def test_epsilon_firm_run_a_above_threshold() -> None:
    assert GroundTruthOracle(RUN_A_ORACLE).measured_epsilon_firm > 0.128


def test_epsilon_firm_run_b_below_threshold() -> None:
    assert GroundTruthOracle(RUN_B_ORACLE).measured_epsilon_firm < 0.128


def test_oracle_different_seed_from_generator() -> None:
    assert RUN_A_GENERATOR.seed != RUN_A_ORACLE.seed
