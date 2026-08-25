"""CIDAR adapters for converting common sensor data formats."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .cidar_dataset import DepthSample


@dataclass(frozen=True)
class SensorReading:
    """A single sensor reading."""

    sensor: str
    value: float
    timestamp: float | None = None
    sample_id: Any = None


def _number(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc

    return result


def camera_adapter(
    prediction: float,
    *,
    sample_id: Any = None,
) -> DepthSample:
    """Adapt a camera depth prediction."""

    return DepthSample(
        ground_truth=0.0,
        prediction=_number(prediction, "prediction"),
        sample_id=sample_id,
    )


def lidar_adapter(
    prediction: float,
    *,
    sample_id: Any = None,
) -> DepthSample:
    """Adapt a LiDAR depth prediction."""

    return DepthSample(
        ground_truth=0.0,
        prediction=_number(prediction, "prediction"),
        sample_id=sample_id,
    )


def radar_adapter(
    prediction: float,
    *,
    sample_id: Any = None,
) -> DepthSample:
    """Adapt a radar range prediction."""

    return DepthSample(
        ground_truth=0.0,
        prediction=_number(prediction, "prediction"),
        sample_id=sample_id,
    )


def mapping_to_sample(
    record: Mapping[str, Any],
    index: int = 0,
) -> DepthSample:
    """Convert a mapping into a DepthSample."""

    if "ground_truth" not in record:
        raise ValueError("missing ground_truth")

    if "prediction" not in record:
        raise ValueError("missing prediction")

    return DepthSample(
        ground_truth=_number(
            record["ground_truth"],
            "ground_truth",
        ),
        prediction=_number(
            record["prediction"],
            "prediction",
        ),
        sample_id=record.get("sample_id", index),
    )


def adapt_samples(
    records: Iterable[Mapping[str, Any] | DepthSample],
) -> list[DepthSample]:
    """Convert heterogeneous records into validated samples."""

    result: list[DepthSample] = []

    for index, record in enumerate(records):
        if isinstance(record, DepthSample):
            sample = record
        elif isinstance(record, Mapping):
            sample = mapping_to_sample(record, index)
        else:
            raise TypeError(
                "records must contain mappings or DepthSample objects"
            )

        if sample.ground_truth < 0:
            raise ValueError(
                "ground_truth cannot be negative"
            )

        if sample.prediction < 0:
            raise ValueError(
                "prediction cannot be negative"
            )

        result.append(sample)

    if not result:
        raise ValueError("CIDAR samples cannot be empty")

    return result


def fuse_predictions(
    predictions: Sequence[float],
    *,
    weights: Sequence[float] | None = None,
) -> float:
    """Fuse multiple sensor predictions using a weighted mean."""

    if not predictions:
        raise ValueError("predictions cannot be empty")

    values = [
        _number(value, "prediction")
        for value in predictions
    ]

    if weights is None:
        return sum(values) / len(values)

    if len(weights) != len(values):
        raise ValueError(
            "weights and predictions must have the same length"
        )

    numeric_weights = [
        _number(weight, "weight")
        for weight in weights
    ]

    total = sum(numeric_weights)

    if total <= 0:
        raise ValueError(
            "sum of weights must be positive"
        )

    return sum(
        value * weight
        for value, weight in zip(
            values,
            numeric_weights,
        )
    ) / total


def validate_adapter_output(
    samples: Iterable[DepthSample],
) -> list[DepthSample]:
    """Validate adapter output."""

    result = list(samples)

    if not result:
        raise ValueError("adapter output is empty")

    for sample in result:
        if sample.ground_truth < 0:
            raise ValueError(
                "ground_truth cannot be negative"
            )

        if sample.prediction < 0:
            raise ValueError(
                "prediction cannot be negative"
            )

    return result


__all__ = [
    "SensorReading",
    "camera_adapter",
    "lidar_adapter",
    "radar_adapter",
    "mapping_to_sample",
    "adapt_samples",
    "fuse_predictions",
    "validate_adapter_output",
]