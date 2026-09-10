"""
GEDT v11.0 Reproducible Baseline Benchmark

Purpose
-------
Runs a fixed GEDT experiment using deterministic inputs and a fixed
random seed. The benchmark produces machine-readable JSON output
that can be compared across versions.

This is a research benchmark, not a forecast of the real economy.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gedt import __version__
from gedt.algorithm_engine import (
    EconomicState,
    Scenario,
    monte_carlo,
    simulate,
)


BENCHMARK_NAME = "gedt_v11_baseline"
BENCHMARK_VERSION = "1.0.0"

DEFAULT_PERIODS = 12
DEFAULT_TRIALS = 1000
DEFAULT_SEED = 42


def create_initial_state() -> EconomicState:
    """Return the fixed benchmark starting state."""
    return EconomicState(
        period=0,
        gdp=1000.0,
        inflation=0.02,
        unemployment=0.05,
    )


def create_baseline_scenario() -> Scenario:
    """Return the fixed neutral benchmark scenario."""
    return Scenario(
        name="baseline",
        demand_shock=0.0,
        supply_shock=0.0,
        policy_rate_change=0.0,
    )


def run_benchmark(
    periods: int = DEFAULT_PERIODS,
    trials: int = DEFAULT_TRIALS,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """
    Execute the reproducible GEDT baseline benchmark.
    """

    if periods < 1:
        raise ValueError("periods must be at least 1")

    if trials < 1:
        raise ValueError("trials must be at least 1")

    initial = create_initial_state()
    scenario = create_baseline_scenario()

    simulation = simulate(
        initial=initial,
        periods=periods,
        scenario=scenario,
    )

    monte_carlo_result = monte_carlo(
        initial=initial,
        scenario=scenario,
        periods=periods,
        trials=trials,
        seed=seed,
    )

    final_gdp = float(simulation.final_gdp)
    initial_gdp = float(simulation.initial_gdp)

    growth = 0.0

    if initial_gdp != 0:
        growth = (final_gdp / initial_gdp) - 1.0

    result = {
        "benchmark": {
            "name": BENCHMARK_NAME,
            "version": BENCHMARK_VERSION,
        },
        "gedt": {
            "version": __version__,
        },
        "experiment": {
            "periods": periods,
            "trials": trials,
            "seed": seed,
        },
        "initial_state": {
            "period": initial.period,
            "gdp": initial.gdp,
            "inflation": initial.inflation,
            "unemployment": initial.unemployment,
        },
        "scenario": {
            "name": scenario.name,
            "demand_shock": scenario.demand_shock,
            "supply_shock": scenario.supply_shock,
            "policy_rate_change": scenario.policy_rate_change,
        },
        "deterministic": {
            "initial_gdp": initial_gdp,
            "final_gdp": final_gdp,
            "gdp_growth": growth,
            "average_inflation": float(
                simulation.average_inflation
            ),
            "average_unemployment": float(
                simulation.average_unemployment
            ),
        },
        "monte_carlo": monte_carlo_result.to_dict(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "metadata": {
            "created_utc": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    }

    return result


def validate_result(result: dict[str, Any]) -> None:
    """Validate benchmark output for numerical safety."""

    deterministic = result["deterministic"]

    numeric_values = [
        deterministic["initial_gdp"],
        deterministic["final_gdp"],
        deterministic["gdp_growth"],
        deterministic["average_inflation"],
        deterministic["average_unemployment"],
    ]

    for value in numeric_values:
        if not math.isfinite(float(value)):
            raise ValueError(
                f"Non-finite benchmark value detected: {value}"
            )

    if deterministic["initial_gdp"] <= 0:
        raise ValueError("Initial GDP must be positive")

    if deterministic["final_gdp"] <= 0:
        raise ValueError("Final GDP must be positive")


def save_result(
    result: dict[str, Any],
    output: Path,
) -> None:
    """Save benchmark results as formatted JSON."""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def print_summary(result: dict[str, Any]) -> None:
    """Print a concise human-readable benchmark summary."""

    deterministic = result["deterministic"]
    monte_carlo_result = result["monte_carlo"]

    print()
    print("=" * 64)
    print("GEDT v11.0 REPRODUCIBLE BASELINE")
    print("=" * 64)

    print()
    print(
        f"Benchmark: "
        f"{result['benchmark']['name']}"
    )

    print(
        f"GEDT version: "
        f"{result['gedt']['version']}"
    )

    print(
        f"Periods: "
        f"{result['experiment']['periods']}"
    )

    print(
        f"Monte Carlo trials: "
        f"{result['experiment']['trials']}"
    )

    print(
        f"Seed: "
        f"{result['experiment']['seed']}"
    )

    print()
    print("DETERMINISTIC RESULTS")
    print("-" * 64)

    print(
        f"Initial GDP: "
        f"{deterministic['initial_gdp']:.6f}"
    )

    print(
        f"Final GDP: "
        f"{deterministic['final_gdp']:.6f}"
    )

    print(
        f"GDP growth: "
        f"{deterministic['gdp_growth']:.6%}"
    )

    print(
        f"Average inflation: "
        f"{deterministic['average_inflation']:.6%}"
    )

    print(
        f"Average unemployment: "
        f"{deterministic['average_unemployment']:.6%}"
    )

    print()
    print("MONTE CARLO RESULTS")
    print("-" * 64)

    for key, value in monte_carlo_result.items():
        if isinstance(value, float):
            print(f"{key}: {value:.6f}")
        else:
            print(f"{key}: {value}")

    print()
    print("=" * 64)
    print("BENCHMARK STATUS: PASS")
    print("=" * 64)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the GEDT v11.0 reproducible baseline."
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=DEFAULT_PERIODS,
        help="Number of simulation periods.",
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=DEFAULT_TRIALS,
        help="Number of Monte Carlo trials.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/gedt_v11_baseline.json"
        ),
        help="Output JSON path.",
    )

    args = parser.parse_args()

    try:
        result = run_benchmark(
            periods=args.periods,
            trials=args.trials,
            seed=args.seed,
        )

        validate_result(result)

        save_result(
            result,
            args.output,
        )

        print_summary(result)

        print(
            f"Saved benchmark: {args.output}"
        )

        return 0

    except Exception as exc:
        print()
        print("BENCHMARK STATUS: FAILED")
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())