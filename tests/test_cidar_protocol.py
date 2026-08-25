from gedt.cidar_protocol import (
    CIDARBenchmarkConfig,
    CIDARBenchmarkRecord,
    compare_protocol_runs,
    protocol_report,
    run_protocol,
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


def test_config():
    config = make_config()

    assert config.dataset_name == "synthetic"
    assert config.dataset_version == "1.0"
    assert "lidar" in config.sensors
    assert config.seed == 42


def test_protocol_record():
    config = make_config()

    record = run_protocol(
        [1.0, 10.0, 50.0],
        [1.1, 9.9, 50.2],
        config,
    )

    assert isinstance(
        record,
        CIDARBenchmarkRecord,
    )

    assert record.valid
    assert record.dataset_name == "synthetic"
    assert record.dataset_version == "1.0"
    assert record.samples == 3
    assert record.mae >= 0.0
    assert record.rmse >= 0.0
    assert record.crlb_variance > 0.0


def test_json_is_machine_readable():
    config = make_config()

    record = run_protocol(
        [1.0, 10.0, 50.0],
        [1.0, 10.0, 50.0],
        config,
    )

    payload = record.to_dict()

    assert payload["dataset_name"] == "synthetic"
    assert payload["dataset_version"] == "1.0"
    assert payload["seed"] == 42
    assert "rmse" in payload
    assert "crlb_variance" in payload
    assert "estimator_efficiency" in payload


def test_report():
    config = make_config()

    record = run_protocol(
        [1.0, 10.0, 50.0],
        [1.1, 10.1, 49.9],
        config,
    )

    report = protocol_report(record)

    assert "CIDAR REPRODUCIBLE BENCHMARK" in report
    assert "Dataset: synthetic" in report
    assert "RMSE:" in report
    assert "CRLB Variance:" in report
    assert "Seed: 42" in report


def test_compare_runs():
    config = make_config()

    first = run_protocol(
        [1.0, 10.0],
        [1.1, 9.9],
        config,
    )

    second_config = CIDARBenchmarkConfig(
        dataset_name="synthetic",
        dataset_version="1.0",
        sensors=("lidar",),
        distance_min=1.0,
        distance_max=100.0,
        seed=43,
        measurements_per_trial=20,
        noise_std=0.25,
    )

    second = run_protocol(
        [1.0, 10.0],
        [1.01, 10.01],
        second_config,
    )

    comparison = compare_protocol_runs(
        [first, second]
    )

    assert len(comparison) == 2