from gedt.cidar_dataset import (
    DepthSample,
    evaluate_arrays,
    evaluate_dataset,
    from_sequences,
    kitti_style_evaluate,
    metric_report,
    nyu_style_evaluate,
)


def test_depth_sample():
    sample = DepthSample(
        ground_truth=10.0,
        prediction=10.5,
        sample_id="frame-001",
    )

    assert sample.ground_truth == 10.0
    assert sample.prediction == 10.5
    assert sample.sample_id == "frame-001"


def test_from_sequences():
    samples = from_sequences(
        [1.0, 2.0, 3.0],
        [1.1, 1.9, 3.2],
    )

    assert len(samples) == 3
    assert samples[0].sample_id == 0


def test_evaluate_dataset():
    samples = [
        DepthSample(10.0, 11.0),
        DepthSample(20.0, 19.0),
        DepthSample(30.0, 31.0),
    ]

    metrics = evaluate_dataset(samples)

    assert metrics.valid
    assert metrics.samples == 3
    assert metrics.mae > 0.0
    assert metrics.rmse > 0.0


def test_perfect_prediction():
    metrics = evaluate_arrays(
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
    )

    assert metrics.mae == 0.0
    assert metrics.rmse == 0.0
    assert metrics.bias == 0.0


def test_kitti_style_adapter():
    metrics = kitti_style_evaluate(
        [5.0, 10.0, 20.0],
        [5.1, 9.9, 20.2],
    )

    assert metrics.valid
    assert metrics.samples == 3


def test_nyu_style_adapter():
    metrics = nyu_style_evaluate(
        [1.0, 2.0, 4.0],
        [1.1, 1.9, 4.1],
    )

    assert metrics.valid
    assert metrics.samples == 3


def test_metric_report():
    metrics = evaluate_arrays(
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
    )

    report = metric_report(metrics)

    assert "CIDAR REAL-WORLD DATASET EVALUATION" in report
    assert "Status: PASS" in report
    assert "RMSE:" in report