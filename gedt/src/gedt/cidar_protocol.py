"""Reproducible CIDAR benchmark protocol."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

from .cidar_dataset import evaluate_arrays
from .cidar_monte_carlo import crlb_variance


@dataclass(frozen=True)
class CIDARBenchmarkConfig:
    """Configuration for a reproducible CIDAR run."""

    dataset_name: str = "CIDAR"
    dataset_version: str = "1.0"
    sensors: tuple[str, ...] = (
        "camera",
        "lidar",
        "radar",
    )
    distance_min: float = 0.0
    distance_max: float = 10000.0
    seed: int = 42
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
    """Recorded result of a CIDAR protocol run."""

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

    @property
    def result(self) -> "CIDARBenchmarkRecord":
        return self

    def to_dict(self) -> dict:
        data = asdict(self)
        data["sensors"] = list(self.sensors)
        return data


def run_protocol(
    ground_truth: Sequence[float],
    prediction: Sequence[float],
    config: CIDARBenchmarkConfig | None = None,
) -> CIDARBenchmarkRecord:
    """Run the deterministic CIDAR evaluation protocol."""

    if config is None:
        config = CIDARBenchmarkConfig()

    metrics = evaluate_arrays(
        ground_truth,
        prediction,
    )

    bound = crlb_variance(
        config.noise_std,
        config.measurements_per_trial,
    )

    observed_variance = metrics.rmse ** 2

    if observed_variance <= 1e-15:
        efficiency = 1.0
    else:
        efficiency = (
            bound
            / observed_variance
        )

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
        measurements_per_trial=(
            config.measurements_per_trial
        ),
        noise_std=config.noise_std,
        valid=metrics.valid,
        samples=metrics.samples,
        mae=metrics.mae,
        rmse=metrics.rmse,
        bias=metrics.bias,
        relative_error=(
            metrics.relative_error
        ),
        crlb_variance=bound,
        estimator_efficiency=efficiency,
    )


def compare_protocol_runs(
    records: Sequence[CIDARBenchmarkRecord],
) -> list[CIDARBenchmarkRecord]:
    """Order protocol runs by increasing RMSE."""

    return sorted(
        records,
        key=lambda record: record.rmse,
    )


def protocol_report(
    record: CIDARBenchmarkRecord,
) -> str:
    """Create a protocol report."""

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
        f"Efficiency: "
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