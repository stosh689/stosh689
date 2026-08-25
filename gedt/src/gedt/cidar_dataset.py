"""CIDAR dataset primitives and depth-estimation evaluation metrics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DepthSample:
    """A single CIDAR ground-truth/prediction pair."""

    ground_truth: float
    prediction: float
    sample_id: object = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "ground_truth",
            float(self.ground_truth),
        )
        object.__setattr__(
            self,
            "prediction",
            float(self.prediction),
        )

    @property
    def error(self) -> float:
        """Signed prediction error."""
        return self.prediction - self.ground_truth

    @property
    def absolute_error(self) -> float:
        """Absolute prediction error."""
        return abs(self.error)

    @property
    def squared_error(self) -> float:
        """Squared prediction error."""
        return self.error ** 2

    @property
    def relative_error(self) -> float:
        """Absolute error relative to ground-truth depth."""
        denominator = max(
            abs(self.ground_truth),
            1e-12,
        )
        return self.absolute_error / denominator


@dataclass(frozen=True)
class DepthMetrics:
    """Aggregate CIDAR depth-estimation metrics."""

    valid: bool
    samples: int
    mae: float
    rmse: float
    bias: float
    relative_error: float

    @property
    def mean_absolute_error(self) -> float:
        return self.mae

    @property
    def root_mean_square_error(self) -> float:
        return self.rmse

    @property
    def mean_relative_error(self) -> float:
        return self.relative_error


def from_sequences(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
) -> list[DepthSample]:
    """Create samples from matching ground-truth and prediction arrays."""

    if len(ground_truth) != len(prediction):
        raise ValueError(
            "ground truth and prediction lengths must match"
        )

    return [
        DepthSample(
            ground_truth=value_gt,
            prediction=value_pred,
            sample_id=index,
        )
        for index, (value_gt, value_pred) in enumerate(
            zip(ground_truth, prediction)
        )
    ]


def evaluate_dataset(
    samples: Iterable[DepthSample],
) -> DepthMetrics:
    """Evaluate a collection of CIDAR depth samples."""

    sample_list = list(samples)

    if not sample_list:
        return DepthMetrics(
            valid=False,
            samples=0,
            mae=0.0,
            rmse=0.0,
            bias=0.0,
            relative_error=0.0,
        )

    errors = [
        sample.error
        for sample in sample_list
    ]

    valid = all(
        math.isfinite(error)
        for error in errors
    )

    mae = (
        sum(
            abs(error)
            for error in errors
        )
        / len(errors)
    )

    rmse = math.sqrt(
        sum(
            error ** 2
            for error in errors
        )
        / len(errors)
    )

    bias = (
        sum(errors)
        / len(errors)
    )

    relative_error = (
        sum(
            sample.relative_error
            for sample in sample_list
        )
        / len(sample_list)
    )

    return DepthMetrics(
        valid=valid,
        samples=len(sample_list),
        mae=mae,
        rmse=rmse,
        bias=bias,
        relative_error=relative_error,
    )


def evaluate_arrays(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
) -> DepthMetrics:
    """Evaluate matching ground-truth and prediction arrays."""

    samples = from_sequences(
        ground_truth,
        prediction,
    )

    return evaluate_dataset(samples)


def validate_samples(
    samples: Iterable[DepthSample],
) -> bool:
    """Return True when all samples contain finite depth values."""

    sample_list = list(samples)

    if not sample_list:
        return False

    return all(
        math.isfinite(sample.ground_truth)
        and math.isfinite(sample.prediction)
        for sample in sample_list
    )


def metric_report(
    metrics: DepthMetrics,
) -> str:
    """Return a human-readable CIDAR metrics report."""

    status = (
        "PASS"
        if metrics.valid
        else "FAIL"
    )

    return (
        "CIDAR DATASET EVALUATION\n"
        "=======================\n"
        f"Status: {status}\n"
        f"Samples: {metrics.samples}\n"
        f"MAE: {metrics.mae:.6f}\n"
        f"RMSE: {metrics.rmse:.6f}\n"
        f"Bias: {metrics.bias:.6f}\n"
        f"Relative Error: "
        f"{metrics.relative_error:.6f}"
    )


__all__ = [
    "DepthSample",
    "DepthMetrics",
    "from_sequences",
    "evaluate_dataset",
    "evaluate_arrays",
    "validate_samples",
    "metric_report",
]