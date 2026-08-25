"""
CIDAR real-world data ingestion.
Supports simple CSV, JSON and JSONL representations of paired
ground-truth/prediction range measurements.
Dataset-specific preprocessing remains outside this module.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any
from .cidar_dataset import DepthSample
class CIDARDataError(ValueError):
    """Raised when CIDAR input data is invalid."""
def _number(
    value: Any,
    field: str,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise CIDARDataError(
            f"{field} must be numeric"
        ) from exc
    if not result == result:
        raise CIDARDataError(
            f"{field} must not be NaN"
        )
    if result == float("inf") or result == float("-inf"):
        raise CIDARDataError(
            f"{field} must be finite"
        )
    return result
def sample_from_mapping(
    item: dict[str, Any],
    *,
    index: int = 0,
) -> DepthSample:
    """Convert one mapping into a DepthSample."""
    if "ground_truth" not in item:
        raise CIDARDataError(
            "missing ground_truth"
        )
    if "prediction" not in item:
        raise CIDARDataError(
            "missing prediction"
        )
    sample_id = item.get(
        "sample_id",
        index,
    )
    return DepthSample(
        ground_truth=_number(
            item["ground_truth"],
            "ground_truth",
        ),
        prediction=_number(
            item["prediction"],
            "prediction",
        ),
        sample_id=sample_id,
    )
def load_json(
    path: str | Path,
) -> list[DepthSample]:
    """Load CIDAR samples from JSON."""
    source = Path(path)
    try:
        data = json.loads(
            source.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as exc:
        raise CIDARDataError(
            f"invalid JSON: {exc}"
        ) from exc
    if isinstance(data, dict):
        data = data.get("samples")
    if not isinstance(data, list):
        raise CIDARDataError(
            "JSON must contain a list of samples"
        )
    return [
        sample_from_mapping(
            item,
            index=index,
        )
        for index, item in enumerate(data)
        if isinstance(item, dict)
    ]
def load_jsonl(
    path: str | Path,
) -> list[DepthSample]:
    """Load CIDAR samples from JSON Lines."""
    source = Path(path)
    samples: list[DepthSample] = []
    for index, line in enumerate(
        source.read_text(
            encoding="utf-8"
        ).splitlines()
    ):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CIDARDataError(
                f"invalid JSONL on line {index + 1}"
            ) from exc
        if not isinstance(item, dict):
            raise CIDARDataError(
                f"line {index + 1} must contain an object"
            )
        samples.append(
            sample_from_mapping(
                item,
                index=index,
            )
        )
    return samples
def load_csv(
    path: str | Path,
) -> list[DepthSample]:
    """Load CIDAR samples from CSV."""
    source = Path(path)
    samples: list[DepthSample] = []
    with source.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise CIDARDataError(
                "CSV is missing a header"
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
                "CSV missing columns: "
                + ", ".join(sorted(missing))
            )
        for index, row in enumerate(reader):
            samples.append(
                sample_from_mapping(
                    row,
                    index=index,
                )
            )
    return samples
def load_dataset(
    path: str | Path,
) -> list[DepthSample]:
    """
    Load a dataset according to its extension.
    Supported:
      .csv
      .json
      .jsonl
    """
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        return load_csv(source)
    if suffix == ".json":
        return load_json(source)
    if suffix in {".jsonl", ".ndjson"}:
        return load_jsonl(source)
    raise CIDARDataError(
        f"unsupported dataset format: {suffix}"
    )
def save_jsonl(
    samples: list[DepthSample],
    path: str | Path,
) -> Path:
    """Save samples as JSONL for reproducible experiments."""
    output = Path(path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    with output.open(
        "w",
        encoding="utf-8",
    ) as handle:
        for sample in samples:
            handle.write(
                json.dumps(
                    {
                        "ground_truth": sample.ground_truth,
                        "prediction": sample.prediction,
                        "sample_id": sample.sample_id,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    return output
__all__ = [
    "CIDARDataError",
    "load_csv",
    "load_dataset",
    "load_json",
    "load_jsonl",
    "sample_from_mapping",
    "save_jsonl",
]