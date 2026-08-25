from gedt.cidar_benchmark import (
    benchmark_summary,
    generate_case,
    generate_dataset,
    run_benchmark,
    sensor_rmse,
)


def test_generate_case():
    case = generate_case(
        10.0,
        seed=42,
    )

    assert case.true_distance == 10.0
    assert case.camera.sensor == "camera"
    assert case.lidar.sensor == "lidar"
    assert case.radar.sensor == "radar"


def test_generate_dataset_is_reproducible():
    first = generate_dataset(
        [1.0, 5.0, 10.0],
        seed=42,
    )

    second = generate_dataset(
        [1.0, 5.0, 10.0],
        seed=42,
    )

    assert first == second


def test_benchmark_runs():
    cases = generate_dataset(
        [1.0, 5.0, 10.0, 25.0],
        seed=42,
    )

    result = run_benchmark(cases)

    assert result.valid
    assert result.cases == 4
    assert result.rmse >= 0.0
    assert result.mean_absolute_error >= 0.0


def test_lidar_is_more_accurate_than_noisy_camera():
    cases = generate_dataset(
        [1.0, 5.0, 10.0, 25.0, 50.0],
        camera_noise=2.0,
        lidar_noise=0.05,
        seed=42,
    )

    camera_error = sensor_rmse(
        cases,
        "camera",
    )

    lidar_error = sensor_rmse(
        cases,
        "lidar",
    )

    assert lidar_error < camera_error


def test_summary_contains_status():
    cases = generate_dataset(
        [1.0, 5.0, 10.0],
        seed=42,
    )

    result = run_benchmark(cases)
    summary = benchmark_summary(result)

    assert "CIDAR SYNTHETIC BENCHMARK" in summary
    assert "Status: PASS" in summary
    assert "RMSE:" in summary