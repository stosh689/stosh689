"""CIDAR Monte Carlo range-estimation analysis."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from statistics import mean


@dataclass(frozen=True)
class MonteCarloResult:
    valid: bool
    samples: int
    true_distance: float
    noise_std: float
    measurements_per_trial: int
    bias: float
    rmse: float
    crlb_variance: float
    estimator_efficiency: float


def crlb_variance(
    noise_std: float,
    measurements: int,
) -> float:
    """Cramér-Rao lower-bound variance for mean estimation."""

    if noise_std < 0:
        raise ValueError("noise_std cannot be negative")

    if measurements <= 0:
        raise ValueError("measurements must be positive")

    return (
        float(noise_std) ** 2
        / float(measurements)
    )


def monte_carlo_range_estimation(
    true_distance: float,
    noise_std: float = 0.25,
    measurements_per_trial: int = 20,
    trials: int = 1000,
    seed: int | None = None,
) -> MonteCarloResult:
    """Estimate range using repeated noisy measurements."""

    if true_distance < 0:
        raise ValueError(
            "true_distance cannot be negative"
        )

    if noise_std < 0:
        raise ValueError(
            "noise_std cannot be negative"
        )

    if measurements_per_trial <= 0:
        raise ValueError(
            "measurements_per_trial must be positive"
        )

    if trials <= 0:
        raise ValueError(
            "trials must be positive"
        )

    rng = random.Random(seed)

    estimates: list[float] = []

    for _ in range(trials):
        measurements = [
            true_distance
            + rng.gauss(0.0, noise_std)
            for _ in range(measurements_per_trial)
        ]

        estimates.append(mean(measurements))

    errors = [
        estimate - true_distance
        for estimate in estimates
    ]

    bias = mean(errors)

    rmse = math.sqrt(
        mean(
            error * error
            for error in errors
        )
    )

    variance_bound = crlb_variance(
        noise_std,
        measurements_per_trial,
    )

    observed_variance = mean(
        (error - bias) ** 2
        for error in errors
    )

    if observed_variance > 0:
        efficiency = (
            variance_bound
            / observed_variance
        )
    else:
        efficiency = 1.0

    efficiency = max(
        0.0,
        min(1.0, efficiency),
    )

    return MonteCarloResult(
        valid=all(
            math.isfinite(value)
            for value in estimates
        ),
        samples=trials,
        true_distance=float(true_distance),
        noise_std=float(noise_std),
        measurements_per_trial=measurements_per_trial,
        bias=float(bias),
        rmse=float(rmse),
        crlb_variance=float(variance_bound),
        estimator_efficiency=float(efficiency),
    )


def monte_carlo_sweep(
    distances,
    trials: int = 1000,
    noise_std: float = 0.25,
    measurements_per_trial: int = 20,
    seed: int | None = None,
) -> list[MonteCarloResult]:
    """Run Monte Carlo estimation over multiple distances."""

    return [
        monte_carlo_range_estimation(
            distance,
            noise_std=noise_std,
            measurements_per_trial=measurements_per_trial,
            trials=trials,
            seed=None if seed is None else seed + index,
        )
        for index, distance in enumerate(distances)
    ]


def monte_carlo_summary(
    result: MonteCarloResult,
) -> str:
    status = (
        "PASS"
        if result.valid
        else "FAIL"
    )

    return (
        "CIDAR MONTE CARLO RANGE ESTIMATION\n"
        "==================================\n"
        f"Status: {status}\n"
        f"True Distance: {result.true_distance:.6f}\n"
        f"Samples: {result.samples}\n"
        f"Noise Std: {result.noise_std:.6f}\n"
        f"Measurements/Trial: "
        f"{result.measurements_per_trial}\n"
        f"Bias: {result.bias:.6f}\n"
        f"RMSE: {result.rmse:.6f}\n"
        f"CRLB Variance: "
        f"{result.crlb_variance:.6f}\n"
        f"Efficiency: "
        f"{result.estimator_efficiency:.6f}"
    )


__all__ = [
    "MonteCarloResult",
    "crlb_variance",
    "monte_carlo_range_estimation",
    "monte_carlo_sweep",
    "monte_carlo_summary",
]