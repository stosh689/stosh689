"""CIDAR reproducible benchmark protocol."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .cidar_dataset import evaluate_arrays
from .cidar_monte_carlo import crlb_variance


@dataclass(frozen=True)
class CIDARBenchmarkConfig:
    dataset_name: str
    dataset_version: str
    sensors: tuple[str, ...]
    distance_min: float
    distance_max: float
    seed: int
    measurements_per_trial: int = 20
    noise_std: float = 0.25

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "sensors",
            tuple(self.sensors),
        )

        if self.distance_min < 0:
            raise ValueError(
                "distance_min cannot be negative"
            )

        if self.distance_max <= self.distance_min:
            raise ValueError(
                "distance_max must exceed distance_min"
            )

        if self.measurements_per_trial <= 0:
            raise ValueError(
                "measurements_per_trial must be positive"
            )

        if self.noise_std < 0:
            raise ValueError(
                "noise_std cannot be negative"
            )


@dataclass(frozen=True)
class CIDARBenchmarkRecord:
    dataset_name: str
    dataset_version: str
    sensors: tuple[str, ...]
    distance_min: float
    distance_max: float
    seed: int
    measurements_per_trial: int
    noise_std: float
    valid: bool
    samples: int
    mae: float
    rmse: float
    bias: float
    relative_error: float
    crlb_variance: float
    estimator_efficiency: float

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["sensors"] = list(self.sensors)
        return payload


def run_protocol(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
    config: CIDARBenchmarkConfig,
) -> CIDARBenchmarkRecord:
    """Execute a reproducible CIDAR evaluation."""

    metrics = evaluate_arrays(
        ground_truth,
        prediction,
    )

    variance = crlb_variance(
        config.noise_std,
        config.measurements_per_trial,
    )

    if variance > 0:
        efficiency = (
            variance
            / max(metrics.rmse ** 2, 1e-12)
        )
    else:
        efficiency = 1.0

    efficiency = max(
        0.0,
        min(1.0, efficiency),
    )

    return CIDARBenchmarkRecord(
        dataset_name=config.dataset_name,
        dataset_version=config.dataset_version,
        sensors=config.sensors,
        distance_min=config.distance_min,
        distance_max=config.distance_max,
        seed=config.seed,
        measurements_per_trial=config.measurements_per_trial,
        noise_std=config.noise_std,
        valid=metrics.valid,
        samples=metrics.samples,
        mae=metrics.mae,
        rmse=metrics.rmse,
        bias=metrics.bias,
        relative_error=metrics.relative_error,
        crlb_variance=variance,
        estimator_efficiency=efficiency,
    )


def compare_protocol_runs(
    records: Sequence[CIDARBenchmarkRecord],
) -> list[CIDARBenchmarkRecord]:
    """Return protocol records ordered by RMSE."""

    return sorted(
        records,
        key=lambda record: record.rmse,
    )


def protocol_report(
    record: CIDARBenchmarkRecord,
) -> str:
    status = (
        "PASS"
        if record.valid
        else "FAIL"
    )

    return (
        "CIDAR REPRODUCIBLE BENCHMARK\n"
        "===========================\n"
        f"Status: {status}\n"
        f"Dataset: {record.dataset_name}\n"
        f"Version: {record.dataset_version}\n"
        f"Sensors: {', '.join(record.sensors)}\n"
        f"Samples: {record.samples}\n"
        f"MAE: {record.mae:.6f}\n"
        f"RMSE: {record.rmse:.6f}\n"
        f"Bias: {record.bias:.6f}\n"
        f"Relative Error: "
        f"{record.relative_error:.6f}\n"
        f"CRLB Variance: "
        f"{record.crlb_variance:.6f}\n"
        f"Estimator Efficiency: "
        f"{record.estimator_efficiency:.6f}\n"
        f"Seed: {record.seed}"
    )


__all__ = [
    "CIDARBenchmarkConfig",
    "CIDARBenchmarkRecord",
    "run_protocol",
    "compare_protocol_runs",
    "protocol_report",
]