"""
GEDT v11.0 Scenario Benchmark Tests

Tests the controlled economic scenario experiment for:
- deterministic behavior
- scenario coverage
- numerical validity
- baseline comparison
- reproducibility
"""

from __future__ import annotations

import json

from gedt.scenario_benchmark import (
    BENCHMARK_NAME,
    BENCHMARK_VERSION,
    calculate_differences,
    initial_state,
    run_scenario_benchmark,
    scenarios,
    save_result,
    validate_result,
)


def test_benchmark_metadata():
    result = run_scenario_benchmark(periods=12)

    assert result["benchmark"]["name"] == BENCHMARK_NAME
    assert result["benchmark"]["version"] == BENCHMARK_VERSION


def test_initial_state():
    state = initial_state()

    assert state.period == 0
    assert state.gdp == 1000.0
    assert state.inflation == 0.02
    assert state.unemployment == 0.05


def test_expected_scenarios_exist():
    scenario_list = scenarios()

    names = {
        scenario.name
        for scenario in scenario_list
    }

    expected = {
        "baseline",
        "demand_expansion",
        "demand_contraction",
        "supply_disruption",
        "supply_improvement",
        "tight_policy",
        "accommodative_policy",
    }

    assert names == expected


def test_scenario_count():
    assert len(scenarios()) == 7


def test_benchmark_returns_all_scenarios():
    result = run_scenario_benchmark(
        periods=12
    )

    assert len(result["scenarios"]) == 7


def test_baseline_exists():
    result = run_scenario_benchmark(
        periods=12
    )

    names = [
        item["scenario"]
        for item in result["scenarios"]
    ]

    assert "baseline" in names


def test_all_final_gdp_values_are_positive():
    result = run_scenario_benchmark(
        periods=12
    )

    for item in result["scenarios"]:
        assert item["final_gdp"] > 0


def test_results_are_numeric():
    result = run_scenario_benchmark(
        periods=12
    )

    numeric_fields = {
        "initial_gdp",
        "final_gdp",
        "gdp_growth",
        "average_inflation",
        "average_unemployment",
    }

    for item in result["scenarios"]:
        for field in numeric_fields:
            assert isinstance(
                item[field],
                (int, float),
            )


def test_demand_expansion_changes_output():
    result = run_scenario_benchmark(
        periods=12
    )

    rows = {
        item["scenario"]: item
        for item in result["scenarios"]
    }

    baseline = rows["baseline"]
    expansion = rows["demand_expansion"]

    assert (
        expansion["final_gdp"]
        != baseline["final_gdp"]
    )


def test_demand_contraction_changes_output():
    result = run_scenario_benchmark(
        periods=12
    )

    rows = {
        item["scenario"]: item
        for item in result["scenarios"]
    }

    baseline = rows["baseline"]
    contraction = rows["demand_contraction"]

    assert (
        contraction["final_gdp"]
        != baseline["final_gdp"]
    )


def test_supply_disruption_changes_output():
    result = run_scenario_benchmark(
        periods=12
    )

    rows = {
        item["scenario"]: item
        for item in result["scenarios"]
    }

    baseline = rows["baseline"]
    disruption = rows["supply_disruption"]

    assert (
        disruption["final_gdp"]
        != baseline["final_gdp"]
    )


def test_policy_scenarios_change_output():
    result = run_scenario_benchmark(
        periods=12
    )

    rows = {
        item["scenario"]: item
        for item in result["scenarios"]
    }

    baseline = rows["baseline"]
    tight = rows["tight_policy"]
    accommodative = rows[
        "accommodative_policy"
    ]

    assert (
        tight["final_gdp"]
        != baseline["final_gdp"]
    )

    assert (
        accommodative["final_gdp"]
        != baseline["final_gdp"]
    )


def test_baseline_difference_is_zero():
    result = run_scenario_benchmark(
        periods=12
    )

    differences = calculate_differences(
        result
    )

    baseline = next(
        item
        for item in differences
        if item["scenario"] == "baseline"
    )

    assert baseline["final_gdp_difference"] == 0.0
    assert baseline["growth_difference"] == 0.0
    assert (
        baseline["inflation_difference"]
        == 0.0
    )
    assert (
        baseline["unemployment_difference"]
        == 0.0
    )


def test_scenario_comparison_contains_all_results():
    result = run_scenario_benchmark(
        periods=12
    )

    differences = calculate_differences(
        result
    )

    assert len(differences) == 7

    result_names = {
        item["scenario"]
        for item in result["scenarios"]
    }

    difference_names = {
        item["scenario"]
        for item in differences
    }

    assert result_names == difference_names


def test_scenario_benchmark_is_deterministic():
    first = run_scenario_benchmark(
        periods=12
    )

    second = run_scenario_benchmark(
        periods=12
    )

    assert first["scenarios"] == second[
        "scenarios"
    ]


def test_different_periods_change_results():
    short = run_scenario_benchmark(
        periods=6
    )

    long = run_scenario_benchmark(
        periods=12
    )

    short_rows = {
        item["scenario"]: item
        for item in short["scenarios"]
    }

    long_rows = {
        item["scenario"]: item
        for item in long["scenarios"]
    }

    assert (
        short_rows["baseline"]["final_gdp"]
        != long_rows["baseline"]["final_gdp"]
    )


def test_validation_passes():
    result = run_scenario_benchmark(
        periods=12
    )

    validate_result(result)


def test_result_can_be_saved(tmp_path):
    result = run_scenario_benchmark(
        periods=12
    )

    output = (
        tmp_path
        / "scenario_benchmark.json"
    )

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

    assert (
        loaded["benchmark"]["name"]
        == BENCHMARK_NAME
    )

    assert (
        len(loaded["scenarios"])
        == 7
    )

    assert (
        "differences_from_baseline"
        in loaded
    )


def test_invalid_periods_are_rejected():
    try:
        run_scenario_benchmark(
            periods=0
        )
    except ValueError:
        return

    raise AssertionError(
        "periods=0 should raise ValueError"
    )


def test_single_period_is_valid():
    result = run_scenario_benchmark(
        periods=1
    )

    assert len(result["scenarios"]) == 7


def test_scenario_benchmark_json_serializable():
    result = run_scenario_benchmark(
        periods=12
    )

    encoded = json.dumps(
        result,
        sort_keys=True,
    )

    decoded = json.loads(encoded)

    assert (
        decoded["benchmark"]["name"]
        == BENCHMARK_NAME
    )