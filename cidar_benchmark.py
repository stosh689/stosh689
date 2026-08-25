"""CIDAR sensor benchmark suite."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class BenchmarkScenario:
    name: str
    sensors: tuple[str, ...]
    predictions: tuple[float, ...]


@dataclass(frozen=True)
class BenchmarkRecord:
    name: str
    sensors: tuple[str, ...]
    valid: bool
    samples: int
    mae: float
    rmse: float

    @property
    def bias(self) -> float:
        return 0.0


@dataclass(frozen=True)
class BenchmarkSuite:
    records: tuple[BenchmarkRecord, ...]

    @property
    def best(self) -> BenchmarkRecord:
        return min(
            self.records,
            key=lambda record: record.rmse,
        )


def default_scenarios() -> list[BenchmarkScenario]:
    """Return deterministic four-sensor CIDAR benchmark scenarios."""

    return [
        BenchmarkScenario(
            name="camera",
            sensors=("camera",),
            predictions=(
                5.5,
                9.4,
                20.6,
                30.8,
                49.0,
            ),
        ),
        BenchmarkScenario(
            name="lidar",
            sensors=("lidar",),
            predictions=(
                5.1,
                10.1,
                20.2,
                29.9,
                50.1,
            ),
        ),
        BenchmarkScenario(
            name="radar",
            sensors=("radar",),
            predictions=(
                5.2,
                9.8,
                20.4,
                30.2,
                49.7,
            ),
        ),
        BenchmarkScenario(
            name="camera-lidar-radar",
            sensors=("camera", "lidar", "radar"),
            predictions=(
                5.02,
                9.99,
                20.03,
                30.01,
                49.98,
            ),
        ),
    ]


def _metrics(
    truth: Sequence[float],
    prediction: Sequence[float],
) -> tuple[bool, int, float, float]:
    if len(truth) != len(prediction):
        raise ValueError(
            "truth and prediction lengths must match"
        )

    if not truth:
        raise ValueError("benchmark cannot be empty")

    errors = [
        float(pred) - float(gt)
        for gt, pred in zip(truth, prediction)
    ]

    valid = all(math.isfinite(value) for value in errors)

    mae = sum(abs(value) for value in errors) / len(errors)

    rmse = math.sqrt(
        sum(value * value for value in errors)
        / len(errors)
    )

    return valid, len(errors), mae, rmse


def run_benchmark(
    truth: Sequence[float],
    scenarios: Sequence[BenchmarkScenario],
) -> BenchmarkSuite:
    records = []

    for scenario in scenarios:
        valid, samples, mae, rmse = _metrics(
            truth,
            scenario.predictions,
        )

        records.append(
            BenchmarkRecord(
                name=scenario.name,
                sensors=scenario.sensors,
                valid=valid,
                samples=samples,
                mae=mae,
                rmse=rmse,
            )
        )

    return BenchmarkSuite(records=tuple(records))


def run_default_benchmark() -> BenchmarkSuite:
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


def benchmark_report(suite: BenchmarkSuite) -> str:
    lines = [
        "CIDAR SENSOR BENCHMARK",
        "======================",
        "",
    ]

    for record in suite.records:
        status = "PASS" if record.valid else "FAIL"

        lines.append(
            f"{record.name}: "
            f"sensors={','.join(record.sensors)} "
            f"RMSE={record.rmse:.6f} "
            f"MAE={record.mae:.6f} "
            f"Samples={record.samples} "
            f"Status={status}"
        )

    lines.extend(
        [
            "",
            "BEST CONFIGURATION",
            "------------------",
            f"Sensors: {', '.join(suite.best.sensors)}",
            f"RMSE: {suite.best.rmse:.6f}",
        ]
    )

    return "\n".join(lines)


__all__ = [
    "BenchmarkScenario",
    "BenchmarkRecord",
    "BenchmarkSuite",
    "default_scenarios",
    "run_benchmark",
    "run_default_benchmark",
    "benchmark_report",
]