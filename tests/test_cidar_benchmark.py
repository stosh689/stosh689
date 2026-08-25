from gedt.cidar_benchmark import (
    BenchmarkSuite,
    benchmark_report,
    default_scenarios,
    run_benchmark,
    run_default_benchmark,
)
def test_default_scenarios():
    scenarios = default_scenarios()
    assert len(scenarios) == 4
    assert scenarios[0].name == "camera"
    assert scenarios[1].name == "lidar"
    assert scenarios[2].name == "radar"
    assert scenarios[3].name == "camera-lidar-radar"
def test_default_benchmark():
    suite = run_default_benchmark()
    assert isinstance(
        suite,
        BenchmarkSuite,
    )
    assert len(suite.records) == 4
    for record in suite.records:
        assert record.valid
        assert record.samples == 5
def test_fusion_beats_camera():
    suite = run_default_benchmark()
    camera = next(
        record
        for record in suite.records
        if record.sensors == ("camera",)
    )
    fusion = next(
        record
        for record in suite.records
        if record.sensors
        == ("camera", "lidar", "radar")
    )
    assert fusion.rmse < camera.rmse
def test_best_configuration():
    suite = run_default_benchmark()
    assert suite.best.sensors == (
        "camera",
        "lidar",
        "radar",
    )
def test_report():
    suite = run_default_benchmark()
    report = benchmark_report(suite)
    assert "CIDAR SENSOR BENCHMARK" in report
    assert "camera" in report
    assert "lidar" in report
    assert "radar" in report
    assert "BEST CONFIGURATION" in report
    assert "RMSE" in report
def test_custom_benchmark():
    truth = [5.0, 10.0, 20.0]
    scenarios = default_scenarios()[:2]
    suite = run_benchmark(
        truth,
        [
            type(scenarios[0])(
                name=scenarios[0].name,
                sensors=scenarios[0].sensors,
                predictions=(5.5, 10.5, 20.5),
            ),
            type(scenarios[1])(
                name=scenarios[1].name,
                sensors=scenarios[1].sensors,
                predictions=(5.1, 10.1, 20.1),
            ),
        ],
    )
    assert len(suite.records) == 2
    assert suite.best.sensors == ("lidar",)