"""
CIDAR reproducible benchmark protocol.

Produces machine-readable experiment records containing:
- dataset name/version
- sensor configuration
- distance range
- sample count
- MAE/RMSE/bias
- maximum error
- relative error
- confidence
- CRLB variance
- estimator efficiency
- reproducibility seed
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any, Mapping, Sequence

from .cidar_dataset import DatasetMetrics, evaluate_arrays
from .cidar_monte_carlo import crlb_variance


@dataclass(frozen=True)
class CIDARBenchmarkConfig:
    """Configuration used to reproduce an experiment."""

    dataset_name: str
    dataset_version: str
    sensors: tuple[str, ...]
    distance_min: float
    distance_max: float
    seed: int
    measurements_per_trial: int
    noise_std: float

    def __post_init__(self) -> None:
        if not self.dataset_name:
            raise ValueError("dataset_name is required")

        if not self.dataset_version:
            raise ValueError("dataset_version is required")

        if not self.sensors:
            raise ValueError("at least one sensor is required")

        if self.distance_min < 0.0:
            raise ValueError(
                "distance_min must be non-negative"
            )

        if self.distance_max < self.distance_min:
            raise ValueError(
                "distance_max must be >= distance_min"
            )

        if self.measurements_per_trial < 1:
            raise ValueError(
                "measurements_per_trial must be >= 1"
            )

        if self.noise_std <= 0.0:
            raise ValueError(
                "noise_std must be greater than zero"
            )


@dataclass(frozen=True)
class CIDARBenchmarkRecord:
    """Complete machine-readable benchmark result."""

    protocol_version: str
    dataset_name: str
    dataset_version: str
    sensors: tuple[str, ...]
    distance_min: float
    distance_max: float
    samples: int
    mae: float
    rmse: float
    bias: float
    maximum_error: float
    relative_error: float
    confidence: float
    crlb_variance: float
    estimator_efficiency: float
    seed: int
    measurements_per_trial: int
    noise_std: float

    @property
    def valid(self) -> bool:
        return (
            self.protocol_version != ""
            and self.dataset_name != ""
            and self.dataset_version != ""
            and bool(self.sensors)
            and self.distance_min >= 0.0
            and self.distance_max >= self.distance_min
            and self.samples > 0
            and self.mae >= 0.0
            and self.rmse >= 0.0
            and self.maximum_error >= 0.0
            and self.relative_error >= 0.0
            and 0.0 <= self.confidence <= 1.0
            and self.crlb_variance > 0.0
            and self.estimator_efficiency >= 0.0
            and self.measurements_per_trial >= 1
            and self.noise_std > 0.0
        )

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible representation."""
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the benchmark result as JSON."""
        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
        )


def build_benchmark_record(
    config: CIDARBenchmarkConfig,
    metrics: DatasetMetrics,
    *,
    confidence: float,
) -> CIDARBenchmarkRecord:
    """
    Build a standardized benchmark record from evaluated metrics.
    """
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "confidence must be between 0 and 1"
        )

    bound = crlb_variance(
        config.noise_std,
        measurements=config.measurements_per_trial,
    )

    efficiency = (
        bound / metrics.rmse ** 2
        if metrics.rmse > 0.0
        else 0.0
    )

    return CIDARBenchmarkRecord(
        protocol_version="1.0",
        dataset_name=config.dataset_name,
        dataset_version=config.dataset_version,
        sensors=config.sensors,
        distance_min=config.distance_min,
        distance_max=config.distance_max,
        samples=metrics.samples,
        mae=metrics.mae,
        rmse=metrics.rmse,
        bias=metrics.bias,
        maximum_error=metrics.max_error,
        relative_error=metrics.relative_error,
        confidence=confidence,
        crlb_variance=bound,
        estimator_efficiency=efficiency,
        seed=config.seed,
        measurements_per_trial=config.measurements_per_trial,
        noise_std=config.noise_std,
    )


def run_protocol(
    ground_truth: Sequence[float],
    predictions: Sequence[float],
    config: CIDARBenchmarkConfig,
    *,
    confidence: float = 0.95,
) -> CIDARBenchmarkRecord:
    """
    Evaluate predictions and create a reproducible benchmark record.
    """
    if not ground_truth:
        raise ValueError(
            "ground_truth cannot be empty"
        )

    metrics = evaluate_arrays(
        ground_truth,
        predictions,
    )

    minimum = min(ground_truth)
    maximum = max(ground_truth)

    if minimum < config.distance_min:
        raise ValueError(
            "ground-truth range falls below configured "
            "distance_min"
        )

    if maximum > config.distance_max:
        raise ValueError(
            "ground-truth range exceeds configured "
            "distance_max"
        )

    return build_benchmark_record(
        config,
        metrics,
        confidence=confidence,
    )


def compare_protocol_runs(
    records: Sequence[CIDARBenchmarkRecord],
) -> dict[str, CIDARBenchmarkRecord]:
    """Index benchmark records by dataset and sensor configuration."""
    if not records:
        raise ValueError(
            "at least one benchmark record is required"
        )

    result: dict[str, CIDARBenchmarkRecord] = {}

    for record in records:
        if not record.valid:
            raise ValueError(
                "cannot compare an invalid benchmark record"
            )

        key = (
            f"{record.dataset_name}:"
            f"{record.dataset_version}:"
            f"{','.join(record.sensors)}"
        )

        result[key] = record

    return result


def protocol_report(
    record: CIDARBenchmarkRecord,
) -> str:
    """Create a concise human-readable protocol report."""
    status = "PASS" if record.valid else "FAIL"

    return (
        "CIDAR REPRODUCIBLE BENCHMARK\n"
        "============================\n"
        f"Status: {status}\n"
        f"Protocol: {record.protocol_version}\n"
        f"Dataset: {record.dataset_name}\n"
        f"Dataset Version: {record.dataset_version}\n"
        f"Sensors: {', '.join(record.sensors)}\n"
        f"Distance Range: "
        f"{record.distance_min:.3f}-"
        f"{record.distance_max:.3f} m\n"
        f"Samples: {record.samples}\n"
        f"MAE: {record.mae:.6f} m\n"
        f"RMSE: {record.rmse:.6f} m\n"
        f"Bias: {record.bias:.6f} m\n"
        f"Maximum Error: "
        f"{record.maximum_error:.6f} m\n"
        f"Relative Error: "
        f"{record.relative_error:.6f}\n"
        f"Confidence: {record.confidence:.4f}\n"
        f"CRLB Variance: "
        f"{record.crlb_variance:.8f} m²\n"
        f"Estimator Efficiency: "
        f"{record.estimator_efficiency:.6f}\n"
        f"Seed: {record.seed}\n"
        f"Measurements/Trial: "
        f"{record.measurements_per_trial}\n"
        f"Noise Std: {record.noise_std:.6f} m"
    )


__all__ = [
    "CIDARBenchmarkConfig",
    "CIDARBenchmarkRecord",
    "build_benchmark_record",
    "compare_protocol_runs",
    "protocol_report",
    "run_protocol",
]