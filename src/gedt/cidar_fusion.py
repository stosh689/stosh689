"""
CIDAR sensor-fusion utilities.

Provides a dependency-free foundation for combining and comparing
camera, LiDAR, and radar range observations.

Python >= 3.10
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import mean, median
from typing import Iterable


@dataclass(frozen=True)
class RangeObservation:
    """A single range observation from a named sensor."""

    sensor: str
    distance: float
    confidence: float = 1.0
    timestamp: float | None = None

    def __post_init__(self) -> None:
        if not self.sensor.strip():
            raise ValueError("sensor must not be empty")

        if not isfinite(self.distance):
            raise ValueError("distance must be finite")

        if self.distance < 0:
            raise ValueError("distance must be non-negative")

        if not isfinite(self.confidence):
            raise ValueError("confidence must be finite")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if self.timestamp is not None:
            if not isfinite(self.timestamp):
                raise ValueError(
                    "timestamp must be finite"
                )


@dataclass(frozen=True)
class FusionResult:
    """Result of multi-sensor range fusion."""

    distance: float
    confidence: float
    observation_count: int
    sensors: tuple[str, ...]
    minimum: float
    maximum: float
    spread: float

    @property
    def valid(self) -> bool:
        return (
            self.observation_count > 0
            and isfinite(self.distance)
            and self.distance >= 0.0
        )


@dataclass(frozen=True)
class FusionError:
    """Difference between two sensor measurements."""

    reference_sensor: str
    comparison_sensor: str
    reference_distance: float
    comparison_distance: float
    absolute_error: float
    relative_error: float
    percent_error: float


def validate_observations(
    observations: Iterable[RangeObservation],
) -> tuple[RangeObservation, ...]:
    """Validate and normalize observations."""
    result = tuple(observations)

    for observation in result:
        if not isinstance(
            observation,
            RangeObservation,
        ):
            raise TypeError(
                "all observations must be RangeObservation instances"
            )

    return result


def weighted_fuse(
    observations: Iterable[RangeObservation],
) -> FusionResult:
    """
    Fuse range observations using confidence-weighted averaging.

    A confidence of zero contributes no weight.
    """
    values = validate_observations(observations)

    if not values:
        raise ValueError(
            "at least one observation is required"
        )

    weighted_values = [
        observation.distance * observation.confidence
        for observation in values
        if observation.confidence > 0.0
    ]

    weights = [
        observation.confidence
        for observation in values
        if observation.confidence > 0.0
    ]

    if not weights:
        raise ValueError(
            "at least one observation must have positive confidence"
        )

    distance = sum(weighted_values) / sum(weights)

    distances = [
        observation.distance
        for observation in values
    ]

    confidence = min(
        1.0,
        sum(weights) / len(values),
    )

    return FusionResult(
        distance=distance,
        confidence=confidence,
        observation_count=len(values),
        sensors=tuple(
            observation.sensor
            for observation in values
        ),
        minimum=min(distances),
        maximum=max(distances),
        spread=max(distances) - min(distances),
    )


def median_fuse(
    observations: Iterable[RangeObservation],
) -> FusionResult:
    """Fuse observations using the robust median estimator."""
    values = validate_observations(observations)

    if not values:
        raise ValueError(
            "at least one observation is required"
        )

    distances = [
        observation.distance
        for observation in values
    ]

    confidence = mean(
        observation.confidence
        for observation in values
    )

    return FusionResult(
        distance=median(distances),
        confidence=confidence,
        observation_count=len(values),
        sensors=tuple(
            observation.sensor
            for observation in values
        ),
        minimum=min(distances),
        maximum=max(distances),
        spread=max(distances) - min(distances),
    )


def compare_ranges(
    reference: RangeObservation,
    comparison: RangeObservation,
) -> FusionError:
    """
    Compare two sensor range measurements.

    The reference sensor is treated as the baseline.
    """
    if not isinstance(
        reference,
        RangeObservation,
    ):
        raise TypeError(
            "reference must be RangeObservation"
        )

    if not isinstance(
        comparison,
        RangeObservation,
    ):
        raise TypeError(
            "comparison must be RangeObservation"
        )

    absolute_error = abs(
        comparison.distance
        - reference.distance
    )

    if reference.distance == 0.0:
        relative_error = (
            0.0
            if comparison.distance == 0.0
            else float("inf")
        )
    else:
        relative_error = (
            absolute_error
            / abs(reference.distance)
        )

    return FusionError(
        reference_sensor=reference.sensor,
        comparison_sensor=comparison.sensor,
        reference_distance=reference.distance,
        comparison_distance=comparison.distance,
        absolute_error=absolute_error,
        relative_error=relative_error,
        percent_error=relative_error * 100.0,
    )


def sensor_bias(
    reference: Iterable[RangeObservation],
    comparison: Iterable[RangeObservation],
) -> float:
    """
    Estimate average signed bias between two sensors.

    Positive result means comparison tends to report larger ranges.
    """
    reference_values = validate_observations(
        reference
    )

    comparison_values = validate_observations(
        comparison
    )

    if len(reference_values) != len(comparison_values):
        raise ValueError(
            "sensor observation collections must have equal length"
        )

    if not reference_values:
        raise ValueError(
            "at least one observation pair is required"
        )

    differences = [
        comparison_item.distance
        - reference_item.distance
        for reference_item, comparison_item
        in zip(
            reference_values,
            comparison_values,
        )
    ]

    return mean(differences)


def root_mean_square_error(
    reference: Iterable[RangeObservation],
    comparison: Iterable[RangeObservation],
) -> float:
    """Calculate RMSE between paired sensor ranges."""
    reference_values = validate_observations(
        reference
    )

    comparison_values = validate_observations(
        comparison
    )

    if len(reference_values) != len(comparison_values):
        raise ValueError(
            "sensor observation collections must have equal length"
        )

    if not reference_values:
        raise ValueError(
            "at least one observation pair is required"
        )

    squared_errors = [
        (
            comparison_item.distance
            - reference_item.distance
        ) ** 2
        for reference_item, comparison_item
        in zip(
            reference_values,
            comparison_values,
        )
    ]

    return (
        sum(squared_errors)
        / len(squared_errors)
    ) ** 0.5


def consistency_score(
    observations: Iterable[RangeObservation],
) -> float:
    """
    Calculate a 0-1 consistency score.

    Lower spread relative to the fused distance produces a higher score.
    """
    result = weighted_fuse(observations)

    if result.distance == 0.0:
        return 1.0 if result.spread == 0.0 else 0.0

    relative_spread = (
        result.spread
        / abs(result.distance)
    )

    return max(
        0.0,
        min(
            1.0,
            1.0 / (1.0 + relative_spread),
        ),
    )


def fuse_camera_lidar_radar(
    *,
    camera: RangeObservation | None = None,
    lidar: RangeObservation | None = None,
    radar: RangeObservation | None = None,
) -> FusionResult:
    """
    Convenience fusion entry point for the three primary CIDAR
    sensor modalities.
    """
    observations = tuple(
        observation
        for observation in (
            camera,
            lidar,
            radar,
        )
        if observation is not None
    )

    if not observations:
        raise ValueError(
            "at least one sensor observation is required"
        )

    return weighted_fuse(observations)


__all__ = [
    "FusionError",
    "FusionResult",
    "RangeObservation",
    "compare_ranges",
    "consistency_score",
    "fuse_camera_lidar_radar",
    "median_fuse",
    "root_mean_square_error",
    "sensor_bias",
    "validate_observations",
    "weighted_fuse",
]