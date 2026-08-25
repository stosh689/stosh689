from gedt.cidar_monte_carlo import (
    crlb_variance,
    monte_carlo_range_estimation,
    monte_carlo_summary,
    monte_carlo_sweep,
)


def test_crlb_variance():
    assert crlb_variance(
        0.5,
        measurements=100,
    ) == 0.0025


def test_monte_carlo_result_is_valid():
    result = monte_carlo_range_estimation(
        10.0,
        noise_std=0.25,
        measurements_per_trial=20,
        trials=500,
        seed=42,
    )

    assert result.valid
    assert result.samples == 500
    assert result.true_distance == 10.0


def test_estimator_is_close_to_truth():
    result = monte_carlo_range_estimation(
        10.0,
        noise_std=0.25,
        measurements_per_trial=20,
        trials=1000,
        seed=42,
    )

    assert abs(result.bias) < 0.05
    assert result.rmse < 0.15


def test_more_measurements_reduce_crlb():
    low = crlb_variance(
        0.25,
        measurements=10,
    )

    high = crlb_variance(
        0.25,
        measurements=100,
    )

    assert high < low


def test_monte_carlo_sweep():
    results = monte_carlo_sweep(
        [1.0, 10.0, 100.0],
        trials=100,
        seed=42,
    )

    assert len(results) == 3

    for result in results:
        assert result.valid


def test_summary():
    result = monte_carlo_range_estimation(
        25.0,
        trials=100,
        seed=42,
    )

    summary = monte_carlo_summary(result)

    assert "CIDAR MONTE CARLO RANGE ESTIMATION" in summary
    assert "Status: PASS" in summary
    assert "CRLB Variance:" in summary
    assert "Efficiency:" in summary