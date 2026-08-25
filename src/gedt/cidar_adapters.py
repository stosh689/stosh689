from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable, Mapping

from .cidar_dataset import DepthSample


class DepthAdapter(ABC):
    @abstractmethod
    def load(self, path: str | Path) -> list[DepthSample]:
        raise NotImplementedError


def _number(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc


def _make_sample(
    record: Mapping[str, Any],
    index: int,
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
        sample_id=record.get("sample_id", index),
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


class CSVDepthAdapter(DepthAdapter):
    def load(
        self,
        path: str | Path,
    ) -> list[DepthSample]:
        path = Path(path)

        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)

            if reader.fieldnames is None:
                raise ValueError(
                    "CSV file has no header"
                )

            samples = [
                _make_sample(row, index)
                for index, row in enumerate(reader)
            ]

        return validate_samples(samples)


class JSONDepthAdapter(DepthAdapter):
    def load(
        self,
        path: str | Path,
    ) -> list[DepthSample]:
        path = Path(path)

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        if isinstance(payload, Mapping):
            payload = payload.get(
                "samples",
                payload.get(
                    "records",
                    [payload],
                ),
            )

        if not isinstance(payload, list):
            raise ValueError(
                "JSON dataset must contain a list"
            )

        samples: list[DepthSample] = []

        for index, row in enumerate(payload):
            if not isinstance(row, Mapping):
                raise ValueError(
                    f"JSON record {index} must be an object"
                )

            samples.append(
                _make_sample(
                    row,
                    index,
                )
            )

        return validate_samples(samples)


class JSONLDepthAdapter(DepthAdapter):
    def load(
        self,
        path: str | Path,
    ) -> list[DepthSample]:
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
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid JSONL at line {index + 1}"
                    ) from exc

                if not isinstance(row, Mapping):
                    raise ValueError(
                        f"JSONL record {index} must be an object"
                    )

                samples.append(
                    _make_sample(
                        row,
                        index,
                    )
                )

        return validate_samples(samples)


def load_with_adapter(
    adapter: DepthAdapter,
    path: str | Path,
) -> list[DepthSample]:
    return adapter.load(path)


def adapter_for_path(
    path: str | Path,
) -> DepthAdapter:
    suffix = Path(path).suffix.lower()

    if suffix == ".csv":
        return CSVDepthAdapter()

    if suffix == ".json":
        return JSONDepthAdapter()

    if suffix in {".jsonl", ".ndjson"}:
        return JSONLDepthAdapter()

    raise ValueError(
        f"unsupported dataset format: {suffix}"
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


def mapping_to_sample(
    record: Mapping[str, Any],
    index: int = 0,
) -> DepthSample:
    return _make_sample(
        record,
        index,
    )


def adapt_samples(
    records: Iterable[
        Mapping[str, Any] | DepthSample
    ],
) -> list[DepthSample]:
    samples: list[DepthSample] = []

    for index, record in enumerate(records):
        if isinstance(
            record,
            DepthSample,
        ):
            samples.append(record)

        elif isinstance(
            record,
            Mapping,
        ):
            samples.append(
                mapping_to_sample(
                    record,
                    index,
                )
            )

        else:
            raise TypeError(
                "records must contain mappings "
                "or DepthSample objects"
            )

    return validate_samples(samples)


def fuse_predictions(
    predictions: list[float] | tuple[float, ...],
    *,
    weights: list[float] | tuple[float, ...] | None = None,
) -> float:
    if not predictions:
        raise ValueError(
            "predictions cannot be empty"
        )

    values = [
        _number(
            value,
            "prediction",
        )
        for value in predictions
    ]

    if weights is None:
        return sum(values) / len(values)

    if len(weights) != len(values):
        raise ValueError(
            "weights and predictions must "
            "have the same length"
        )

    numeric_weights = [
        _number(
            weight,
            "weight",
        )
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
    return validate_samples(samples)


__all__ = [
    "DepthAdapter",
    "CSVDepthAdapter",
    "JSONDepthAdapter",
    "JSONLDepthAdapter",
    "load_with_adapter",
    "adapter_for_path",
    "validate_samples",
    "camera_adapter",
    "lidar_adapter",
    "radar_adapter",
    "mapping_to_sample",
    "adapt_samples",
    "fuse_predictions",
    "validate_adapter_output",
]