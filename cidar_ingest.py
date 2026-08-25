"""CIDAR dataset ingestion and serialization."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .cidar_dataset import DepthSample


class CIDARDataError(ValueError):
    """Raised when CIDAR input data is invalid."""


def _sample(payload: dict, index: int) -> DepthSample:
    if "ground_truth" not in payload:
        raise CIDARDataError("missing ground_truth")

    if "prediction" not in payload:
        raise CIDARDataError("missing prediction")

    try:
        ground_truth = float(payload["ground_truth"])
        prediction = float(payload["prediction"])
    except (TypeError, ValueError) as exc:
        raise CIDARDataError(
            "ground_truth and prediction must be numeric"
        ) from exc

    return DepthSample(
        ground_truth=ground_truth,
        prediction=prediction,
        sample_id=payload.get("sample_id", index),
    )


def load_csv(path: str | Path) -> list[DepthSample]:
    path = Path(path)

    try:
        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)

            if not reader.fieldnames:
                raise CIDARDataError(
                    "CSV is missing a header"
                )

            required = {
                "ground_truth",
                "prediction",
            }

            if not required.issubset(reader.fieldnames):
                raise CIDARDataError(
                    "CSV must contain ground_truth and prediction"
                )

            samples = [
                _sample(row, index)
                for index, row in enumerate(reader)
            ]

    except OSError as exc:
        raise CIDARDataError(
            f"unable to read CSV: {path}"
        ) from exc

    if not samples:
        raise CIDARDataError("dataset is empty")

    return samples


def load_json(path: str | Path) -> list[DepthSample]:
    path = Path(path)

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CIDARDataError(
            f"unable to read JSON: {path}"
        ) from exc

    if isinstance(payload, dict):
        payload = payload.get("samples")

    if not isinstance(payload, list):
        raise CIDARDataError(
            "JSON must contain a list of samples"
        )

    samples = [
        _sample(item, index)
        for index, item in enumerate(payload)
    ]

    if not samples:
        raise CIDARDataError("dataset is empty")

    return samples


def load_jsonl(path: str | Path) -> list[DepthSample]:
    path = Path(path)
    samples: list[DepthSample] = []

    try:
        lines = path.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError as exc:
        raise CIDARDataError(
            f"unable to read JSONL: {path}"
        ) from exc

    for index, line in enumerate(lines):
        if not line.strip():
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CIDARDataError(
                f"invalid JSONL at line {index + 1}"
            ) from exc

        if not isinstance(payload, dict):
            raise CIDARDataError(
                f"JSONL line {index + 1} must be an object"
            )

        samples.append(
            _sample(payload, index)
        )

    if not samples:
        raise CIDARDataError("dataset is empty")

    return samples


def load_dataset(path: str | Path) -> list[DepthSample]:
    """Dispatch ingestion based on file extension."""

    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return load_csv(path)

    if suffix == ".json":
        return load_json(path)

    if suffix == ".jsonl":
        return load_jsonl(path)

    raise CIDARDataError(
        f"unsupported dataset format: {suffix}"
    )


def save_jsonl(
    samples: list[DepthSample],
    path: str | Path,
) -> None:
    path = Path(path)

    with path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        for sample in samples:
            payload = {
                "ground_truth": sample.ground_truth,
                "prediction": sample.prediction,
                "sample_id": sample.sample_id,
            }

            handle.write(
                json.dumps(payload)
                + "\n"
            )


__all__ = [
    "CIDARDataError",
    "load_csv",
    "load_json",
    "load_jsonl",
    "load_dataset",
    "save_jsonl",
]