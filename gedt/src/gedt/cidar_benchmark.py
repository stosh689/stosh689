"""CIDAR benchmark scenarios and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class BenchmarkScenario:
    """A deterministic CIDAR sensor configuration."""

    name: str
    sensors: tuple[str, ...]
    predictions: tuple[float, ...]


@dataclass(frozen=True)
class BenchmarkResult:
    """Result for one benchmark scenario."""

    name: str
    sensors: tuple[str, ...]
    valid: bool
    samples: int
    mae: float
    rmse: float
    bias: float

    @property
    def mean_absolute_error(self) -> float:
        return self.mae

    @property
    def root_mean_square_error(self) -> float:
        return self.rmse


@dataclass(frozen=True)
class BenchmarkSuite:
    """Complete benchmark output."""

    records: tuple[BenchmarkResult, ...]

    @property
    def results(self) -> tuple[BenchmarkResult, ...]:
        return self.records

    @property
    def best(self) -> BenchmarkResult:
        return min(
            self.records,
            key=lambda record: record.rmse,
        )


def _evaluate(
    truth: Sequence[float],
    prediction: Sequence[float],
) -> tuple[bool, int, float, float, float]:
    if len(truth) != len(prediction):
        raise ValueError(
            "truth and prediction lengths must match"
        )

    if not truth:
        raise ValueError("benchmark cannot be empty")

    errors = [
        float(predicted) - float(actual)
        for actual, predicted in zip(
            truth,
            prediction,
        )
    ]

    valid = all(
        math.isfinite(error)
        for error in errors
    )

    mae = sum(
        abs(error)
        for error in errors
    ) / len(errors)

    rmse = math.sqrt(
        sum(
            error * error
            for error in errors
        ) / len(errors)
    )

    bias = sum(errors) / len(errors)

    return (
        valid,
        len(errors),
        mae,
        rmse,
        bias,
    )


def default_scenarios() -> list[BenchmarkScenario]:
    """Return the standard four CIDAR benchmark configurations."""

    return [
        BenchmarkScenario(
            name="camera",
            sensors=("camera",),
            predictions=(
                5.50,
                9.40,
                20.60,
                30.80,
                49.00,
            ),
        ),
        BenchmarkScenario(
            name="lidar",
            sensors=("lidar",),
            predictions=(
                5.10,
                10.10,
                20.20,
                29.90,
                50.10,
            ),
        ),
        BenchmarkScenario(
            name="radar",
            sensors=("radar",),
            predictions=(
                5.20,
                9.80,
                20.40,
                30.20,
                49.70,
            ),
        ),
        BenchmarkScenario(
            name="camera-lidar-radar",
            sensors=(
                "camera",
                "lidar",
                "radar",
            ),
            predictions=(
                5.02,
                9.99,
                20.03,
                30.01,
                49.98,
            ),
        ),
    ]


def run_benchmark(
    truth: Sequence[float],
    scenarios: Sequence[BenchmarkScenario] | None = None,
) -> BenchmarkSuite:
    """Run all supplied benchmark scenarios."""

    if scenarios is None:
        scenarios = default_scenarios()

    records: list[BenchmarkResult] = []

    for scenario in scenarios:
        valid, samples, mae, rmse, bias = _evaluate(
            truth,
            scenario.predictions,
        )

        records.append(
            BenchmarkResult(
                name=scenario.name,
                sensors=scenario.sensors,
                valid=valid,
                samples=samples,
                mae=mae,
                rmse=rmse,
                bias=bias,
            )
        )

    return BenchmarkSuite(
        records=tuple(records)
    )


def run_default_benchmark() -> BenchmarkSuite:
    """Run the canonical CIDAR benchmark."""

    truth = (
        5.0,
        10.0,
        20.0,
        30.0,
        50.0,
    )

    return run_benchmark(truth)


def benchmark_report(
    suite: BenchmarkSuite,
) -> str:
    """Generate a human-readable benchmark report."""

    lines = [
        "CIDAR SENSOR BENCHMARK",
        "======================",
    ]

    for result in suite.records:
        status = "PASS" if result.valid else "FAIL"

        lines.append(
            f"{result.name}: "
            f"RMSE={result.rmse:.6f} "
            f"MAE={result.mae:.6f} "
            f"Bias={result.bias:.6f} "
            f"Samples={result.samples} "
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
    "BenchmarkResult",
    "BenchmarkSuite",
    "default_scenarios",
    "run_benchmark",
    "run_default_benchmark",
    "benchmark_report",
]