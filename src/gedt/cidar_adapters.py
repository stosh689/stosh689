from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


@dataclass(frozen=True)
class DepthRecord:
    """
    Normalized depth/range measurement.

    The adapters convert different input formats into this common structure.
    """
    image_id: str
    predicted_depth: float
    ground_truth_depth: float | None = None
    confidence: float | None = None
    metadata: dict[str, Any] | None = None


class DepthAdapter(ABC):
    """Base class for CIDAR depth-data adapters."""

    @abstractmethod
    def load(self, path: str | Path) -> list[DepthRecord]:
        """Load records from a file."""
        raise NotImplementedError


def _first_value(
    row: Mapping[str, Any],
    names: Sequence[str],
    default: Any = None,
) -> Any:
    """Return the first matching field from a mapping."""
    normalized = {
        str(key).strip().lower(): value
        for key, value in row.items()
    }

    for name in names:
        value = normalized.get(name.lower())

        if value is not None and value != "":
            return value

    return default


def _float_or_none(value: Any) -> float | None:
    """Convert a value to float, returning None for missing values."""
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_record(
    row: Mapping[str, Any],
    index: int,
) -> DepthRecord:
    """
    Convert a raw mapping into a normalized DepthRecord.

    Several common field names are accepted so the adapter layer remains
    compatible with typical CIDAR/KITTI/NYU-style datasets.
    """

    image_id = _first_value(
        row,
        (
            "image_id",
            "image",
            "filename",
            "file",
            "frame_id",
            "frame",
            "id",
        ),
        default=str(index),
    )

    predicted = _first_value(
        row,
        (
            "predicted_depth",
            "predicted",
            "prediction",
            "pred_depth",
            "depth_pred",
            "estimated_depth",
            "estimated",
            "depth",
            "range",
        ),
    )

    ground_truth = _first_value(
        row,
        (
            "ground_truth_depth",
            "ground_truth",
            "gt_depth",
            "ground_truth_range",
            "gt_range",
            "true_depth",
            "target",
            "actual_depth",
        ),
    )

    confidence = _first_value(
        row,
        (
            "confidence",
            "score",
            "confidence_score",
        ),
    )

    if predicted is None:
        raise ValueError(
            f"Record {index} is missing a predicted depth/range value"
        )

    predicted_float = _float_or_none(predicted)

    if predicted_float is None:
        raise ValueError(
            f"Record {index} has an invalid predicted depth: {predicted!r}"
        )

    ground_truth_float = _float_or_none(ground_truth)
    confidence_float = _float_or_none(confidence)

    metadata = {
        str(key): value
        for key, value in row.items()
        if str(key).strip().lower()
        not in {
            "image_id",
            "image",
            "filename",
            "file",
            "frame_id",
            "frame",
            "id",
            "predicted_depth",
            "predicted",
            "prediction",
            "pred_depth",
            "depth_pred",
            "estimated_depth",
            "estimated",
            "depth",
            "range",
            "ground_truth_depth",
            "ground_truth",
            "gt_depth",
            "ground_truth_range",
            "gt_range",
            "true_depth",
            "target",
            "actual_depth",
            "confidence",
            "score",
            "confidence_score",
        }
    }

    return DepthRecord(
        image_id=str(image_id),
        predicted_depth=predicted_float,
        ground_truth_depth=ground_truth_float,
        confidence=confidence_float,
        metadata=metadata or None,
    )


class CSVDepthAdapter(DepthAdapter):
    """Adapter for CSV depth/range datasets."""

    def load(self, path: str | Path) -> list[DepthRecord]:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        if not path.is_file():
            raise ValueError(f"Expected a file: {path}")

        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)

            if reader.fieldnames is None:
                raise ValueError(
                    f"CSV file has no header: {path}"
                )

            records: list[DepthRecord] = []

            for index, row in enumerate(reader):
                records.append(
                    _normalize_record(row, index)
                )

        return records


class JSONDepthAdapter(DepthAdapter):
    """Adapter for JSON datasets."""

    def load(self, path: str | Path) -> list[DepthRecord]:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        if not path.is_file():
            raise ValueError(f"Expected a file: {path}")

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        if isinstance(payload, Mapping):
            # Support either:
            # {"records": [...]}
            # {"samples": [...]}
            # {"data": [...]}
            for key in ("records", "samples", "data"):
                if key in payload:
                    payload = payload[key]
                    break
            else:
                payload = [payload]

        if not isinstance(payload, list):
            raise ValueError(
                "JSON dataset must contain an object or list of records"
            )

        records: list[DepthRecord] = []

        for index, row in enumerate(payload):
            if not isinstance(row, Mapping):
                raise ValueError(
                    f"JSON record {index} must be an object"
                )

            records.append(
                _normalize_record(row, index)
            )

        return records


class JSONLDepthAdapter(DepthAdapter):
    """Adapter for JSON Lines depth datasets."""

    def load(self, path: str | Path) -> list[DepthRecord]:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        if not path.is_file():
            raise ValueError(f"Expected a file: {path}")

        records: list[DepthRecord] = []

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
                        f"Invalid JSONL record at line {index + 1}"
                    ) from exc

                if not isinstance(row, Mapping):
                    raise ValueError(
                        f"JSONL record {index} must be an object"
                    )

                records.append(
                    _normalize_record(row, index)
                )

        return records


def adapter_for_path(path: str | Path) -> DepthAdapter:
    """Select an adapter based on the file extension."""
    suffix = Path(path).suffix.lower()

    if suffix == ".csv":
        return CSVDepthAdapter()

    if suffix == ".json":
        return JSONDepthAdapter()

    if suffix in {".jsonl", ".ndjson"}:
        return JSONLDepthAdapter()

    raise ValueError(
        f"Unsupported depth dataset format: {suffix or '<none>'}"
    )


def load_with_adapter(
    path: str | Path,
    adapter: DepthAdapter | None = None,
) -> list[DepthRecord]:
    """
    Load a dataset using an explicitly supplied adapter or infer the adapter
    from the file extension.
    """
    selected_adapter = (
        adapter
        if adapter is not None
        else adapter_for_path(path)
    )

    return selected_adapter.load(path)


def records_to_dicts(
    records: Iterable[DepthRecord],
) -> list[dict[str, Any]]:
    """Convert normalized records back into serializable dictionaries."""
    return [
        {
            "image_id": record.image_id,
            "predicted_depth": record.predicted_depth,
            "ground_truth_depth": record.ground_truth_depth,
            "confidence": record.confidence,
            "metadata": record.metadata,
        }
        for record in records
    ]


__all__ = [
    "DepthRecord",
    "DepthAdapter",
    "CSVDepthAdapter",
    "JSONDepthAdapter",
    "JSONLDepthAdapter",
    "adapter_for_path",
    "load_with_adapter",
    "records_to_dicts",
]