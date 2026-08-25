"""CIDAR dataset primitives and evaluation metrics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DepthSample:
    """A single ground-truth/prediction depth sample."""

    ground_truth: float
    prediction: float
    sample_id: object = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ground_truth", float(self.ground_truth))
        object.__setattr__(self, "prediction", float(self.prediction))

    @property
    def error(self) -> float:
        return self.prediction - self.ground_truth

    @property
    def absolute_error(self) -> float:
        return abs(self.error)

    @property
    def squared_error(self) -> float:
        return self.error ** 2

    @property
    def relative_error(self) -> float:
        denominator = max(abs(self.ground_truth), 1e-12)
        return self.absolute_error / denominator


@dataclass(frozen=True)
class DepthMetrics:
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
    if len(ground_truth) != len(prediction):
        raise ValueError(
            "ground truth and prediction lengths must match"
        )

    return [
        DepthSample(
            ground_truth=gt,
            prediction=pred,
            sample_id=index,
        )
        for index, (gt, pred) in enumerate(
            zip(ground_truth, prediction)
        )
    ]


def validate_samples(
    samples: Iterable[DepthSample],
) -> list[DepthSample]:
    """Validate and return samples."""

    result = list(samples)

    if not result:
        raise ValueError("CIDAR samples cannot be empty")

    for sample in result:
        if not math.isfinite(sample.ground_truth):
            raise ValueError("ground_truth must be finite")

        if not math.isfinite(sample.prediction):
            raise ValueError("prediction must be finite")

        if sample.ground_truth < 0:
            raise ValueError(
                "ground_truth cannot be negative"
            )

        if sample.prediction < 0:
            raise ValueError(
                "prediction cannot be negative"
            )

    return result


def evaluate_dataset(
    samples: Iterable[DepthSample],
) -> DepthMetrics:
    sample_list = validate_samples(samples)

    errors = [
        sample.error
        for sample in sample_list
    ]

    mae = sum(
        abs(error)
        for error in errors
    ) / len(errors)

    rmse = math.sqrt(
        sum(
            error ** 2
            for error in errors
        ) / len(errors)
    )

    bias = sum(errors) / len(errors)

    relative_error = sum(
        sample.relative_error
        for sample in sample_list
    ) / len(sample_list)

    valid = all(
        math.isfinite(value)
        for value in (
            mae,
            rmse,
            bias,
            relative_error,
        )
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
    return evaluate_dataset(
        from_sequences(
            ground_truth,
            prediction,
        )
    )


def kitti_style_evaluate(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
) -> DepthMetrics:
    """KITTI-style range evaluation."""

    return evaluate_arrays(
        ground_truth,
        prediction,
    )


def nyu_style_evaluate(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
) -> DepthMetrics:
    """NYU-style depth evaluation."""

    return evaluate_arrays(
        ground_truth,
        prediction,
    )


def metric_report(metrics: DepthMetrics) -> str:
    status = "PASS" if metrics.valid else "FAIL"

    return (
        "CIDAR REAL-WORLD DATASET EVALUATION\n"
        "====================================\n"
        f"Status: {status}\n"
        f"Samples: {metrics.samples}\n"
        f"MAE: {metrics.mae:.6f}\n"
        f"RMSE: {metrics.rmse:.6f}\n"
        f"Bias: {metrics.bias:.6f}\n"
        f"Relative Error: {metrics.relative_error:.6f}\n"
    )


__all__ = [
    "DepthSample",
    "DepthMetrics",
    "from_sequences",
    "validate_samples",
    "evaluate_dataset",
    "evaluate_arrays",
    "kitti_style_evaluate",
    "nyu_style_evaluate",
    "metric_report",
]