from pathlib import Path

from gedt.cidar_protocol import CIDARBenchmarkConfig
from gedt.cidar_runner import (
    CIDARRunResult,
    run_and_report,
    run_arrays,
    run_dataset,
)


def make_config():
    return CIDARBenchmarkConfig(
        dataset_name="integration-test",
        dataset_version="1.0",
        sensors=("camera", "lidar", "radar"),
        distance_min=1.0,
        distance_max=100.0,
        seed=42,
        measurements_per_trial=20,
        noise_std=0.25,
    )


def test_run_arrays():
    result = run_arrays(
        [1.0, 10.0, 50.0],
        [1.1, 10.1, 49.9],
        make_config(),
    )

    assert result.valid
    assert result.samples == 3


def test_run_dataset(tmp_path: Path):
    input_path = tmp_path / "dataset.csv"
    output_path = tmp_path / "result.json"

    input_path.write_text(
        "ground_truth,prediction,sample_id\n"
        "1.0,1.1,a\n"
        "10.0,10.1,b\n"
        "50.0,49.9,c\n",
        encoding="utf-8",
    )

    result = run_dataset(
        input_path,
        output_path,
        make_config(),
    )

    assert isinstance(
        result,
        CIDARRunResult,
    )

    assert result.passed
    assert result.record.samples == 3
    assert output_path.exists()


def test_run_result_can_be_reloaded(tmp_path: Path):
    input_path = tmp_path / "dataset.jsonl"
    output_path = tmp_path / "result.json"

    input_path.write_text(
        '{"ground_truth": 1.0, "prediction": 1.1}\n'
        '{"ground_truth": 2.0, "prediction": 2.1}\n',
        encoding="utf-8",
    )

    result = run_dataset(
        input_path,
        output_path,
        make_config(),
    )

    assert result.record.dataset_name == "integration-test"
    assert result.record.seed == 42


def test_run_and_report(tmp_path: Path):
    input_path = tmp_path / "dataset.csv"
    output_path = tmp_path / "result.json"

    input_path.write_text(
        "ground_truth,prediction\n"
        "1.0,1.1\n"
        "2.0,1.9\n",
        encoding="utf-8",
    )

    report = run_and_report(
        input_path,
        output_path,
        make_config(),
    )

    assert "CIDAR EXPERIMENT" in report
    assert "Status: PASS" in report
    assert "RMSE:" in report
    assert "CRLB Variance:" in report