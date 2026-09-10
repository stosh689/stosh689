"""
GEDT v11.0 Benchmark Tests

Verifies that the baseline experiment is deterministic and
reproducible when the same configuration and random seed are used.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmark import (
    DEFAULT_SEED,
    DEFAULT_TRIALS,
    DEFAULT_PERIODS,
    create_baseline_scenario,
    create_initial_state,
    run_benchmark,
    save_result,
    validate_result,
)


def test_benchmark_uses_expected_defaults():
    assert DEFAULT_PERIODS == 12
    assert DEFAULT_TRIALS == 1000
    assert DEFAULT_SEED == 42


def test_initial_state_is_deterministic():
    first = create_initial_state()
    second = create_initial_state()

    assert first == second
    assert first.gdp == 1000.0
    assert first.inflation == 0.02
    assert first.unemployment == 0.05


def test_baseline_scenario_is_deterministic():
    first = create_baseline_scenario()
    second = create_baseline_scenario()

    assert first == second
    assert first.name == "baseline"
    assert first.demand_shock == 0.0
    assert first.supply_shock == 0.0
    assert first.policy_rate_change == 0.0


def test_benchmark_has_required_sections():
    result = run_benchmark(
        periods=12,
        trials=100,
        seed=42,
    )

    required = {
        "benchmark",
        "gedt",
        "experiment",
        "initial_state",
        "scenario",
        "deterministic",
        "monte_carlo",
        "environment",
        "metadata",
    }

    assert required.issubset(result.keys())


def test_benchmark_is_reproducible():
    first = run_benchmark(
        periods=12,
        trials=100,
        seed=42,
    )

    second = run_benchmark(
        periods=12,
        trials=100,
        seed=42,
    )

    first_mc = first["monte_carlo"]
    second_mc = second["monte_carlo"]

    assert first["deterministic"] == second["deterministic"]

    assert first_mc == second_mc


def test_different_seed_changes_stochastic_results():
    first = run_benchmark(
        periods=12,
        trials=100,
        seed=42,
    )

    second = run_benchmark(
        periods=12,
        trials=100,
        seed=99,
    )

    assert first["deterministic"] == second["deterministic"]

    assert (
        first["monte_carlo"]
        != second["monte_carlo"]
    )


def test_benchmark_validation_passes():
    result = run_benchmark(
        periods=12,
        trials=100,
        seed=42,
    )

    validate_result(result)


def test_benchmark_output_can_be_saved(tmp_path: Path):
    result = run_benchmark(
        periods=12,
        trials=100,
        seed=42,
    )

    output = tmp_path / "baseline.json"

    save_result(
        result,
        output,
    )

    assert output.exists()

    loaded = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert loaded["benchmark"]["name"] == (
        "gedt_v11_baseline"
    )

    assert loaded["gedt"]["version"] == "11.0.0"


def test_benchmark_result_is_json_serializable():
    result = run_benchmark(
        periods=12,
        trials=100,
        seed=42,
    )

    encoded = json.dumps(
        result,
        sort_keys=True,
    )

    decoded = json.loads(encoded)

    assert decoded["gedt"]["version"] == "11.0.0"


def test_benchmark_repeated_execution():
    results = []

    for _ in range(3):
        results.append(
            run_benchmark(
                periods=12,
                trials=100,
                seed=42,
            )
        )

    first = results[0]

    for result in results[1:]:
        assert (
            result["deterministic"]
            == first["deterministic"]
        )

        assert (
            result["monte_carlo"]
            == first["monte_carlo"]
        )