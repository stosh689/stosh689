"""Reproducible CIDAR benchmarking protocol."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Sequence

from .cidar_dataset import evaluate_arrays


@dataclass(frozen=True)
class CIDARBenchmarkConfig:
    dataset_name: str
    dataset_version: str
    sensors: tuple[str, ...]
    distance_min: float
    distance_max: float
    seed: int
    measurements_per_trial: int
    noise_std: float


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


def _crlb_variance(
    noise_std: float,
    measurements: int,
) -> float:
    if noise_std <= 0:
        raise ValueError(
            "noise_std must be positive"
        )

    if measurements <= 0:
        raise ValueError(
            "measurements must be positive"
        )

    return (
        noise_std ** 2
        / measurements
    )


def run_protocol(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
    config: CIDARBenchmarkConfig,
) -> CIDARBenchmarkRecord:
    if not config.sensors:
        raise ValueError(
            "at least one sensor is required"
        )

    if config.distance_min < 0:
        raise ValueError(
            "distance_min cannot be negative"
        )

    if config.distance_max <= config.distance_min:
        raise ValueError(
            "distance_max must exceed distance_min"
        )

    if config.measurements_per_trial <= 0:
        raise ValueError(
            "measurements_per_trial must be positive"
        )

    if config.noise_std <= 0:
        raise ValueError(
            "noise_std must be positive"
        )

    metrics = evaluate_arrays(
        ground_truth,
        prediction,
    )

    crlb = _crlb_variance(
        config.noise_std,
        config.measurements_per_trial,
    )

    observed_variance = metrics.rmse ** 2

    if observed_variance <= 0:
        efficiency = 1.0
    else:
        efficiency = min(
            1.0,
            crlb / observed_variance,
        )

    return CIDARBenchmarkRecord(
        dataset_name=config.dataset_name,
        dataset_version=config.dataset_version,
        sensors=tuple(config.sensors),
        distance_min=float(config.distance_min),
        distance_max=float(config.distance_max),
        seed=int(config.seed),
        measurements_per_trial=int(
            config.measurements_per_trial
        ),
        noise_std=float(config.noise_std),
        valid=metrics.valid,
        samples=metrics.samples,
        mae=metrics.mae,
        rmse=metrics.rmse,
        bias=metrics.bias,
        relative_error=metrics.relative_error,
        crlb_variance=crlb,
        estimator_efficiency=efficiency,
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
        "============================\n"
        f"Status: {status}\n"
        f"Dataset: {record.dataset_name}\n"
        f"Version: {record.dataset_version}\n"
        f"Sensors: "
        f"{', '.join(record.sensors)}\n"
        f"Samples: {record.samples}\n"
        f"MAE: {record.mae:.6f}\n"
        f"RMSE: {record.rmse:.6f}\n"
        f"Bias: {record.bias:.6f}\n"
        f"CRLB Variance: "
        f"{record.crlb_variance:.6f}\n"
        f"Estimator Efficiency: "
        f"{record.estimator_efficiency:.6f}\n"
        f"Seed: {record.seed}\n"
    )


def compare_protocol_runs(
    records: Sequence[CIDARBenchmarkRecord],
) -> list[CIDARBenchmarkRecord]:
    return sorted(
        list(records),
        key=lambda record: (
            record.rmse,
            record.mae,
            record.sensors,
        ),
    )


__all__ = [
    "CIDARBenchmarkConfig",
    "CIDARBenchmarkRecord",
    "run_protocol",
    "protocol_report",
    "compare_protocol_runs",
] 