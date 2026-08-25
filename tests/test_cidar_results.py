from pathlib import Path

from gedt.cidar_protocol import CIDARBenchmarkConfig, run_protocol
from gedt.cidar_results import (
    append_result,
    best_result,
    compare_rmse,
    load_result,
    load_results,
    regression_report,
    save_result,
)


def make_config():
    return CIDARBenchmarkConfig(
        dataset_name="synthetic",
        dataset_version="1.0",
        sensors=("camera", "lidar", "radar"),
        distance_min=1.0,
        distance_max=100.0,
        seed=42,
        measurements_per_trial=20,
        noise_std=0.25,
    )


def make_result(predictions):
    return run_protocol(
        [1.0, 10.0, 50.0],
        predictions,
        make_config(),
    )


def test_save_and_load(tmp_path: Path):
    record = make_result(
        [1.1, 9.9, 50.2]
    )

    path = tmp_path / "result.json"

    save_result(
        record,
        path,
    )

    loaded = load_result(path)

    assert loaded == record


def test_jsonl_append_and_load(tmp_path: Path):
    first = make_result(
        [1.1, 9.9, 50.2]
    )

    second = make_result(
        [1.01, 10.01, 50.01]
    )

    path = tmp_path / "results.jsonl"

    append_result(first, path)
    append_result(second, path)

    results = load_results(path)

    assert len(results) == 2
    assert results[0] == first
    assert results[1] == second


def test_best_result():
    baseline = make_result(
        [1.5, 9.5, 51.0]
    )

    improved = make_result(
        [1.01, 10.01, 50.01]
    )

    assert best_result(
        [baseline, improved]
    ) == improved


def test_rmse_improvement():
    baseline = make_result(
        [1.5, 9.5, 51.0]
    )

    candidate = make_result(
        [1.01, 10.01, 50.01]
    )

    improvement = compare_rmse(
        baseline,
        candidate,
    )

    assert improvement > 0.0


def test_regression_report():
    baseline = make_result(
        [1.1, 9.9, 50.2]
    )

    candidate = make_result(
        [1.01, 10.01, 50.01]
    )

    report = regression_report(
        baseline,
        candidate,
    )

    assert "CIDAR REGRESSION REPORT" in report
    assert "Baseline RMSE:" in report
    assert "Candidate RMSE:" in report
    assert "IMPROVED" in report