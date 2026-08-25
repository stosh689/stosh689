"""
CIDAR end-to-end experiment runner.

Pipeline:

dataset
   ↓
ingestion
   ↓
evaluation
   ↓
benchmark protocol
   ↓
persistent result

The runner intentionally keeps dataset-specific acquisition outside
the core pipeline. This allows CSV/JSON/JSONL exports from real-world
datasets to be evaluated consistently.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .cidar_ingest import load_dataset
from .cidar_protocol import (
    CIDARBenchmarkConfig,
    CIDARBenchmarkRecord,
    run_protocol,
)
from .cidar_results import save_result


@dataclass(frozen=True)
class CIDARRunResult:
    """Result of one complete CIDAR experiment."""

    input_path: str
    output_path: str
    record: CIDARBenchmarkRecord

    @property
    def passed(self) -> bool:
        return self.record.valid


def run_dataset(
    input_path: str | Path,
    output_path: str | Path,
    config: CIDARBenchmarkConfig,
    *,
    confidence: float = 0.95,
) -> CIDARRunResult:
    """
    Run the complete CIDAR pipeline on a dataset.

    The input dataset must contain:

        ground_truth
        prediction

    and may optionally contain:

        sample_id
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    samples = load_dataset(input_file)

    if not samples:
        raise ValueError(
            "dataset contains no valid samples"
        )

    ground_truth = [
        sample.ground_truth
        for sample in samples
    ]

    predictions = [
        sample.prediction
        for sample in samples
    ]

    record = run_protocol(
        ground_truth,
        predictions,
        config,
        confidence=confidence,
    )

    save_result(
        record,
        output_file,
    )

    return CIDARRunResult(
        input_path=str(input_file),
        output_path=str(output_file),
        record=record,
    )


def run_arrays(
    ground_truth: list[float],
    predictions: list[float],
    config: CIDARBenchmarkConfig,
) -> CIDARBenchmarkRecord:
    """Run the protocol directly on in-memory measurements."""
    return run_protocol(
        ground_truth,
        predictions,
        config,
    )


def run_and_report(
    input_path: str | Path,
    output_path: str | Path,
    config: CIDARBenchmarkConfig,
) -> str:
    """Run an experiment and return its human-readable report."""
    result = run_dataset(
        input_path,
        output_path,
        config,
    )

    record = result.record

    status = (
        "PASS"
        if result.passed
        else "FAIL"
    )

    return (
        "CIDAR EXPERIMENT\n"
        "================\n"
        f"Status: {status}\n"
        f"Input: {result.input_path}\n"
        f"Output: {result.output_path}\n"
        f"Dataset: {record.dataset_name}\n"
        f"Version: {record.dataset_version}\n"
        f"Sensors: {', '.join(record.sensors)}\n"
        f"Samples: {record.samples}\n"
        f"MAE: {record.mae:.6f} m\n"
        f"RMSE: {record.rmse:.6f} m\n"
        f"Bias: {record.bias:.6f} m\n"
        f"Relative Error: "
        f"{record.relative_error:.6f}\n"
        f"CRLB Variance: "
        f"{record.crlb_variance:.8f} m²\n"
        f"Efficiency: "
        f"{record.estimator_efficiency:.6f}"
    )


__all__ = [
    "CIDARRunResult",
    "run_and_report",
    "run_arrays",
    "run_dataset",
]