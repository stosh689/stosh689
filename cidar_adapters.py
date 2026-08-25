"""CIDAR dataset format adapters."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .cidar_dataset import DepthSample


def _sample_from_mapping(data: dict, index: int) -> DepthSample:
    if "ground_truth" not in data:
        raise ValueError("missing ground_truth")
    if "prediction" not in data:
        raise ValueError("missing prediction")

    return DepthSample(
        ground_truth=float(data["ground_truth"]),
        prediction=float(data["prediction"]),
        sample_id=data.get("sample_id", index),
    )


def validate_samples(
    samples: Iterable[DepthSample],
) -> list[DepthSample]:
    """Validate and return CIDAR samples."""

    result = list(samples)

    if not result:
        raise ValueError("CIDAR dataset cannot be empty")

    for sample in result:
        if sample.ground_truth < 0:
            raise ValueError("ground_truth cannot be negative")
        if sample.prediction < 0:
            raise ValueError("prediction cannot be negative")

    return result


class CSVDepthAdapter:
    """Load depth samples from CSV."""

    def load(self, path: str | Path) -> list[DepthSample]:
        path = Path(path)

        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)

            if reader.fieldnames is None:
                raise ValueError("CSV has no header")

            required = {"ground_truth", "prediction"}

            if not required.issubset(reader.fieldnames):
                raise ValueError(
                    "CSV must contain ground_truth and prediction"
                )

            samples = [
                _sample_from_mapping(row, index)
                for index, row in enumerate(reader)
            ]

        return validate_samples(samples)


class JSONDepthAdapter:
    """Load depth samples from a JSON array or wrapped object."""

    def load(self, path: str | Path) -> list[DepthSample]:
        path = Path(path)

        try:
            payload = json.loads(
                path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise ValueError("invalid JSON") from exc

        if isinstance(payload, dict):
            payload = payload.get("samples")

        if not isinstance(payload, list):
            raise ValueError("JSON must contain a sample list")

        samples = [
            _sample_from_mapping(item, index)
            for index, item in enumerate(payload)
        ]

        return validate_samples(samples)


class JSONLDepthAdapter:
    """Load newline-delimited JSON depth samples."""

    def load(self, path: str | Path) -> list[DepthSample]:
        path = Path(path)
        samples: list[DepthSample] = []

        for index, line in enumerate(
            path.read_text(encoding="utf-8").splitlines()
        ):
            if not line.strip():
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSONL at line {index + 1}"
                ) from exc

            if not isinstance(payload, dict):
                raise ValueError(
                    f"JSONL line {index + 1} must be an object"
                )

            samples.append(
                _sample_from_mapping(payload, index)
            )

        return validate_samples(samples)


def load_with_adapter(
    adapter,
    path: str | Path,
) -> list[DepthSample]:
    """Load samples using a supplied adapter."""

    return adapter.load(path)


__all__ = [
    "CSVDepthAdapter",
    "JSONDepthAdapter",
    "JSONLDepthAdapter",
    "load_with_adapter",
    "validate_samples",
]