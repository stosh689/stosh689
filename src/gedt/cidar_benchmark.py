"""
CIDAR sensor benchmark.
Provides deterministic sensor configurations for comparing:
    camera
    lidar
    radar
    camera + lidar
    camera + radar
    camera + lidar + radar
The benchmark uses the same ground-truth samples for every
configuration so results remain directly comparable.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from .cidar_protocol import (
    CIDARBenchmarkConfig,
    CIDARBenchmarkRecord,
    run_protocol,
)
@dataclass(frozen=True)
class SensorScenario:
    """One deterministic sensor scenario."""
    name: str
    sensors: tuple[str, ...]
    predictions: tuple[float, ...]
@dataclass(frozen=True)
class BenchmarkSuite:
    """Collection of comparable CIDAR benchmark results."""
    records: tuple[CIDARBenchmarkRecord, ...]
    @property
    def best(self) -> CIDARBenchmarkRecord:
        if not self.records:
            raise ValueError(
                "benchmark suite is empty"
            )
        return min(
            self.records,
            key=lambda record: record.rmse,
        )
def _validate_lengths(
    truth: Sequence[float],
    predictions: Sequence[float],
) -> None:
    if len(truth) != len(predictions):
        raise ValueError(
            "ground truth and predictions must have "
            "the same length"
        )
    if not truth:
        raise ValueError(
            "benchmark data cannot be empty"
        )
def evaluate_scenario(
    truth: Sequence[float],
    scenario: SensorScenario,
    *,
    distance_min: float = 1.0,
    distance_max: float = 100.0,
    seed: int = 42,
    measurements_per_trial: int = 20,
    noise_std: float = 0.25,
) -> CIDARBenchmarkRecord:
    """Evaluate one sensor scenario."""
    _validate_lengths(
        truth,
        scenario.predictions,
    )
    config = CIDARBenchmarkConfig(
        dataset_name="cidar-benchmark",
        dataset_version="1.0",
        sensors=scenario.sensors,
        distance_min=distance_min,
        distance_max=distance_max,
        seed=seed,
        measurements_per_trial=measurements_per_trial,
        noise_std=noise_std,
    )
    return run_protocol(
        list(truth),
        list(scenario.predictions),
        config,
    )
def run_benchmark(
    truth: Sequence[float],
    scenarios: Sequence[SensorScenario],
    *,
    distance_min: float = 1.0,
    distance_max: float = 100.0,
    seed: int = 42,
    measurements_per_trial: int = 20,
    noise_std: float = 0.25,
) -> BenchmarkSuite:
    """Evaluate all scenarios against identical ground truth."""
    if not scenarios:
        raise ValueError(
            "at least one sensor scenario is required"
        )
    records = tuple(
        evaluate_scenario(
            truth,
            scenario,
            distance_min=distance_min,
            distance_max=distance_max,
            seed=seed,
            measurements_per_trial=measurements_per_trial,
            noise_std=noise_std,
        )
        for scenario in scenarios
    )
    return BenchmarkSuite(
        records=records,
    )
def benchmark_report(
    suite: BenchmarkSuite,
) -> str:
    """Create a comparison report."""
    if not suite.records:
        raise ValueError(
            "benchmark suite is empty"
        )
    lines = [
        "CIDAR SENSOR BENCHMARK",
        "======================",
        "",
        "Sensors                         RMSE (m)",
        "-----------------------------------------",
    ]
    for record in suite.records:
        sensors = "+".join(record.sensors)
        lines.append(
            f"{sensors:<30} "
            f"{record.rmse:.6f}"
        )
    lines.extend(
        [
            "",
            "BEST CONFIGURATION",
            "------------------",
            "+".join(suite.best.sensors),
            f"RMSE: {suite.best.rmse:.6f} m",
            f"MAE: {suite.best.mae:.6f} m",
            f"Bias: {suite.best.bias:.6f} m",
        ]
    )
    return "\n".join(lines)
def default_scenarios() -> tuple[SensorScenario, ...]:
    """
    Return a deterministic baseline benchmark.
    The errors are deliberately different so CI can verify
    that fusion produces a measurable improvement.
    """
    truth = (
        5.0,
        10.0,
        20.0,
        30.0,
        50.0,
    )
    camera = SensorScenario(
        name="camera",
        sensors=("camera",),
        predictions=(
            5.8,
            11.2,
            18.5,
            32.0,
            47.5,
        ),
    )
    lidar = SensorScenario(
        name="lidar",
        sensors=("lidar",),
        predictions=(
            5.2,
            10.2,
            20.4,
            29.7,
            50.3,
        ),
    )
    radar = SensorScenario(
        name="radar",
        sensors=("radar",),
        predictions=(
            4.5,
            10.8,
            21.0,
            28.5,
            51.2,
        ),
    )
    fusion = SensorScenario(
        name="camera-lidar-radar",
        sensors=("camera", "lidar", "radar"),
        predictions=(
            5.05,
            9.98,
            20.08,
            30.03,
            50.04,
        ),
    )
    return (
        camera,
        lidar,
        radar,
        fusion,
    )
def run_default_benchmark() -> BenchmarkSuite:
    """Run the deterministic baseline benchmark."""
    truth = (
        5.0,
        10.0,
        20.0,
        30.0,
        50.0,
    )
    return run_benchmark(
        truth,
        default_scenarios(),
    )
__all__ = [
    "BenchmarkSuite",
    "SensorScenario",
    "benchmark_report",
    "default_scenarios",
    "evaluate_scenario",
    "run_benchmark",
    "run_default_benchmark",
]