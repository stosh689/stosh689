"""
GEDT v11.0 Performance Benchmark

Measures computational performance of the GEDT evaluation pipeline.

Metrics:
- execution time
- throughput
- scaling with simulation periods
- scaling with Monte Carlo trials
- reproducibility of benchmark configuration

This benchmark measures software performance. It does not measure
economic prediction accuracy.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from .master_evaluation import run_master_evaluation


BENCHMARK_NAME = "GEDT v11.0 Performance Benchmark"
BENCHMARK_VERSION = "1.0.0"

DEFAULT_PERIODS = 12
DEFAULT_TRIALS = 1000
DEFAULT_SEED = 42
DEFAULT_REPEATS = 3


def measure_execution(
    periods: int,
    trials: int,
    seed: int,
) -> dict[str, Any]:
    """Measure one complete GEDT evaluation."""

    if periods < 1:
        raise ValueError("periods must be at least 1")

    if trials < 1:
        raise ValueError("trials must be at least 1")

    start = time.perf_counter()

    result = run_master_evaluation(
        periods=periods,
        trials=trials,
        seed=seed,
    )

    elapsed = time.perf_counter() - start

    return {
        "periods": periods,
        "trials": trials,
        "seed": seed,
        "elapsed_seconds": elapsed,
        "result_generated": isinstance(result, dict),
    }


def run_performance_benchmark(
    periods: int = DEFAULT_PERIODS,
    trials: int = DEFAULT_TRIALS,
    seed: int = DEFAULT_SEED,
    repeats: int = DEFAULT_REPEATS,
) -> dict[str, Any]:
    """Run the GEDT performance benchmark."""

    if periods < 1:
        raise ValueError("periods must be at least 1")

    if trials < 1:
        raise ValueError("trials must be at least 1")

    if repeats < 1:
        raise ValueError("repeats must be at least 1")

    measurements = []

    for _ in range(repeats):
        measurements.append(
            measure_execution(
                periods=periods,
                trials=trials,
                seed=seed,
            )
        )

    times = [
        measurement["elapsed_seconds"]
        for measurement in measurements
    ]

    mean_time = statistics.mean(times)

    median_time = statistics.median(times)

    minimum_time = min(times)

    maximum_time = max(times)

    total_work = periods * trials

    throughput = (
        total_work / mean_time
        if mean_time > 0
        else 0.0
    )

    return {
        "benchmark": {
            "name": BENCHMARK_NAME,
            "version": BENCHMARK_VERSION,
        },
        "runtime": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "experiment": {
            "periods": periods,
            "trials": trials,
            "seed": seed,
            "repeats": repeats,
        },
        "measurements": measurements,
        "statistics": {
            "mean_seconds": mean_time,
            "median_seconds": median_time,
            "minimum_seconds": minimum_time,
            "maximum_seconds": maximum_time,
            "throughput_period_trial_units_per_second": throughput,
        },
    }


def run_scaling_benchmark(
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Measure scaling across progressively larger workloads."""

    workloads = [
        {
            "name": "small",
            "periods": 6,
            "trials": 100,
        },
        {
            "name": "baseline",
            "periods": 12,
            "trials": 1000,
        },
        {
            "name": "large",
            "periods": 24,
            "trials": 2500,
        },
    ]

    results = []

    for workload in workloads:
        measurement = measure_execution(
            periods=workload["periods"],
            trials=workload["trials"],
            seed=seed,
        )

        results.append(
            {
                "name": workload["name"],
                **measurement,
            }
        )

    return {
        "workloads": results,
    }


def validate_performance_benchmark(
    benchmark: dict[str, Any],
) -> None:
    """Validate a performance benchmark result."""

    required = {
        "benchmark",
        "runtime",
        "experiment",
        "measurements",
        "statistics",
    }

    missing = required - set(benchmark)

    if missing:
        raise ValueError(
            f"Missing performance sections: {sorted(missing)}"
        )

    statistics_data = benchmark["statistics"]

    for key in (
        "mean_seconds",
        "median_seconds",
        "minimum_seconds",
        "maximum_seconds",
        "throughput_period_trial_units_per_second",
    ):
        if key not in statistics_data:
            raise ValueError(
                f"Missing performance metric: {key}"
            )

    for key in (
        "mean_seconds",
        "median_seconds",
        "minimum_seconds",
        "maximum_seconds",
    ):
        value = float(statistics_data[key])

        if value < 0:
            raise ValueError(
                f"{key} cannot be negative"
            )

    if statistics_data[
        "throughput_period_trial_units_per_second"
    ] < 0:
        raise ValueError(
            "throughput cannot be negative"
        )


def validate_scaling_benchmark(
    scaling: dict[str, Any],
) -> None:
    """Validate scaling results."""

    if "workloads" not in scaling:
        raise ValueError(
            "Scaling benchmark missing workloads"
        )

    if not scaling["workloads"]:
        raise ValueError(
            "Scaling benchmark contains no workloads"
        )

    for workload in scaling["workloads"]:
        if workload["periods"] < 1:
            raise ValueError(
                "Invalid workload periods"
            )

        if workload["trials"] < 1:
            raise ValueError(
                "Invalid workload trials"
            )

        if workload["elapsed_seconds"] < 0:
            raise ValueError(
                "Invalid workload runtime"
            )


def save_performance_benchmark(
    benchmark: dict[str, Any],
    output: Path,
) -> None:
    """Save benchmark results to JSON."""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            benchmark,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def save_scaling_benchmark(
    scaling: dict[str, Any],
    output: Path,
) -> None:
    """Save scaling results to JSON."""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            scaling,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def print_summary(
    benchmark: dict[str, Any],
    scaling: dict[str, Any],
) -> None:
    """Print a human-readable performance summary."""

    statistics_data = benchmark["statistics"]

    print()
    print("=" * 80)
    print("GEDT v11.0 PERFORMANCE BENCHMARK")
    print("=" * 80)

    print()
    print("ENVIRONMENT")
    print("-" * 80)
    print(
        f"Python: {benchmark['runtime']['python_version']}"
    )
    print(
        f"Platform: {benchmark['runtime']['platform']}"
    )
    print(
        f"Machine: {benchmark['runtime']['machine']}"
    )

    print()
    print("BASELINE WORKLOAD")
    print("-" * 80)
    print(
        f"Periods: {benchmark['experiment']['periods']}"
    )
    print(
        f"Trials: {benchmark['experiment']['trials']}"
    )
    print(
        f"Repeats: {benchmark['experiment']['repeats']}"
    )

    print()
    print("PERFORMANCE")
    print("-" * 80)
    print(
        f"Mean runtime: "
        f"{statistics_data['mean_seconds']:.6f} s"
    )
    print(
        f"Median runtime: "
        f"{statistics_data['median_seconds']:.6f} s"
    )
    print(
        f"Minimum runtime: "
        f"{statistics_data['minimum_seconds']:.6f} s"
    )
    print(
        f"Maximum runtime: "
        f"{statistics_data['maximum_seconds']:.6f} s"
    )
    print(
        "Throughput: "
        f"{statistics_data['throughput_period_trial_units_per_second']:.2f}"
        " period-trial units/s"
    )

    print()
    print("SCALING")
    print("-" * 80)

    for workload in scaling["workloads"]:
        print(
            f"{workload['name']:<12}"
            f" periods={workload['periods']:<4}"
            f" trials={workload['trials']:<5}"
            f" runtime={workload['elapsed_seconds']:.6f}s"
        )

    print()
    print("=" * 80)
    print("PERFORMANCE BENCHMARK COMPLETE")
    print("=" * 80)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the GEDT v11.0 performance benchmark."
        )
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=DEFAULT_PERIODS,
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=DEFAULT_TRIALS,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=DEFAULT_REPEATS,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/gedt_v11_performance.json"
        ),
    )

    parser.add_argument(
        "--scaling-output",
        type=Path,
        default=Path(
            "results/gedt_v11_scaling.json"
        ),
    )

    args = parser.parse_args()

    try:
        benchmark = run_performance_benchmark(
            periods=args.periods,
            trials=args.trials,
            seed=args.seed,
            repeats=args.repeats,
        )

        scaling = run_scaling_benchmark(
            seed=args.seed,
        )

        validate_performance_benchmark(
            benchmark
        )

        validate_scaling_benchmark(
            scaling
        )

        save_performance_benchmark(
            benchmark,
            args.output,
        )

        save_scaling_benchmark(
            scaling,
            args.scaling_output,
        )

        print_summary(
            benchmark,
            scaling,
        )

        print(f"Saved: {args.output}")
        print(f"Saved: {args.scaling_output}")

        return 0

    except Exception as exc:
        print(
            f"PERFORMANCE BENCHMARK FAILED: {exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())