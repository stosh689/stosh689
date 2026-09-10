"""
GEDT v11.0 Uncertainty and Sensitivity Benchmark

Measures how changes in economic assumptions affect model outcomes.

This is a research diagnostic. It does not establish causal
relationships or constitute an economic forecast.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from .algorithm_engine import (
    EconomicState,
    Scenario,
    monte_carlo,
    sensitivity_analysis,
)


BENCHMARK_NAME = "gedt_v11_uncertainty_sensitivity"
BENCHMARK_VERSION = "1.0.0"

DEFAULT_PERIODS = 12
DEFAULT_TRIALS = 1000
DEFAULT_SEED = 42


def create_initial_state() -> EconomicState:
    """Create the fixed benchmark starting state."""
    return EconomicState(
        period=0,
        gdp=1000.0,
        inflation=0.02,
        unemployment=0.05,
    )


def create_baseline_scenario() -> Scenario:
    """Create the neutral baseline scenario."""
    return Scenario(
        name="baseline",
        demand_shock=0.0,
        supply_shock=0.0,
        policy_rate_change=0.0,
    )


def run_uncertainty_benchmark(
    periods: int = DEFAULT_PERIODS,
    trials: int = DEFAULT_TRIALS,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """
    Run Monte Carlo uncertainty analysis and local sensitivity analysis.
    """

    if periods < 1:
        raise ValueError("periods must be at least 1")

    if trials < 1:
        raise ValueError("trials must be at least 1")

    initial = create_initial_state()
    scenario = create_baseline_scenario()

    monte_carlo_result = monte_carlo(
        initial=initial,
        scenario=scenario,
        periods=periods,
        trials=trials,
        seed=seed,
    )

    sensitivity = sensitivity_analysis(
        initial=initial,
        scenario=scenario,
        periods=periods,
    )

    return {
        "benchmark": {
            "name": BENCHMARK_NAME,
            "version": BENCHMARK_VERSION,
        },
        "experiment": {
            "periods": periods,
            "trials": trials,
            "seed": seed,
        },
        "monte_carlo": monte_carlo_result.to_dict(),
        "sensitivity": sensitivity,
    }


def validate_result(
    result: dict[str, Any],
) -> None:
    """Validate uncertainty benchmark output."""

    if "monte_carlo" not in result:
        raise ValueError("Monte Carlo results missing")

    if "sensitivity" not in result:
        raise ValueError("Sensitivity results missing")

    monte_carlo_result = result["monte_carlo"]

    for key, value in monte_carlo_result.items():
        if isinstance(value, (int, float)):
            if not math.isfinite(float(value)):
                raise ValueError(
                    f"Non-finite Monte Carlo value: {key}"
                )

    if monte_carlo_result["trials"] <= 0:
        raise ValueError("Trial count must be positive")


def save_result(
    result: dict[str, Any],
    output: Path,
) -> None:
    """Save benchmark output as JSON."""

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


def print_summary(
    result: dict[str, Any],
) -> None:
    """Print a human-readable uncertainty report."""

    mc = result["monte_carlo"]
    sensitivity = result["sensitivity"]

    print()
    print("=" * 72)
    print("GEDT v11.0 UNCERTAINTY & SENSITIVITY")
    print("=" * 72)

    print()
    print(
        f"Periods: {result['experiment']['periods']}"
    )
    print(
        f"Trials:  {result['experiment']['trials']}"
    )
    print(
        f"Seed:    {result['experiment']['seed']}"
    )

    print()
    print("MONTE CARLO")
    print("-" * 72)

    for key, value in mc.items():
        if isinstance(value, float):
            print(f"{key}: {value:.6f}")
        else:
            print(f"{key}: {value}")

    print()
    print("SENSITIVITY")
    print("-" * 72)

    if isinstance(sensitivity, dict):
        for key, value in sensitivity.items():
            if isinstance(value, float):
                print(f"{key}: {value:.6f}")
            else:
                print(f"{key}: {value}")
    else:
        print(sensitivity)

    print()
    print("UNCERTAINTY BENCHMARK: PASS")
    print("=" * 72)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run GEDT v11.0 uncertainty and sensitivity analysis."
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
        "--output",
        type=Path,
        default=Path(
            "results/gedt_v11_uncertainty.json"
        ),
    )

    args = parser.parse_args()

    try:
        result = run_uncertainty_benchmark(
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

        print(f"Saved: {args.output}")

        return 0

    except Exception as exc:
        print(
            f"UNCERTAINTY BENCHMARK FAILED: {exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())