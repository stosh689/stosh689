"""CIDAR dataset ingestion and persistence."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .cidar_dataset import DepthSample


class CIDARDataError(ValueError):
    """Raised when CIDAR dataset data is invalid."""


def _sample_from_record(
    record: dict,
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

    return DepthSample(
        ground_truth=ground_truth,
        prediction=prediction,
        sample_id=record.get(
            "sample_id",
            index,
        ),
    )


def load_csv(
    path: str | Path,
) -> list[DepthSample]:
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

            missing = required - set(
                reader.fieldnames
            )

            if missing:
                raise CIDARDataError(
                    "missing CSV columns: "
                    + ", ".join(sorted(missing))
                )

            return [
                _sample_from_record(
                    dict(row),
                    index,
                )
                for index, row in enumerate(reader)
            ]

    except OSError as exc:
        raise CIDARDataError(
            f"unable to read CSV: {path}"
        ) from exc


def load_json(
    path: str | Path,
) -> list[DepthSample]:
    path = Path(path)

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CIDARDataError(
            f"unable to read JSON: {path}"
        ) from exc

    if isinstance(payload, dict):
        payload = payload.get(
            "samples"
        )

    if not isinstance(payload, list):
        raise CIDARDataError(
            "JSON dataset must contain a sample list"
        )

    return [
        _sample_from_record(
            dict(record),
            index,
        )
        for index, record in enumerate(payload)
    ]


def load_jsonl(
    path: str | Path,
) -> list[DepthSample]:
    path = Path(path)
    samples: list[DepthSample] = []

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line_number, line in enumerate(
                handle,
                start=1,
            ):
                line = line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise CIDARDataError(
                        f"invalid JSONL at line "
                        f"{line_number}"
                    ) from exc

                if not isinstance(record, dict):
                    raise CIDARDataError(
                        f"JSONL line {line_number} "
                        "must contain an object"
                    )

                samples.append(
                    _sample_from_record(
                        record,
                        len(samples),
                    )
                )

    except OSError as exc:
        raise CIDARDataError(
            f"unable to read JSONL: {path}"
        ) from exc

    return samples


def load_dataset(
    path: str | Path,
) -> list[DepthSample]:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return load_csv(path)

    if suffix == ".json":
        return load_json(path)

    if suffix in {".jsonl", ".ndjson"}:
        return load_jsonl(path)

    raise CIDARDataError(
        f"unsupported dataset format: {suffix}"
    )


def save_jsonl(
    samples: Iterable[DepthSample],
    path: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
                json.dumps(
                    payload,
                    sort_keys=True,
                )
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