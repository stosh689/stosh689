"""
CIDAR synthetic range benchmark.

Generates controlled sensor measurements and evaluates
camera/LiDAR/radar fusion without external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
import random

from .cidar_fusion import (
    RangeObservation,
    compare_ranges,
    fuse_camera_lidar_radar,
    root_mean_square_error,
)


@dataclass(frozen=True)
class BenchmarkCase:
    """One synthetic CIDAR measurement case."""

    true_distance: float
    camera: RangeObservation
    lidar: RangeObservation
    radar: RangeObservation


@dataclass(frozen=True)
class BenchmarkResult:
    """Aggregate benchmark results."""

    cases: int
    rmse: float
    mean_absolute_error: float
    maximum_absolute_error: float
    mean_fused_confidence: float

    @property
    def valid(self) -> bool:
        return (
            self.cases > 0
            and self.rmse >= 0.0
            and self.mean_absolute_error >= 0.0
            and self.maximum_absolute_error >= 0.0
            and 0.0 <= self.mean_fused_confidence <= 1.0
        )


def _validate_distance(distance: float) -> None:
    if distance < 0.0:
        raise ValueError(
            "distance must be non-negative"
        )


def _measurement(
    sensor: str,
    true_distance: float,
    noise: float,
    confidence: float,
    rng: random.Random,
) -> RangeObservation:
    distance = max(
        0.0,
        true_distance
        + rng.gauss(0.0, noise),
    )

    return RangeObservation(
        sensor=sensor,
        distance=distance,
        confidence=confidence,
    )


def generate_case(
    true_distance: float,
    *,
    camera_noise: float = 0.25,
    lidar_noise: float = 0.05,
    radar_noise: float = 0.15,
    camera_confidence: float = 0.75,
    lidar_confidence: float = 0.95,
    radar_confidence: float = 0.85,
    seed: int | None = None,
) -> BenchmarkCase:
    """
    Generate one synthetic camera/LiDAR/radar measurement.
    """
    _validate_distance(true_distance)

    if camera_noise < 0:
        raise ValueError("camera_noise must be non-negative")

    if lidar_noise < 0:
        raise ValueError("lidar_noise must be non-negative")

    if radar_noise < 0:
        raise ValueError("radar_noise must be non-negative")

    rng = random.Random(seed)

    return BenchmarkCase(
        true_distance=true_distance,
        camera=_measurement(
            "camera",
            true_distance,
            camera_noise,
            camera_confidence,
            rng,
        ),
        lidar=_measurement(
            "lidar",
            true_distance,
            lidar_noise,
            lidar_confidence,
            rng,
        ),
        radar=_measurement(
            "radar",
            true_distance,
            radar_noise,
            radar_confidence,
            rng,
        ),
    )


def generate_dataset(
    distances: list[float],
    *,
    camera_noise: float = 0.25,
    lidar_noise: float = 0.05,
    radar_noise: float = 0.15,
    camera_confidence: float = 0.75,
    lidar_confidence: float = 0.95,
    radar_confidence: float = 0.85,
    seed: int = 42,
) -> list[BenchmarkCase]:
    """Generate a reproducible synthetic benchmark dataset."""
    rng = random.Random(seed)

    cases: list[BenchmarkCase] = []

    for distance in distances:
        _validate_distance(distance)

        cases.append(
            BenchmarkCase(
                true_distance=distance,
                camera=_measurement(
                    "camera",
                    distance,
                    camera_noise,
                    camera_confidence,
                    rng,
                ),
                lidar=_measurement(
                    "lidar",
                    distance,
                    lidar_noise,
                    lidar_confidence,
                    rng,
                ),
                radar=_measurement(
                    "radar",
                    distance,
                    radar_noise,
                    radar_confidence,
                    rng,
                ),
            )
        )

    return cases


def run_benchmark(
    cases: list[BenchmarkCase],
) -> BenchmarkResult:
    """Evaluate fused range against ground truth."""
    if not cases:
        raise ValueError(
            "at least one benchmark case is required"
        )

    squared_errors: list[float] = []
    absolute_errors: list[float] = []
    confidences: list[float] = []

    for case in cases:
        fused = fuse_camera_lidar_radar(
            camera=case.camera,
            lidar=case.lidar,
            radar=case.radar,
        )

        error = fused.distance - case.true_distance

        squared_errors.append(error ** 2)
        absolute_errors.append(abs(error))
        confidences.append(fused.confidence)

    rmse = sqrt(
        sum(squared_errors)
        / len(squared_errors)
    )

    return BenchmarkResult(
        cases=len(cases),
        rmse=rmse,
        mean_absolute_error=(
            sum(absolute_errors)
            / len(absolute_errors)
        ),
        maximum_absolute_error=max(
            absolute_errors
        ),
        mean_fused_confidence=(
            sum(confidences)
            / len(confidences)
        ),
    )


def sensor_rmse(
    cases: list[BenchmarkCase],
    sensor: str,
) -> float:
    """Calculate RMSE for one sensor."""
    if not cases:
        raise ValueError(
            "at least one benchmark case is required"
        )

    observations: list[RangeObservation] = []

    for case in cases:
        if sensor == "camera":
            observations.append(case.camera)
        elif sensor == "lidar":
            observations.append(case.lidar)
        elif sensor == "radar":
            observations.append(case.radar)
        else:
            raise ValueError(
                f"unknown sensor: {sensor}"
            )

    truth = [
        RangeObservation(
            sensor="ground_truth",
            distance=case.true_distance,
            confidence=1.0,
        )
        for case in cases
    ]

    return root_mean_square_error(
        truth,
        observations,
    )


def benchmark_summary(
    result: BenchmarkResult,
) -> str:
    """Create a human-readable benchmark report."""
    status = (
        "PASS"
        if result.valid
        else "FAIL"
    )

    return (
        "CIDAR SYNTHETIC BENCHMARK\n"
        "=========================\n"
        f"Status: {status}\n"
        f"Cases: {result.cases}\n"
        f"RMSE: {result.rmse:.6f} m\n"
        f"MAE: {result.mean_absolute_error:.6f} m\n"
        f"Max Error: "
        f"{result.maximum_absolute_error:.6f} m\n"
        f"Mean Confidence: "
        f"{result.mean_fused_confidence:.4f}"
    )


__all__ = [
    "BenchmarkCase",
    "BenchmarkResult",
    "benchmark_summary",
    "generate_case",
    "generate_dataset",
    "run_benchmark",
    "sensor_rmse",
]