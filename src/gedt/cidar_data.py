"""
CIDAR real-world sensor data compatibility layer.

Provides lightweight, dependency-free data models and parsers for
image/depth/range measurements. Designed to be extended with KITTI,
NYU Depth V2, LiDAR, radar, and other real-world datasets.

Python: >=3.10
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import math


@dataclass(frozen=True)
class SensorPoint:
    """A single range/depth measurement."""

    x: float
    y: float
    z: float
    intensity: float | None = None

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.z)

        if not all(math.isfinite(value) for value in values):
            raise ValueError("SensorPoint coordinates must be finite")

        if self.intensity is not None and not math.isfinite(self.intensity):
            raise ValueError("SensorPoint intensity must be finite")


@dataclass(frozen=True)
class CIDARFrame:
    """Normalized representation of one CIDAR sensor frame."""

    frame_id: str
    timestamp: float | None = None
    image_path: str | None = None
    depth_path: str | None = None
    points: tuple[SensorPoint, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.frame_id:
            raise ValueError("frame_id must not be empty")

        if self.timestamp is not None and not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite")

    @property
    def point_count(self) -> int:
        """Return the number of sensor points in this frame."""
        return len(self.points)


@dataclass(frozen=True)
class CIDARDataset:
    """Collection of normalized CIDAR frames."""

    name: str
    frames: tuple[CIDARFrame, ...]
    source: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def frame_count(self) -> int:
        """Return the number of frames."""
        return len(self.frames)

    @property
    def point_count(self) -> int:
        """Return the total number of sensor points."""
        return sum(frame.point_count for frame in self.frames)


def _as_float(value: Any, field_name: str) -> float:
    """Convert a value to finite float."""
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be numeric"
        ) from exc

    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")

    return result


def parse_sensor_point(
    value: Mapping[str, Any] | Iterable[Any],
) -> SensorPoint:
    """
    Parse a sensor point from either:

        {"x": 1, "y": 2, "z": 3}

    or:

        [1, 2, 3]

    Optional intensity is supported.
    """
    if isinstance(value, Mapping):
        try:
            x = value["x"]
            y = value["y"]
            z = value["z"]
        except KeyError as exc:
            raise ValueError(
                "sensor point mapping requires x, y, and z"
            ) from exc

        intensity = value.get("intensity")

    else:
        values = list(value)

        if len(values) < 3:
            raise ValueError(
                "sensor point sequence requires at least x, y, and z"
            )

        x, y, z = values[:3]
        intensity = values[3] if len(values) >= 4 else None

    return SensorPoint(
        x=_as_float(x, "x"),
        y=_as_float(y, "y"),
        z=_as_float(z, "z"),
        intensity=(
            None
            if intensity is None
            else _as_float(intensity, "intensity")
        ),
    )


def parse_frame(
    value: Mapping[str, Any],
    *,
    default_frame_id: str = "frame-0",
) -> CIDARFrame:
    """Parse a normalized CIDAR frame from a mapping."""
    if not isinstance(value, Mapping):
        raise TypeError("frame must be a mapping")

    frame_id = str(value.get("frame_id", default_frame_id))

    timestamp_value = value.get("timestamp")
    timestamp = (
        None
        if timestamp_value is None
        else _as_float(timestamp_value, "timestamp")
    )

    points_value = value.get("points", ())
    points = tuple(parse_sensor_point(point) for point in points_value)

    metadata = value.get("metadata", {})

    if metadata is None:
        metadata = {}

    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping")

    return CIDARFrame(
        frame_id=frame_id,
        timestamp=timestamp,
        image_path=_optional_string(value.get("image_path")),
        depth_path=_optional_string(value.get("depth_path")),
        points=points,
        metadata=dict(metadata),
    )


def _optional_string(value: Any) -> str | None:
    """Normalize optional path/string values."""
    if value is None:
        return None

    result = str(value).strip()

    return result if result else None


def parse_dataset(
    value: Mapping[str, Any],
    *,
    default_name: str = "cidar-dataset",
) -> CIDARDataset:
    """
    Parse a complete CIDAR dataset.

    Expected structure:

        {
            "name": "example",
            "source": "KITTI",
            "frames": [
                {
                    "frame_id": "000001",
                    "timestamp": 1.0,
                    "points": [
                        [1, 2, 3]
                    ]
                }
            ]
        }
    """
    if not isinstance(value, Mapping):
        raise TypeError("dataset must be a mapping")

    name = str(value.get("name", default_name)).strip()

    if not name:
        raise ValueError("dataset name must not be empty")

    frames_value = value.get("frames", ())

    if frames_value is None:
        frames_value = ()

    frames = tuple(
        parse_frame(frame, default_frame_id=f"frame-{index}")
        for index, frame in enumerate(frames_value)
    )

    metadata = value.get("metadata", {})

    if metadata is None:
        metadata = {}

    if not isinstance(metadata, Mapping):
        raise TypeError("dataset metadata must be a mapping")

    return CIDARDataset(
        name=name,
        frames=frames,
        source=_optional_string(value.get("source")),
        metadata=dict(metadata),
    )


def load_json(path: str | Path) -> CIDARDataset:
    """Load a CIDAR dataset from a JSON file."""
    file_path = Path(path)

    with file_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return parse_dataset(payload)


def dataset_summary(dataset: CIDARDataset) -> dict[str, Any]:
    """Return a machine-readable dataset summary."""
    return {
        "name": dataset.name,
        "source": dataset.source,
        "frame_count": dataset.frame_count,
        "point_count": dataset.point_count,
        "metadata": dict(dataset.metadata),
    }


def validate_dataset(dataset: CIDARDataset) -> list[str]:
    """
    Validate a normalized dataset.

    Returns a list of validation errors.
    An empty list means the dataset is valid.
    """
    errors: list[str] = []

    if not dataset.name:
        errors.append("dataset name is empty")

    if not isinstance(dataset.frames, tuple):
        errors.append("frames must be a tuple")

    for index, frame in enumerate(dataset.frames):
        if not frame.frame_id:
            errors.append(f"frame {index} has no frame_id")

        for point_index, point in enumerate(frame.points):
            for coordinate_name, coordinate in (
                ("x", point.x),
                ("y", point.y),
                ("z", point.z),
            ):
                if not math.isfinite(coordinate):
                    errors.append(
                        f"frame {index} point {point_index} "
                        f"{coordinate_name} is not finite"
                    )

    return errors


def normalize_frames(
    frames: Iterable[Mapping[str, Any]],
) -> tuple[CIDARFrame, ...]:
    """Normalize an iterable of raw frame mappings."""
    return tuple(
        parse_frame(frame, default_frame_id=f"frame-{index}")
        for index, frame in enumerate(frames)
    )


__all__ = [
    "CIDARDataset",
    "CIDARFrame",
    "SensorPoint",
    "dataset_summary",
    "load_json",
    "normalize_frames",
    "parse_dataset",
    "parse_frame",
    "parse_sensor_point",
    "validate_dataset",
]