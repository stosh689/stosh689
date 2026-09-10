"""High-level CIDAR experiment runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .cidar_dataset import DepthMetrics
from .cidar_ingest import load_dataset
from .cidar_protocol import (
    CIDARBenchmarkConfig,
    CIDARBenchmarkRecord,
    protocol_report,
    run_protocol,
)
from .cidar_results import save_result


@dataclass(frozen=True)
class CIDARRunResult:
    """Result of one complete CIDAR experiment."""

    record: CIDARBenchmarkRecord

    @property
    def valid(self) -> bool:
        """Return whether the benchmark result is valid."""
        return self.record.valid

    @property
    def passed(self) -> bool:
        """Return whether the benchmark passed validation."""
        return self.record.valid

    @property
    def samples(self) -> int:
        """Return the number of evaluated samples."""
        return self.record.samples

    @property
    def metrics(self) -> DepthMetrics:
        """Return the core depth metrics."""
        return DepthMetrics(
            valid=self.record.valid,
            samples=self.record.samples,
            mae=self.record.mae,
            rmse=self.record.rmse,
            bias=self.record.bias,
            relative_error=self.record.relative_error,
        )


def run_arrays(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
    config: CIDARBenchmarkConfig,
) -> CIDARRunResult:
    """Run the CIDAR benchmark directly on in-memory arrays."""

    record = run_protocol(
        ground_truth,
        prediction,
        config,
    )

    return CIDARRunResult(record=record)


def run_dataset(
    input_path: str | Path,
    output_path: str | Path,
    config: CIDARBenchmarkConfig,
) -> CIDARRunResult:
    """Load a dataset, evaluate it, and persist the benchmark result."""

    samples = load_dataset(input_path)

    if not samples:
        raise ValueError("dataset contains no valid samples")

    ground_truth = [
        sample.ground_truth
        for sample in samples
    ]

    prediction = [
        sample.prediction
        for sample in samples
    ]

    result = run_arrays(
        ground_truth,
        prediction,
        config,
    )

    save_result(
        result.record,
        output_path,
    )

    return result


def run_and_report(
    input_path: str | Path,
    output_path: str | Path,
    config: CIDARBenchmarkConfig,
) -> str:
    """Run a dataset benchmark and return a human-readable report."""

    result = run_dataset(
        input_path,
        output_path,
        config,
    )

    return (
        "CIDAR EXPERIMENT\n"
        "================\n"
        + protocol_report(result.record)
    )


__all__ = [
    "CIDARRunResult",
    "run_arrays",
    "run_dataset",
    "run_and_report",
]