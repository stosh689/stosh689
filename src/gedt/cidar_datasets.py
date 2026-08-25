"""
CIDAR real-world dataset adapters.

Provides lightweight adapters for common computer-vision/ranging
dataset layouts without requiring NumPy, OpenCV, or dataset-specific
packages.

Supported layouts:
- KITTI-style frame directories
- NYU-style image/depth pairs
- Generic image/depth manifests

Python >= 3.10
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
import json

from .cidar_data import (
    CIDARDataset,
    CIDARFrame,
    SensorPoint,
    parse_dataset,
)


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
}

DEPTH_EXTENSIONS = {
    ".png",
    ".npy",
    ".npz",
    ".tif",
    ".tiff",
}


@dataclass(frozen=True)
class DatasetRecord:
    """One image/depth dataset pair."""

    frame_id: str
    image_path: str | None
    depth_path: str | None
    metadata: Mapping[str, Any]


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def _is_depth(path: Path) -> bool:
    return path.suffix.lower() in DEPTH_EXTENSIONS


def _frame_id(path: Path) -> str:
    """Return a stable frame identifier."""
    return path.stem


def _sorted_files(
    directory: Path,
    predicate,
) -> list[Path]:
    return sorted(
        (
            path
            for path in directory.rglob("*")
            if path.is_file() and predicate(path)
        ),
        key=lambda path: str(path),
    )


def discover_image_files(
    directory: str | Path,
) -> list[Path]:
    """Discover image files recursively."""
    root = Path(directory)

    if not root.exists():
        raise FileNotFoundError(root)

    if not root.is_dir():
        raise NotADirectoryError(root)

    return _sorted_files(
        root,
        _is_image,
    )


def discover_depth_files(
    directory: str | Path,
) -> list[Path]:
    """Discover depth files recursively."""
    root = Path(directory)

    if not root.exists():
        raise FileNotFoundError(root)

    if not root.is_dir():
        raise NotADirectoryError(root)

    return _sorted_files(
        root,
        _is_depth,
    )


def pair_files(
    images: Iterable[Path],
    depths: Iterable[Path],
) -> list[DatasetRecord]:
    """
    Pair image and depth files by filename stem.

    Unmatched files are retained rather than silently discarded.
    """
    image_map = {
        _frame_id(path): path
        for path in images
    }

    depth_map = {
        _frame_id(path): path
        for path in depths
    }

    frame_ids = sorted(
        set(image_map) | set(depth_map)
    )

    records: list[DatasetRecord] = []

    for frame_id in frame_ids:
        image = image_map.get(frame_id)
        depth = depth_map.get(frame_id)

        records.append(
            DatasetRecord(
                frame_id=frame_id,
                image_path=(
                    str(image)
                    if image is not None
                    else None
                ),
                depth_path=(
                    str(depth)
                    if depth is not None
                    else None
                ),
                metadata={
                    "image_available": image is not None,
                    "depth_available": depth is not None,
                },
            )
        )

    return records


def records_to_dataset(
    records: Iterable[DatasetRecord],
    *,
    name: str,
    source: str,
) -> CIDARDataset:
    """Convert dataset records to the normalized CIDAR model."""
    frames = tuple(
        CIDARFrame(
            frame_id=record.frame_id,
            image_path=record.image_path,
            depth_path=record.depth_path,
            points=(),
            metadata=dict(record.metadata),
        )
        for record in records
    )

    return CIDARDataset(
        name=name,
        source=source,
        frames=frames,
    )


def load_directory_dataset(
    image_directory: str | Path,
    depth_directory: str | Path,
    *,
    name: str = "cidar-directory",
    source: str = "generic",
) -> CIDARDataset:
    """
    Load a generic image/depth directory pair.
    """
    images = discover_image_files(
        image_directory
    )

    depths = discover_depth_files(
        depth_directory
    )

    records = pair_files(
        images,
        depths,
    )

    return records_to_dataset(
        records,
        name=name,
        source=source,
    )


def load_manifest(
    path: str | Path,
) -> CIDARDataset:
    """
    Load a normalized dataset manifest.

    JSON may contain either the normalized CIDAR structure or:

        {
            "dataset": "example",
            "source": "KITTI",
            "records": [
                {
                    "frame_id": "000001",
                    "image": "image.png",
                    "depth": "depth.png"
                }
            ]
        }
    """
    manifest_path = Path(path)

    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)

    with manifest_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(file)

    if not isinstance(payload, Mapping):
        raise ValueError(
            "dataset manifest must contain a JSON object"
        )

    if "frames" in payload:
        return parse_dataset(payload)

    records_value = payload.get(
        "records",
        [],
    )

    if not isinstance(records_value, list):
        raise ValueError(
            "manifest records must be a list"
        )

    records: list[DatasetRecord] = []

    for index, record in enumerate(records_value):
        if not isinstance(record, Mapping):
            raise ValueError(
                f"record {index} must be an object"
            )

        frame_id = str(
            record.get(
                "frame_id",
                index,
            )
        )

        image_path = record.get(
            "image",
            record.get("image_path"),
        )

        depth_path = record.get(
            "depth",
            record.get("depth_path"),
        )

        records.append(
            DatasetRecord(
                frame_id=frame_id,
                image_path=(
                    str(image_path)
                    if image_path is not None
                    else None
                ),
                depth_path=(
                    str(depth_path)
                    if depth_path is not None
                    else None
                ),
                metadata={
                    "manifest_index": index,
                },
            )
        )

    return records_to_dataset(
        records,
        name=str(
            payload.get(
                "dataset",
                "cidar-manifest",
            )
        ),
        source=str(
            payload.get(
                "source",
                "generic",
            )
        ),
    )


def load_kitti_style(
    root: str | Path,
) -> CIDARDataset:
    """
    Discover a KITTI-style directory structure.

    The adapter intentionally does not assume a single KITTI release
    layout. It searches recursively for image and depth files and
    pairs them by filename stem.
    """
    root_path = Path(root)

    if not root_path.exists():
        raise FileNotFoundError(root_path)

    if not root_path.is_dir():
        raise NotADirectoryError(root_path)

    images = discover_image_files(
        root_path
    )

    depths = discover_depth_files(
        root_path
    )

    records = pair_files(
        images,
        depths,
    )

    return records_to_dataset(
        records,
        name="kitti",
        source="KITTI",
    )


def load_nyu_style(
    root: str | Path,
) -> CIDARDataset:
    """
    Discover an NYU Depth V2-style directory.

    Image and depth observations are paired using filename stems.
    """
    root_path = Path(root)

    if not root_path.exists():
        raise FileNotFoundError(root_path)

    if not root_path.is_dir():
        raise NotADirectoryError(root_path)

    images = discover_image_files(
        root_path
    )

    depths = discover_depth_files(
        root_path
    )

    records = pair_files(
        images,
        depths,
    )

    return records_to_dataset(
        records,
        name="nyu-depth-v2",
        source="NYU Depth V2",
    )


def dataset_statistics(
    dataset: CIDARDataset,
) -> dict[str, Any]:
    """Calculate adapter-level dataset statistics."""
    frames = dataset.frames

    image_count = sum(
        frame.image_path is not None
        for frame in frames
    )

    depth_count = sum(
        frame.depth_path is not None
        for frame in frames
    )

    paired_count = sum(
        frame.image_path is not None
        and frame.depth_path is not None
        for frame in frames
    )

    return {
        "name": dataset.name,
        "source": dataset.source,
        "frames": len(frames),
        "images": image_count,
        "depth_maps": depth_count,
        "paired_frames": paired_count,
        "unpaired_frames": (
            len(frames) - paired_count
        ),
    }


__all__ = [
    "DatasetRecord",
    "dataset_statistics",
    "discover_depth_files",
    "discover_image_files",
    "load_directory_dataset",
    "load_kitti_style",
    "load_manifest",
    "load_nyu_style",
    "pair_files",
    "records_to_dataset",
]