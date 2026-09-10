"""
GEDT v11.0
Global Economic Digital Twin

Command-line execution entry point.

This module provides one coherent execution path:

    configuration
        ↓
    economic state
        ↓
    baseline simulation
        ↓
    scenario analysis
        ↓
    algorithm evaluation
        ↓
    Monte Carlo analysis
        ↓
    reproducible report
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .algorithm_engine import (
    EconomicState,
    Scenario,
    compare_scenarios,
    engine_report,
    monte_carlo,
    run_baseline_experiment,
)


VERSION = "11.0.0"


def build_parser() -> argparse.ArgumentParser:
    """Build the GEDT command-line interface."""

    parser = argparse.ArgumentParser(
        prog="gedt",
        description=(
            "GEDT v11.0 - Global Economic Digital Twin "
            "research and simulation engine."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"GEDT {VERSION}",
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=12,
        help="Number of simulation periods.",
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=1000,
        help="Number of Monte Carlo trials.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional JSON output file.",
    )

    return parser


def create_baseline_state() -> EconomicState:
    """Create the deterministic GEDT baseline state."""

    return EconomicState(
        period=0,
        gdp=1000.0,
        inflation=0.02,
        unemployment=0.05,
    )


def create_scenarios() -> list[Scenario]:
    """Create the standard GEDT demonstration scenarios."""

    return [
        Scenario(
            name="baseline",
            demand_shock=0.0,
            supply_shock=0.0,
            policy_rate_change=0.0,
        ),
        Scenario(
            name="demand_stress",
            demand_shock=-0.10,
            supply_shock=0.0,
            policy_rate_change=0.0,
        ),
        Scenario(
            name="supply_stress",
            demand_shock=0.0,
            supply_shock=0.10,
            policy_rate_change=0.0,
        ),
        Scenario(
            name="tight_policy",
            demand_shock=0.0,
            supply_shock=0.0,
            policy_rate_change=0.02,
        ),
    ]


def run_gedt(
    periods: int = 12,
    trials: int = 1000,
    seed: int = 42,
) -> dict:
    """
    Execute the complete GEDT baseline workflow.

    Returns a machine-readable dictionary containing
    the baseline experiment, scenario analysis,
    Monte Carlo analysis, and engine report.
    """

    if periods < 1:
        raise ValueError("periods must be at least 1")

    if trials < 1:
        raise ValueError("trials must be at least 1")

    initial = create_baseline_state()
    scenarios = create_scenarios()

    baseline = run_baseline_experiment()

    scenario_results = compare_scenarios(
        initial=initial,
        scenarios=scenarios,
        periods=periods,
    )

    monte_carlo_result = monte_carlo(
        initial=initial,
        scenario=scenarios[0],
        periods=periods,
        trials=trials,
        seed=seed,
    )

    return {
        "gedt_version": VERSION,
        "seed": seed,
        "periods": periods,
        "trials": trials,
        "initial_state": asdict(initial),
        "baseline": baseline,
        "scenario_results": [
            {
                "scenario": result.scenario.name,
                "initial_gdp": result.initial_gdp,
                "final_gdp": result.final_gdp,
                "gdp_growth": result.gdp_growth,
                "average_inflation": result.average_inflation,
                "average_unemployment": result.average_unemployment,
            }
            for result in scenario_results
        ],
        "monte_carlo": asdict(monte_carlo_result),
        "engine_report": engine_report(),
    }


def print_summary(results: dict) -> None:
    """Print a concise human-readable GEDT summary."""

    print()
    print("=" * 72)
    print("GEDT v11.0 — GLOBAL ECONOMIC DIGITAL TWIN")
    print("=" * 72)

    print()
    print("Execution")
    print("-" * 72)
    print(f"Version:          {results['gedt_version']}")
    print(f"Periods:          {results['periods']}")
    print(f"Monte Carlo:      {results['trials']} trials")
    print(f"Random seed:      {results['seed']}")

    print()
    print("Initial Economic State")
    print("-" * 72)

    initial = results["initial_state"]

    print(f"GDP:              {initial['gdp']:.4f}")
    print(f"Inflation:        {initial['inflation']:.4%}")
    print(f"Unemployment:     {initial['unemployment']:.4%}")

    print()
    print("Scenario Results")
    print("-" * 72)

    for result in results["scenario_results"]:
        print()
        print(f"Scenario:         {result['scenario']}")
        print(f"Final GDP:        {result['final_gdp']:.4f}")
        print(f"GDP Growth:       {result['gdp_growth']:.4%}")
        print(
            f"Average Inflation: "
            f"{result['average_inflation']:.4%}"
        )
        print(
            f"Average Unemployment: "
            f"{result['average_unemployment']:.4%}"
        )

    print()
    print("Monte Carlo")
    print("-" * 72)

    mc = results["monte_carlo"]

    for key, value in mc.items():
        if isinstance(value, float):
            print(f"{key}: {value:.6f}")
        else:
            print(f"{key}: {value}")

    print()
    print("=" * 72)
    print("GEDT execution completed.")
    print("=" * 72)
    print()


def save_results(results: dict, output: str) -> None:
    """Save GEDT results as formatted JSON."""

    output_path = Path(output)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            results,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print(f"Results written to: {output_path}")


def main() -> int:
    """Main CLI entry point."""

    parser = build_parser()
    args = parser.parse_args()

    try:
        results = run_gedt(
            periods=args.periods,
            trials=args.trials,
            seed=args.seed,
        )

        print_summary(results)

        if args.output:
            save_results(
                results,
                args.output,
            )

        return 0

    except Exception as exc:
        print()
        print("GEDT execution failed.")
        print(f"Error: {exc}")
        print()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())