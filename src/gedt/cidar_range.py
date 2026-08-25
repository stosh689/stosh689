"""
CIDAR range and depth estimation utilities.

Dependency-free numerical foundation for converting depth samples
into physical range estimates.

Supports:
- scalar depth measurements
- depth maps represented as nested sequences
- point-cloud Euclidean range
- robust statistics
- confidence estimation
- outlier rejection

Python >= 3.10
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt, isfinite
from statistics import median
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RangeEstimate:
    """Result of a range estimation operation."""

    distance: float
    sample_count: int
    confidence: float
    minimum: float
    maximum: float
    median: float

    @property
    def valid(self) -> bool:
        return (
            isfinite(self.distance)
            and self.distance >= 0.0
            and self.sample_count > 0
        )


def euclidean_range(
    x: float,
    y: float,
    z: float,
) -> float:
    """Calculate Euclidean range from a 3D point."""
    values = (float(x), float(y), float(z))

    if not all(isfinite(value) for value in values):
        raise ValueError("point coordinates must be finite")

    return sqrt(
        x * x
        + y * y
        + z * z
    )


def filter_depth_values(
    values: Iterable[float],
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> list[float]:
    """
    Normalize and filter depth values.

    Non-finite values are discarded.
    Values outside the requested range are discarded.
    """
    minimum = float(minimum)

    if not isfinite(minimum):
        raise ValueError("minimum must be finite")

    if maximum is not None:
        maximum = float(maximum)

        if not isfinite(maximum):
            raise ValueError("maximum must be finite")

        if maximum < minimum:
            raise ValueError(
                "maximum must be greater than or equal to minimum"
            )

    result: list[float] = []

    for value in values:
        value = float(value)

        if not isfinite(value):
            continue

        if value < minimum:
            continue

        if maximum is not None and value > maximum:
            continue

        result.append(value)

    return result


def reject_outliers(
    values: Sequence[float],
    *,
    threshold: float = 3.0,
) -> list[float]:
    """
    Reject robust median-based outliers.

    Uses median absolute deviation (MAD), which is substantially
    less sensitive to extreme values than mean/std filtering.
    """
    if not values:
        return []

    threshold = float(threshold)

    if not isfinite(threshold) or threshold <= 0:
        raise ValueError(
            "threshold must be a positive finite number"
        )

    center = median(values)

    deviations = [
        abs(value - center)
        for value in values
    ]

    mad = median(deviations)

    # All values are effectively identical.
    if mad == 0:
        return list(values)

    scale = 1.4826 * mad

    return [
        value
        for value in values
        if abs(value - center) <= threshold * scale
    ]


def confidence_score(
    values: Sequence[float],
) -> float:
    """
    Estimate confidence from sample count and dispersion.

    Returns a value between 0 and 1.
    """
    if not values:
        return 0.0

    if len(values) == 1:
        return 0.5

    center = median(values)

    deviations = [
        abs(value - center)
        for value in values
    ]

    spread = median(deviations)

    if center == 0:
        return 1.0 if spread == 0 else 0.0

    relative_spread = spread / abs(center)

    dispersion_score = 1.0 / (
        1.0 + relative_spread
    )

    sample_score = min(
        1.0,
        len(values) / 32.0,
    )

    return max(
        0.0,
        min(
            1.0,
            0.5 * dispersion_score
            + 0.5 * sample_score,
        ),
    )


def estimate_range(
    values: Iterable[float],
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
    reject: bool = True,
    outlier_threshold: float = 3.0,
) -> RangeEstimate:
    """
    Estimate physical range from depth samples.

    The median is used as the primary robust estimator.
    """
    filtered = filter_depth_values(
        values,
        minimum=minimum,
        maximum=maximum,
    )

    if reject:
        filtered = reject_outliers(
            filtered,
            threshold=outlier_threshold,
        )

    if not filtered:
        raise ValueError(
            "no valid depth samples available"
        )

    center = median(filtered)

    return RangeEstimate(
        distance=center,
        sample_count=len(filtered),
        confidence=confidence_score(filtered),
        minimum=min(filtered),
        maximum=max(filtered),
        median=center,
    )


def flatten_depth_map(
    depth_map: Iterable[Iterable[float]],
) -> list[float]:
    """Flatten a nested depth map into a one-dimensional list."""
    result: list[float] = []

    for row in depth_map:
        for value in row:
            result.append(float(value))

    return result


def estimate_depth_map_range(
    depth_map: Iterable[Iterable[float]],
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
    reject: bool = True,
) -> RangeEstimate:
    """Estimate scene range from a depth map."""
    values = flatten_depth_map(depth_map)

    return estimate_range(
        values,
        minimum=minimum,
        maximum=maximum,
        reject=reject,
    )


def estimate_point_cloud_range(
    points: Iterable[tuple[float, float, float]],
    *,
    reject: bool = True,
) -> RangeEstimate:
    """
    Estimate range from a collection of 3D points.

    Each point is interpreted in the same physical coordinate system.
    """
    distances = [
        euclidean_range(x, y, z)
        for x, y, z in points
    ]

    return estimate_range(
        distances,
        minimum=0.0,
        reject=reject,
    )


__all__ = [
    "RangeEstimate",
    "confidence_score",
    "estimate_depth_map_range",
    "estimate_point_cloud_range",
    "estimate_range",
    "euclidean_range",
    "filter_depth_values",
    "flatten_depth_map",
    "reject_outliers",
]