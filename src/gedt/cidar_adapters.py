"""Adapters for loading CIDAR depth datasets."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .cidar_dataset import DepthSample


@dataclass(frozen=True)
class SensorReading:
    sensor: str
    value: float
    timestamp: float | None = None
    sample_id: Any = None


def _number(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be numeric"
        ) from exc

    if result != result:
        raise ValueError(
            f"{name} must be finite"
        )

    return result


def mapping_to_sample(
    record: Mapping[str, Any],
    index: int = 0,
) -> DepthSample:
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
        sample_id=record.get(
            "sample_id",
            index,
        ),
    )


def validate_samples(
    samples: Iterable[DepthSample],
) -> list[DepthSample]:
    result = list(samples)

    if not result:
        raise ValueError(
            "CIDAR samples cannot be empty"
        )

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


class CSVDepthAdapter:
    """Load depth samples from CSV."""

    def load(self, path: str | Path) -> list[DepthSample]:
        path = Path(path)

        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)

            if not reader.fieldnames:
                raise ValueError(
                    "CSV has no header"
                )

            required = {
                "ground_truth",
                "prediction",
            }

            missing = required - set(
                reader.fieldnames
            )

            if missing:
                raise ValueError(
                    "missing CSV columns: "
                    + ", ".join(sorted(missing))
                )

            records = [
                mapping_to_sample(
                    row,
                    index,
                )
                for index, row in enumerate(reader)
            ]

        return validate_samples(records)


class JSONDepthAdapter:
    """Load depth samples from JSON."""

    def load(self, path: str | Path) -> list[DepthSample]:
        path = Path(path)

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        if isinstance(payload, dict):
            payload = payload.get(
                "samples",
                [],
            )

        if not isinstance(payload, list):
            raise ValueError(
                "JSON dataset must be a list"
            )

        samples = [
            mapping_to_sample(
                record,
                index,
            )
            for index, record in enumerate(payload)
        ]

        return validate_samples(samples)


class JSONLDepthAdapter:
    """Load newline-delimited JSON depth samples."""

    def load(self, path: str | Path) -> list[DepthSample]:
        path = Path(path)
        samples: list[DepthSample] = []

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for index, line in enumerate(handle):
                line = line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid JSONL at line {index + 1}"
                    ) from exc

                samples.append(
                    mapping_to_sample(
                        record,
                        index,
                    )
                )

        return validate_samples(samples)


def load_with_adapter(
    adapter: Any,
    path: str | Path,
) -> list[DepthSample]:
    if not hasattr(adapter, "load"):
        raise TypeError(
            "adapter must provide a load() method"
        )

    return validate_samples(
        adapter.load(path)
    )


def camera_adapter(
    prediction: float,
    *,
    sample_id: Any = None,
) -> DepthSample:
    return DepthSample(
        ground_truth=0.0,
        prediction=_number(
            prediction,
            "prediction",
        ),
        sample_id=sample_id,
    )


def lidar_adapter(
    prediction: float,
    *,
    sample_id: Any = None,
) -> DepthSample:
    return DepthSample(
        ground_truth=0.0,
        prediction=_number(
            prediction,
            "prediction",
        ),
        sample_id=sample_id,
    )


def radar_adapter(
    prediction: float,
    *,
    sample_id: Any = None,
) -> DepthSample:
    return DepthSample(
        ground_truth=0.0,
        prediction=_number(
            prediction,
            "prediction",
        ),
        sample_id=sample_id,
    )


def adapt_samples(
    records: Iterable[
        Mapping[str, Any] | DepthSample
    ],
) -> list[DepthSample]:
    result: list[DepthSample] = []

    for index, record in enumerate(records):
        if isinstance(record, DepthSample):
            sample = record
        elif isinstance(record, Mapping):
            sample = mapping_to_sample(
                record,
                index,
            )
        else:
            raise TypeError(
                "records must contain mappings "
                "or DepthSample objects"
            )

        result.append(sample)

    return validate_samples(result)


def fuse_predictions(
    predictions: Iterable[float],
    *,
    weights: Iterable[float] | None = None,
) -> float:
    values = [
        _number(value, "prediction")
        for value in predictions
    ]

    if not values:
        raise ValueError(
            "predictions cannot be empty"
        )

    if weights is None:
        return sum(values) / len(values)

    numeric_weights = [
        _number(weight, "weight")
        for weight in weights
    ]

    if len(values) != len(numeric_weights):
        raise ValueError(
            "weights and predictions must have "
            "the same length"
        )

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
    return validate_samples(samples)


__all__ = [
    "SensorReading",
    "CSVDepthAdapter",
    "JSONDepthAdapter",
    "JSONLDepthAdapter",
    "load_with_adapter",
    "validate_samples",
    "mapping_to_sample",
    "adapt_samples",
    "fuse_predictions",
    "validate_adapter_output",
    "camera_adapter",
    "lidar_adapter",
    "radar_adapter",
]