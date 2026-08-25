"""CIDAR Monte Carlo and Cramér-Rao analysis."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from statistics import mean


@dataclass(frozen=True)
class MonteCarloResult:
    """Monte Carlo range-estimation result."""

    valid: bool
    samples: int
    true_distance: float
    noise_std: float
    measurements_per_trial: int
    bias: float
    rmse: float
    crlb_variance: float
    estimator_efficiency: float

    @property
    def variance(self) -> float:
        return self.rmse ** 2

    @property
    def standard_error(self) -> float:
        return math.sqrt(
            self.crlb_variance
        )


def crlb_variance(
    noise_std: float,
    measurements: int,
) -> float:
    """Calculate the CRLB variance for a Gaussian mean estimator."""

    noise_std = float(noise_std)

    if noise_std < 0:
        raise ValueError(
            "noise_std cannot be negative"
        )

    if measurements <= 0:
        raise ValueError(
            "measurements must be positive"
        )

    return (
        noise_std ** 2
        / float(measurements)
    )


def monte_carlo_range_estimation(
    true_distance: float,
    noise_std: float = 0.25,
    measurements_per_trial: int = 20,
    trials: int = 1000,
    seed: int | None = None,
) -> MonteCarloResult:
    """Estimate distance from repeated noisy measurements."""

    true_distance = float(true_distance)
    noise_std = float(noise_std)

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
            + rng.gauss(
                0.0,
                noise_std,
            )
            for _ in range(
                measurements_per_trial
            )
        ]

        estimates.append(
            mean(measurements)
        )

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

    bound = crlb_variance(
        noise_std,
        measurements_per_trial,
    )

    observed_variance = mean(
        (error - bias) ** 2
        for error in errors
    )

    if observed_variance <= 1e-15:
        efficiency = 1.0
    else:
        efficiency = (
            bound
            / observed_variance
        )

    efficiency = max(
        0.0,
        min(1.0, efficiency),
    )

    return MonteCarloResult(
        valid=all(
            math.isfinite(
                estimate
            )
            for estimate in estimates
        ),
        samples=trials,
        true_distance=true_distance,
        noise_std=noise_std,
        measurements_per_trial=measurements_per_trial,
        bias=bias,
        rmse=rmse,
        crlb_variance=bound,
        estimator_efficiency=efficiency,
    )


def monte_carlo_sweep(
    distances,
    *,
    noise_std: float = 0.25,
    measurements_per_trial: int = 20,
    trials: int = 1000,
    seed: int | None = None,
) -> list[MonteCarloResult]:
    """Run the estimator across multiple distances."""

    return [
        monte_carlo_range_estimation(
            distance,
            noise_std=noise_std,
            measurements_per_trial=measurements_per_trial,
            trials=trials,
            seed=(
                None
                if seed is None
                else seed + index
            ),
        )
        for index, distance
        in enumerate(distances)
    ]


def monte_carlo_summary(
    result: MonteCarloResult,
) -> str:
    """Format Monte Carlo results."""

    status = (
        "PASS"
        if result.valid
        else "FAIL"
    )

    return (
        "CIDAR MONTE CARLO RANGE ESTIMATION\n"
        "==================================\n"
        f"Status: {status}\n"
        f"True Distance: "
        f"{result.true_distance:.6f}\n"
        f"Trials: {result.samples}\n"
        f"Noise Std: "
        f"{result.noise_std:.6f}\n"
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