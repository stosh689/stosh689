"""Tests for GEDT v11.0 performance benchmarking."""

import json

import pytest

from gedt.performance_benchmark import (
    BENCHMARK_NAME,
    BENCHMARK_VERSION,
    measure_execution,
    run_performance_benchmark,
    run_scaling_benchmark,
    save_performance_benchmark,
    save_scaling_benchmark,
    validate_performance_benchmark,
    validate_scaling_benchmark,
)


def make_benchmark():
    """Create a small performance benchmark."""
    return run_performance_benchmark(
        periods=3,
        trials=10,
        seed=42,
        repeats=2,
    )


def test_benchmark_metadata():
    benchmark = make_benchmark()

    assert benchmark["benchmark"]["name"] == BENCHMARK_NAME
    assert benchmark["benchmark"]["version"] == BENCHMARK_VERSION


def test_experiment_parameters():
    benchmark = make_benchmark()

    experiment = benchmark["experiment"]

    assert experiment["periods"] == 3
    assert experiment["trials"] == 10
    assert experiment["seed"] == 42
    assert experiment["repeats"] == 2


def test_measurement_count():
    benchmark = make_benchmark()

    assert len(benchmark["measurements"]) == 2


def test_measurements_have_runtime():
    benchmark = make_benchmark()

    for measurement in benchmark["measurements"]:
        assert measurement["elapsed_seconds"] >= 0
        assert measurement["result_generated"] is True


def test_statistics_exist():
    benchmark = make_benchmark()

    statistics = benchmark["statistics"]

    assert "mean_seconds" in statistics
    assert "median_seconds" in statistics
    assert "minimum_seconds" in statistics
    assert "maximum_seconds" in statistics
    assert (
        "throughput_period_trial_units_per_second"
        in statistics
    )


def test_runtime_statistics_are_nonnegative():
    benchmark = make_benchmark()

    statistics = benchmark["statistics"]

    assert statistics["mean_seconds"] >= 0
    assert statistics["median_seconds"] >= 0
    assert statistics["minimum_seconds"] >= 0
    assert statistics["maximum_seconds"] >= 0
    assert (
        statistics[
            "throughput_period_trial_units_per_second"
        ]
        >= 0
    )


def test_minimum_does_not_exceed_maximum():
    benchmark = make_benchmark()

    statistics = benchmark["statistics"]

    assert (
        statistics["minimum_seconds"]
        <= statistics["maximum_seconds"]
    )


def test_mean_is_within_runtime_bounds():
    benchmark = make_benchmark()

    statistics = benchmark["statistics"]

    assert (
        statistics["minimum_seconds"]
        <= statistics["mean_seconds"]
        <= statistics["maximum_seconds"]
    )


def test_measure_execution():
    result = measure_execution(
        periods=2,
        trials=5,
        seed=42,
    )

    assert result["periods"] == 2
    assert result["trials"] == 5
    assert result["seed"] == 42
    assert result["elapsed_seconds"] >= 0
    assert result["result_generated"] is True


def test_invalid_periods():
    with pytest.raises(ValueError):
        run_performance_benchmark(
            periods=0,
            trials=10,
            seed=42,
            repeats=1,
        )


def test_invalid_trials():
    with pytest.raises(ValueError):
        run_performance_benchmark(
            periods=3,
            trials=0,
            seed=42,
            repeats=1,
        )


def test_invalid_repeats():
    with pytest.raises(ValueError):
        run_performance_benchmark(
            periods=3,
            trials=10,
            seed=42,
            repeats=0,
        )


def test_measure_execution_invalid_periods():
    with pytest.raises(ValueError):
        measure_execution(
            periods=0,
            trials=10,
            seed=42,
        )


def test_measure_execution_invalid_trials():
    with pytest.raises(ValueError):
        measure_execution(
            periods=3,
            trials=0,
            seed=42,
        )


def test_scaling_benchmark():
    scaling = run_scaling_benchmark(
        seed=42,
    )

    assert "workloads" in scaling
    assert len(scaling["workloads"]) == 3


def test_scaling_workload_names():
    scaling = run_scaling_benchmark(
        seed=42,
    )

    names = [
        workload["name"]
        for workload in scaling["workloads"]
    ]

    assert names == [
        "small",
        "baseline",
        "large",
    ]


def test_scaling_workloads_are_valid():
    scaling = run_scaling_benchmark(
        seed=42,
    )

    for workload in scaling["workloads"]:
        assert workload["periods"] > 0
        assert workload["trials"] > 0
        assert workload["elapsed_seconds"] >= 0
        assert workload["result_generated"] is True


def test_scaling_workload_sizes_increase():
    scaling = run_scaling_benchmark(
        seed=42,
    )

    workloads = scaling["workloads"]

    sizes = [
        item["periods"] * item["trials"]
        for item in workloads
    ]

    assert sizes == sorted(sizes)
    assert len(set(sizes)) == len(sizes)


def test_performance_validation():
    benchmark = make_benchmark()

    validate_performance_benchmark(
        benchmark
    )


def test_scaling_validation():
    scaling = run_scaling_benchmark(
        seed=42,
    )

    validate_scaling_benchmark(
        scaling
    )


def test_missing_performance_section_fails():
    benchmark = make_benchmark()

    del benchmark["statistics"]

    with pytest.raises(ValueError):
        validate_performance_benchmark(
            benchmark
        )


def test_missing_scaling_section_fails():
    with pytest.raises(ValueError):
        validate_scaling_benchmark({})


def test_json_serializable():
    benchmark = make_benchmark()

    encoded = json.dumps(
        benchmark,
        indent=2,
        sort_keys=True,
    )

    decoded = json.loads(encoded)

    assert decoded == benchmark


def test_scaling_json_serializable():
    scaling = run_scaling_benchmark(
        seed=42,
    )

    encoded = json.dumps(
        scaling,
        indent=2,
        sort_keys=True,
    )

    decoded = json.loads(encoded)

    assert decoded == scaling


def test_save_performance_benchmark(tmp_path):
    benchmark = make_benchmark()

    output = tmp_path / "performance.json"

    save_performance_benchmark(
        benchmark,
        output,
    )

    assert output.exists()

    loaded = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert loaded == benchmark


def test_save_scaling_benchmark(tmp_path):
    scaling = run_scaling_benchmark(
        seed=42,
    )

    output = tmp_path / "scaling.json"

    save_scaling_benchmark(
        scaling,
        output,
    )

    assert output.exists()

    loaded = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert loaded == scaling


def test_repeated_benchmark_structure_is_stable():
    first = make_benchmark()
    second = make_benchmark()

    assert (
        first["experiment"]
        == second["experiment"]
    )

    assert (
        first["benchmark"]
        == second["benchmark"]
    )


def test_scaling_is_repeatable_in_structure():
    first = run_scaling_benchmark(
        seed=42,
    )

    second = run_scaling_benchmark(
        seed=42,
    )

    first_structure = [
        (
            item["name"],
            item["periods"],
            item["trials"],
        )
        for item in first["workloads"]
    ]

    second_structure = [
        (
            item["name"],
            item["periods"],
            item["trials"],
        )
        for item in second["workloads"]
    ]

    assert first_structure == second_structure


def test_end_to_end_performance_pipeline():
    benchmark = run_performance_benchmark(
        periods=2,
        trials=5,
        seed=42,
        repeats=1,
    )

    scaling = run_scaling_benchmark(
        seed=42,
    )

    validate_performance_benchmark(
        benchmark
    )

    validate_scaling_benchmark(
        scaling
    )

    assert benchmark["statistics"]["mean_seconds"] >= 0
    assert len(scaling["workloads"]) == 3