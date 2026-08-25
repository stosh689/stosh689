"""
CIDAR Monte Carlo range-estimation benchmark.

Provides reproducible statistical experiments for comparing
range estimators against a theoretical Cramér-Rao-style bound.

This module intentionally uses only Python's standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
import random
from statistics import mean, stdev


@dataclass(frozen=True)
class MonteCarloResult:
    """Statistical result for a range estimator."""

    true_distance: float
    samples: int
    mean_estimate: float
    bias: float
    variance: float
    standard_deviation: float
    rmse: float
    confidence_low: float
    confidence_high: float
    crlb_variance: float
    efficiency: float

    @property
    def unbiased(self) -> bool:
        """Return whether estimated bias is effectively negligible."""
        tolerance = max(
            1e-9,
            abs(self.true_distance) * 0.01,
        )
        return abs(self.bias) <= tolerance

    @property
    def valid(self) -> bool:
        """Return whether the statistical result is valid."""
        return (
            self.samples >= 2
            and self.true_distance >= 0.0
            and self.variance >= 0.0
            and self.standard_deviation >= 0.0
            and self.rmse >= 0.0
            and self.confidence_low <= self.confidence_high
            and self.crlb_variance > 0.0
            and self.efficiency >= 0.0
        )


def crlb_variance(
    noise_std: float,
    *,
    measurements: int = 1,
) -> float:
    """
    Calculate the variance lower bound for estimating
    the mean of Gaussian range measurements.

    CRLB = sigma^2 / N
    """
    if noise_std <= 0.0:
        raise ValueError(
            "noise_std must be greater than zero"
        )

    if measurements < 1:
        raise ValueError(
            "measurements must be at least one"
        )

    return (
        noise_std ** 2
        / measurements
    )


def _confidence_interval(
    estimates: list[float],
) -> tuple[float, float]:
    """Calculate an approximate 95% confidence interval."""
    if len(estimates) < 2:
        raise ValueError(
            "at least two estimates are required"
        )

    average = mean(estimates)
    standard_error = stdev(estimates) / sqrt(
        len(estimates)
    )

    margin = 1.96 * standard_error

    return (
        average - margin,
        average + margin,
    )


def monte_carlo_range_estimation(
    true_distance: float,
    *,
    noise_std: float = 0.25,
    measurements_per_trial: int = 20,
    trials: int = 1000,
    seed: int = 42,
) -> MonteCarloResult:
    """
    Run a Monte Carlo experiment using a sample-mean estimator.

    Each trial generates independent Gaussian measurements
    around the true distance and estimates range using their mean.
    """
    if true_distance < 0.0:
        raise ValueError(
            "true_distance must be non-negative"
        )

    if noise_std <= 0.0:
        raise ValueError(
            "noise_std must be greater than zero"
        )

    if measurements_per_trial < 2:
        raise ValueError(
            "measurements_per_trial must be at least two"
        )

    if trials < 2:
        raise ValueError(
            "trials must be at least two"
        )

    rng = random.Random(seed)

    estimates: list[float] = []

    for _ in range(trials):
        measurements = [
            true_distance
            + rng.gauss(0.0, noise_std)
            for _ in range(measurements_per_trial)
        ]

        estimate = mean(measurements)
        estimates.append(estimate)

    mean_estimate = mean(estimates)
    bias = mean_estimate - true_distance

    variance = sum(
        (estimate - mean_estimate) ** 2
        for estimate in estimates
    ) / (len(estimates) - 1)

    standard_deviation = sqrt(variance)

    rmse = sqrt(
        mean(
            (estimate - true_distance) ** 2
            for estimate in estimates
        )
    )

    confidence_low, confidence_high = (
        _confidence_interval(estimates)
    )

    theoretical_variance = crlb_variance(
        noise_std,
        measurements=measurements_per_trial,
    )

    efficiency = (
        theoretical_variance / variance
        if variance > 0.0
        else 0.0
    )

    return MonteCarloResult(
        true_distance=true_distance,
        samples=trials,
        mean_estimate=mean_estimate,
        bias=bias,
        variance=variance,
        standard_deviation=standard_deviation,
        rmse=rmse,
        confidence_low=confidence_low,
        confidence_high=confidence_high,
        crlb_variance=theoretical_variance,
        efficiency=efficiency,
    )


def monte_carlo_sweep(
    distances: list[float],
    *,
    noise_std: float = 0.25,
    measurements_per_trial: int = 20,
    trials: int = 1000,
    seed: int = 42,
) -> list[MonteCarloResult]:
    """Run Monte Carlo experiments across multiple ranges."""
    results: list[MonteCarloResult] = []

    for index, distance in enumerate(distances):
        results.append(
            monte_carlo_range_estimation(
                distance,
                noise_std=noise_std,
                measurements_per_trial=measurements_per_trial,
                trials=trials,
                seed=seed + index,
            )
        )

    return results


def monte_carlo_summary(
    result: MonteCarloResult,
) -> str:
    """Format a statistical experiment result."""
    status = (
        "PASS"
        if result.valid
        else "FAIL"
    )

    return (
        "CIDAR MONTE CARLO RANGE ESTIMATION\n"
        "==================================\n"
        f"Status: {status}\n"
        f"True Distance: {result.true_distance:.4f} m\n"
        f"Trials: {result.samples}\n"
        f"Mean Estimate: {result.mean_estimate:.6f} m\n"
        f"Bias: {result.bias:.6f} m\n"
        f"Variance: {result.variance:.8f} m²\n"
        f"Std Dev: {result.standard_deviation:.6f} m\n"
        f"RMSE: {result.rmse:.6f} m\n"
        f"95% CI: "
        f"[{result.confidence_low:.6f}, "
        f"{result.confidence_high:.6f}]\n"
        f"CRLB Variance: "
        f"{result.crlb_variance:.8f} m²\n"
        f"Efficiency: {result.efficiency:.4f}"
    )


__all__ = [
    "MonteCarloResult",
    "crlb_variance",
    "monte_carlo_range_estimation",
    "monte_carlo_summary",
    "monte_carlo_sweep",
]