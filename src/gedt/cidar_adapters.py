"""
CIDAR real-world dataset adapter layer.

Adapters convert external datasets into the normalized GEDT/CIDAR
DepthSample representation.

The evaluation engine remains dataset-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

from .cidar_dataset import DepthSample


class CIDARDatasetAdapter(ABC):
    """Base interface for real-world CIDAR datasets."""

    name: str = "unknown"
    version: str = "unknown"

    @abstractmethod
    def load(
        self,
        root: str | Path,
    ) -> Iterable[DepthSample]:
        """Load normalized samples from a dataset."""
        raise NotImplementedError


class CSVDepthAdapter(CIDARDatasetAdapter):
    """
    Generic adapter for datasets exported as CSV.

    Expected columns:

        ground_truth
        prediction

    Optional:

        sample_id
    """

    name = "generic-csv"

    def __init__(
        self,
        *,
        version: str = "1.0",
    ) -> None:
        self.version = version

    def load(
        self,
        root: str | Path,
    ) -> Iterable[DepthSample]:
        from .cidar_ingest import load_csv

        return load_csv(Path(root))


class JSONDepthAdapter(CIDARDatasetAdapter):
    """Generic JSON depth dataset adapter."""

    name = "generic-json"

    def __init__(
        self,
        *,
        version: str = "1.0",
    ) -> None:
        self.version = version

    def load(
        self,
        root: str | Path,
    ) -> Iterable[DepthSample]:
        from .cidar_ingest import load_json

        return load_json(Path(root))


class JSONLDepthAdapter(CIDARDatasetAdapter):
    """Generic JSONL depth dataset adapter."""

    name = "generic-jsonl"

    def __init__(
        self,
        *,
        version: str = "1.0",
    ) -> None:
        self.version = version

    def load(
        self,
        root: str | Path,
    ) -> Iterable[DepthSample]:
        from .cidar_ingest import load_jsonl

        return load_jsonl(Path(root))


def validate_samples(
    samples: Iterable[DepthSample],
) -> list[DepthSample]:
    """
    Normalize and validate an adapter's output.

    All samples must contain finite, non-negative distances.
    """

    import math

    result = list(samples)

    if not result:
        raise ValueError(
            "adapter produced no samples"
        )

    for index, sample in enumerate(result):
        if not math.isfinite(sample.ground_truth):
            raise ValueError(
                f"sample {index} has invalid ground truth"
            )

        if not math.isfinite(sample.prediction):
            raise ValueError(
                f"sample {index} has invalid prediction"
            )

        if sample.ground_truth < 0.0:
            raise ValueError(
                f"sample {index} has negative ground truth"
            )

        if sample.prediction < 0.0:
            raise ValueError(
                f"sample {index} has negative prediction"
            )

    return result


def load_with_adapter(
    adapter: CIDARDatasetAdapter,
    root: str | Path,
) -> list[DepthSample]:
    """Load and validate a real-world dataset."""
    return validate_samples(
        adapter.load(root)
    )


__all__ = [
    "CIDARDatasetAdapter",
    "CSVDepthAdapter",
    "JSONDepthAdapter",
    "JSONLDepthAdapter",
    "load_with_adapter",
    "validate_samples",
]