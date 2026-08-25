"""CIDAR dataset ingestion."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .cidar_dataset import DepthSample


class CIDARDataError(ValueError):
    """Raised when CIDAR data cannot be ingested."""


def _sample_from_mapping(
    record: Mapping[str, Any],
    index: int,
) -> DepthSample:
    if "ground_truth" not in record:
        raise CIDARDataError(
            "missing ground_truth"
        )

    if "prediction" not in record:
        raise CIDARDataError(
            "missing prediction"
        )

    try:
        ground_truth = float(
            record["ground_truth"]
        )
        prediction = float(
            record["prediction"]
        )
    except (TypeError, ValueError) as exc:
        raise CIDARDataError(
            "ground_truth and prediction must be numeric"
        ) from exc

    if ground_truth < 0:
        raise CIDARDataError(
            "ground_truth cannot be negative"
        )

    if prediction < 0:
        raise CIDARDataError(
            "prediction cannot be negative"
        )

    return DepthSample(
        ground_truth=ground_truth,
        prediction=prediction,
        sample_id=record.get(
            "sample_id",
            index,
        ),
    )


def ingest_records(
    records: Iterable[
        Mapping[str, Any] | DepthSample
    ],
) -> list[DepthSample]:
    """Convert records into DepthSample objects."""

    result: list[DepthSample] = []

    for index, record in enumerate(records):
        if isinstance(record, DepthSample):
            sample = record

            if sample.ground_truth < 0:
                raise CIDARDataError(
                    "ground_truth cannot be negative"
                )

            if sample.prediction < 0:
                raise CIDARDataError(
                    "prediction cannot be negative"
                )

            result.append(sample)
        elif isinstance(record, Mapping):
            result.append(
                _sample_from_mapping(
                    record,
                    index,
                )
            )
        else:
            raise CIDARDataError(
                "records must be mappings or DepthSample objects"
            )

    if not result:
        raise CIDARDataError(
            "dataset cannot be empty"
        )

    return result


def load_csv(
    path: str | Path,
) -> list[DepthSample]:
    """Load CIDAR samples from CSV."""

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
                    "CSV has no header"
                )

            required = {
                "ground_truth",
                "prediction",
            }

            if not required.issubset(
                reader.fieldnames
            ):
                raise CIDARDataError(
                    "CSV requires ground_truth and prediction"
                )

            return ingest_records(reader)

    except OSError as exc:
        raise CIDARDataError(
            f"unable to read CSV: {path}"
        ) from exc


def load_json(
    path: str | Path,
) -> list[DepthSample]:
    """Load CIDAR samples from JSON."""

    path = Path(path)

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CIDARDataError(
            f"unable to read JSON: {path}"
        ) from exc

    if isinstance(payload, dict):
        payload = payload.get(
            "samples",
            payload.get("data"),
        )

    if not isinstance(payload, list):
        raise CIDARDataError(
            "JSON must contain a list of samples"
        )

    return ingest_records(payload)


def load_jsonl(
    path: str | Path,
) -> list[DepthSample]:
    """Load newline-delimited CIDAR JSON."""

    path = Path(path)

    try:
        lines = path.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError as exc:
        raise CIDARDataError(
            f"unable to read JSONL: {path}"
        ) from exc

    records: list[Mapping[str, Any]] = []

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        if not line.strip():
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CIDARDataError(
                f"invalid JSON at line {line_number}"
            ) from exc

        if not isinstance(record, Mapping):
            raise CIDARDataError(
                f"line {line_number} is not an object"
            )

        records.append(record)

    return ingest_records(records)


def load_dataset(
    path: str | Path,
) -> list[DepthSample]:
    """Automatically select an ingestion format."""

    path = Path(path)

    suffix = path.suffix.lower()

    if suffix == ".csv":
        return load_csv(path)

    if suffix == ".json":
        return load_json(path)

    if suffix == ".jsonl":
        return load_jsonl(path)

    raise CIDARDataError(
        f"unsupported file format: {suffix}"
    )


def save_jsonl(
    samples: Iterable[DepthSample],
    path: str | Path,
) -> None:
    """Write samples as JSONL."""

    path = Path(path)

    with path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        for sample in samples:
            handle.write(
                json.dumps(
                    {
                        "ground_truth":
                            sample.ground_truth,
                        "prediction":
                            sample.prediction,
                        "sample_id":
                            sample.sample_id,
                    }
                )
                + "\n"
            )


__all__ = [
    "CIDARDataError",
    "ingest_records",
    "load_csv",
    "load_json",
    "load_jsonl",
    "load_dataset",
    "save_jsonl",
]