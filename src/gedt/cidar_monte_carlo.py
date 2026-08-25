"""Monte Carlo range-estimation experiments."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Sequence


def crlb_variance(
    noise_std: float,
    measurements: int,
) -> float:
    if noise_std <= 0:
        raise ValueError(
            "noise_std must be positive"
        )

    if measurements <= 0:
        raise ValueError(
            "measurements must be positive"
        )

    return (
        noise_std ** 2
        / measurements
    )


@dataclass(frozen=True)
class MonteCarloResult:
    true_distance: float
    noise_std: float
    measurements_per_trial: int
    trials: int
    seed: int | None
    estimate: float
    bias: float
    rmse: float
    variance: float
    crlb_variance: float
    efficiency: float
    valid: bool
    samples: int


def monte_carlo_range_estimation(
    true_distance: float,
    noise_std: float = 0.25,
    measurements_per_trial: int = 20,
    trials: int = 500,
    seed: int | None = 42,
) -> MonteCarloResult:
    if true_distance < 0:
        raise ValueError(
            "true_distance cannot be negative"
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
            sum(measurements)
            / len(measurements)
        )

    estimate = (
        sum(estimates)
        / len(estimates)
    )

    bias = (
        estimate
        - true_distance
    )

    variance = (
        sum(
            (
                value - estimate
            ) ** 2
            for value in estimates
        )
        / len(estimates)
    )

    rmse = math.sqrt(
        sum(
            (
                value
                - true_distance
            ) ** 2
            for value in estimates
        )
        / len(estimates)
    )

    bound = crlb_variance(
        noise_std,
        measurements_per_trial,
    )

    efficiency = (
        bound / variance
        if variance > 0
        else 1.0
    )

    efficiency = min(
        1.0,
        max(0.0, efficiency),
    )

    return MonteCarloResult(
        true_distance=float(true_distance),
        noise_std=float(noise_std),
        measurements_per_trial=int(
            measurements_per_trial
        ),
        trials=int(trials),
        seed=seed,
        estimate=estimate,
        bias=bias,
        rmse=rmse,
        variance=variance,
        crlb_variance=bound,
        efficiency=efficiency,
        valid=(
            math.isfinite(estimate)
            and math.isfinite(bias)
            and math.isfinite(rmse)
            and math.isfinite(variance)
        ),
        samples=trials,
    )


def monte_carlo_sweep(
    distances: Sequence[float],
    *,
    noise_std: float = 0.25,
    measurements_per_trial: int = 20,
    trials: int = 500,
    seed: int | None = 42,
) -> list[MonteCarloResult]:
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
        for index, distance in enumerate(
            distances
        )
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
        f"True Distance: "
        f"{result.true_distance:.6f}\n"
        f"Estimate: "
        f"{result.estimate:.6f}\n"
        f"Bias: {result.bias:.6f}\n"
        f"RMSE: {result.rmse:.6f}\n"
        f"Variance: {result.variance:.6f}\n"
        f"CRLB Variance: "
        f"{result.crlb_variance:.6f}\n"
        f"Efficiency: "
        f"{result.efficiency:.6f}\n"
        f"Trials: {result.trials}\n"
    )


__all__ = [
    "MonteCarloResult",
    "crlb_variance",
    "monte_carlo_range_estimation",
    "monte_carlo_sweep",
    "monte_carlo_summary",
]