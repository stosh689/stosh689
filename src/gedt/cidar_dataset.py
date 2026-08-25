"""
CIDAR real-world dataset adapter.

Provides a dependency-free interface for evaluating predicted
depth/range values against real-world ground-truth measurements.

The adapter accepts ordinary Python sequences so that KITTI,
NYU Depth V2, and future datasets can be connected without
making the core CIDAR package depend on a specific dataset SDK.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from statistics import mean, median
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DepthSample:
    """A single predicted/ground-truth depth observation."""

    ground_truth: float
    prediction: float
    sample_id: str | int | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.ground_truth):
            raise ValueError(
                "ground_truth must be finite"
            )

        if not isfinite(self.prediction):
            raise ValueError(
                "prediction must be finite"
            )

        if self.ground_truth < 0.0:
            raise ValueError(
                "ground_truth must be non-negative"
            )

        if self.prediction < 0.0:
            raise ValueError(
                "prediction must be non-negative"
            )


@dataclass(frozen=True)
class DatasetMetrics:
    """Standard CIDAR depth/range evaluation metrics."""

    samples: int
    mae: float
    rmse: float
    bias: float
    median_absolute_error: float
    relative_error: float
    max_error: float

    @property
    def valid(self) -> bool:
        return (
            self.samples > 0
            and self.mae >= 0.0
            and self.rmse >= 0.0
            and self.median_absolute_error >= 0.0
            and self.relative_error >= 0.0
            and self.max_error >= 0.0
            and isfinite(self.bias)
        )


def validate_samples(
    samples: Iterable[DepthSample],
) -> tuple[DepthSample, ...]:
    """Validate and normalize dataset samples."""
    result = tuple(samples)

    for sample in result:
        if not isinstance(sample, DepthSample):
            raise TypeError(
                "all samples must be DepthSample instances"
            )

    if not result:
        raise ValueError(
            "dataset must contain at least one sample"
        )

    return result


def from_sequences(
    ground_truth: Sequence[float],
    predictions: Sequence[float],
    *,
    sample_ids: Sequence[str | int] | None = None,
) -> list[DepthSample]:
    """
    Build DepthSample objects from paired sequences.

    This is the primary bridge for NumPy arrays, CSV readers,
    dataset loaders, or other external data sources.
    """
    if len(ground_truth) != len(predictions):
        raise ValueError(
            "ground_truth and predictions must have equal length"
        )

    if sample_ids is not None:
        if len(sample_ids) != len(ground_truth):
            raise ValueError(
                "sample_ids must match the number of samples"
            )

    samples: list[DepthSample] = []

    for index, (truth, prediction) in enumerate(
        zip(ground_truth, predictions)
    ):
        sample_id = (
            sample_ids[index]
            if sample_ids is not None
            else index
        )

        samples.append(
            DepthSample(
                ground_truth=float(truth),
                prediction=float(prediction),
                sample_id=sample_id,
            )
        )

    return samples


def evaluate_dataset(
    samples: Iterable[DepthSample],
) -> DatasetMetrics:
    """Evaluate predictions against ground truth."""
    values = validate_samples(samples)

    errors = [
        sample.prediction - sample.ground_truth
        for sample in values
    ]

    absolute_errors = [
        abs(error)
        for error in errors
    ]

    squared_errors = [
        error ** 2
        for error in errors
    ]

    relative_errors = [
        abs(sample.prediction - sample.ground_truth)
        / sample.ground_truth
        for sample in values
        if sample.ground_truth > 0.0
    ]

    mae = mean(absolute_errors)

    rmse = sqrt(
        mean(squared_errors)
    )

    bias = mean(errors)

    median_absolute_error = median(
        absolute_errors
    )

    relative_error = (
        mean(relative_errors)
        if relative_errors
        else 0.0
    )

    return DatasetMetrics(
        samples=len(values),
        mae=mae,
        rmse=rmse,
        bias=bias,
        median_absolute_error=median_absolute_error,
        relative_error=relative_error,
        max_error=max(absolute_errors),
    )


def evaluate_arrays(
    ground_truth: Sequence[float],
    predictions: Sequence[float],
) -> DatasetMetrics:
    """Evaluate two paired numeric sequences."""
    return evaluate_dataset(
        from_sequences(
            ground_truth,
            predictions,
        )
    )


def kitti_style_evaluate(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
) -> DatasetMetrics:
    """
    Evaluate KITTI-style sparse depth/range samples.

    Dataset-specific loading is intentionally outside this
    function; callers provide paired valid measurements.
    """
    return evaluate_arrays(
        ground_truth,
        prediction,
    )


def nyu_style_evaluate(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
) -> DatasetMetrics:
    """
    Evaluate NYU-style dense depth samples.

    Dataset-specific loading is intentionally outside this
    function; callers provide paired valid measurements.
    """
    return evaluate_arrays(
        ground_truth,
        prediction,
    )


def metric_report(
    metrics: DatasetMetrics,
) -> str:
    """Generate a human-readable CIDAR dataset report."""
    status = (
        "PASS"
        if metrics.valid
        else "FAIL"
    )

    return (
        "CIDAR REAL-WORLD DATASET EVALUATION\n"
        "====================================\n"
        f"Status: {status}\n"
        f"Samples: {metrics.samples}\n"
        f"MAE: {metrics.mae:.6f} m\n"
        f"RMSE: {metrics.rmse:.6f} m\n"
        f"Bias: {metrics.bias:.6f} m\n"
        f"Median Absolute Error: "
        f"{metrics.median_absolute_error:.6f} m\n"
        f"Relative Error: "
        f"{metrics.relative_error:.6f}\n"
        f"Maximum Error: "
        f"{metrics.max_error:.6f} m"
    )


__all__ = [
    "DatasetMetrics",
    "DepthSample",
    "evaluate_arrays",
    "evaluate_dataset",
    "from_sequences",
    "kitti_style_evaluate",
    "metric_report",
    "nyu_style_evaluate",
    "validate_samples",
]