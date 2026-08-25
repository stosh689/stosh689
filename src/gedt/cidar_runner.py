"""High-level CIDAR experiment runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .cidar_dataset import (
    DepthMetrics,
    evaluate_arrays,
)
from .cidar_ingest import load_dataset
from .cidar_protocol import (
    CIDARBenchmarkConfig,
    CIDARBenchmarkRecord,
    run_protocol,
    protocol_report,
)
from .cidar_results import save_result


@dataclass(frozen=True)
class CIDARRunResult:
    record: CIDARBenchmarkRecord

    @property
    def valid(self) -> bool:
        return self.record.valid

    @property
    def passed(self) -> bool:
        return self.record.valid

    @property
    def samples(self) -> int:
        return self.record.samples

    @property
    def metrics(self) -> DepthMetrics:
        return DepthMetrics(
            valid=self.record.valid,
            samples=self.record.samples,
            mae=self.record.mae,
            rmse=self.record.rmse,
            bias=self.record.bias,
            relative_error=self.record.relative_error,
        )


def run_arrays(
    ground_truth,
    prediction,
    config: CIDARBenchmarkConfig,
) -> CIDARRunResult:
    record = run_protocol(
        ground_truth,
        prediction,
        config,
    )

    return CIDARRunResult(
        record=record
    )


def run_dataset(
    input_path: str | Path,
    output_path: str | Path,
    config: CIDARBenchmarkConfig,
) -> CIDARRunResult:
    samples = load_dataset(input_path)

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
    result = run_dataset(
        input_path,
        output_path,
        config,
    )

    return (
        "CIDAR EXPERIMENT\n"
        "================\n"
        + protocol_report(
            result.record
        )
    )


__all__ = [
    "CIDARRunResult",
    "run_arrays",
    "run_dataset",
    "run_and_report",
]