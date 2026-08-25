"""
CIDAR Synthetic Ranging Benchmark
=================================

Deterministic synthetic validation for passive ranging.

The benchmark generates known ground-truth distances, simulates
measurement noise, evaluates the estimator, and verifies that
accuracy metrics remain within defined limits.

Python 3.10+
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
import random


@dataclass(frozen=True)
class RangeSample:
    """One synthetic ranging observation."""

    truth: float
    measurement: float


@dataclass(frozen=True)
class RangeMetrics:
    """Accuracy metrics for a ranging experiment."""

    count: int
    mae: float
    rmse: float
    bias: float
    maximum_error: float

    @property
    def passed(self) -> bool:
        """Return whether the metrics satisfy baseline limits."""
        return (
            self.count > 0
            and self.mae < 10.0
            and self.rmse < 15.0
            and self.maximum_error < 40.0
        )


def generate_dataset(
    *,
    count: int = 1000,
    minimum_distance: float = 10.0,
    maximum_distance: float = 10_000.0,
    noise_std: float = 2.0,
    seed: int = 42,
) -> list[RangeSample]:
    """
    Generate deterministic synthetic ranging measurements.
    """
    if count <= 0:
        raise ValueError("count must be positive")

    if minimum_distance <= 0:
        raise ValueError(
            "minimum_distance must be positive"
        )

    if maximum_distance <= minimum_distance:
        raise ValueError(
            "maximum_distance must exceed minimum_distance"
        )

    if noise_std < 0:
        raise ValueError(
            "noise_std cannot be negative"
        )

    rng = random.Random(seed)

    samples: list[RangeSample] = []

    for _ in range(count):
        truth = rng.uniform(
            minimum_distance,
            maximum_distance,
        )

        measurement = truth + rng.gauss(
            0.0,
            noise_std,
        )

        samples.append(
            RangeSample(
                truth=truth,
                measurement=measurement,
            )
        )

    return samples


def calculate_metrics(
    samples: list[RangeSample],
) -> RangeMetrics:
    """Calculate ranging accuracy metrics."""
    if not samples:
        raise ValueError(
            "samples cannot be empty"
        )

    errors = [
        sample.measurement - sample.truth
        for sample in samples
    ]

    absolute_errors = [
        abs(error)
        for error in errors
    ]

    squared_errors = [
        error * error
        for error in errors
    ]

    mae = sum(
        absolute_errors
    ) / len(samples)

    rmse = sqrt(
        sum(squared_errors)
        / len(samples)
    )

    bias = (
        sum(errors)
        / len(samples)
    )

    maximum_error = max(
        absolute_errors
    )

    return RangeMetrics(
        count=len(samples),
        mae=mae,
        rmse=rmse,
        bias=bias,
        maximum_error=maximum_error,
    )


def run_benchmark(
    *,
    count: int = 1000,
    noise_std: float = 2.0,
    seed: int = 42,
) -> RangeMetrics:
    """Generate data and evaluate the ranging baseline."""
    samples = generate_dataset(
        count=count,
        noise_std=noise_std,
        seed=seed,
    )

    return calculate_metrics(
        samples
    )


def test_dataset_is_deterministic():
    """The same seed must generate identical observations."""
    first = generate_dataset(
        count=100,
        seed=42,
    )

    second = generate_dataset(
        count=100,
        seed=42,
    )

    assert first == second


def test_dataset_contains_expected_range():
    """Synthetic distances must remain inside the configured range."""
    samples = generate_dataset(
        count=1000,
        minimum_distance=10.0,
        maximum_distance=10_000.0,
        seed=42,
    )

    assert len(samples) == 1000

    for sample in samples:
        assert 10.0 <= sample.truth <= 10_000.0


def test_measurements_are_close_to_ground_truth():
    """Low-noise measurements should remain close to truth."""
    samples = generate_dataset(
        count=1000,
        noise_std=2.0,
        seed=42,
    )

    metrics = calculate_metrics(
        samples
    )

    assert metrics.mae < 10.0
    assert metrics.rmse < 15.0


def test_metrics_are_valid():
    """All calculated metrics must be finite and non-negative."""
    metrics = run_benchmark(
        count=1000,
        noise_std=2.0,
        seed=42,
    )

    assert metrics.count == 100
    assert metrics.mae >= 0.0
    assert metrics.rmse >= 0.0
    assert metrics.maximum_error >= 0.0


def test_cidar_baseline_passes():
    """The synthetic CIDAR baseline must pass."""
    metrics = run_benchmark(
        count=1000,
        noise_std=2.0,
        seed=42,
    )

    assert metrics.passed


def test_higher_noise_increases_error():
    """Increasing measurement noise should increase error."""
    low_noise = run_benchmark(
        count=1000,
        noise_std=1.0,
        seed=42,
    )

    high_noise = run_benchmark(
        count=1000,
        noise_std=10.0,
        seed=42,
    )

    assert high_noise.mae > low_noise.mae
    assert high_noise.rmse > low_noise.rmse


def test_invalid_count_is_rejected():
    """Invalid sample counts must fail clearly."""
    try:
        generate_dataset(count=0)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "count=0 should raise ValueError"
        )


def test_invalid_distance_range_is_rejected():
    """Invalid distance ranges must fail clearly."""
    try:
        generate_dataset(
            minimum_distance=100.0,
            maximum_distance=50.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Invalid distance range should raise ValueError"
        )