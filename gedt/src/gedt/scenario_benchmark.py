"""
GEDT v11.0 Scenario Benchmark

Compares a neutral baseline against controlled economic scenarios.

This is a research experiment, not a real-world economic forecast.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .algorithm_engine import (
    EconomicState,
    Scenario,
    simulate,
)


BENCHMARK_NAME = "gedt_v11_scenario_benchmark"
BENCHMARK_VERSION = "1.0.0"

DEFAULT_PERIODS = 12


def initial_state() -> EconomicState:
    """Create the fixed starting economic state."""

    return EconomicState(
        period=0,
        gdp=1000.0,
        inflation=0.02,
        unemployment=0.05,
    )


def scenarios() -> list[Scenario]:
    """Return the controlled benchmark scenarios."""

    return [
        Scenario(
            name="baseline",
            demand_shock=0.0,
            supply_shock=0.0,
            policy_rate_change=0.0,
        ),
        Scenario(
            name="demand_expansion",
            demand_shock=0.20,
            supply_shock=0.0,
            policy_rate_change=0.0,
        ),
        Scenario(
            name="demand_contraction",
            demand_shock=-0.20,
            supply_shock=0.0,
            policy_rate_change=0.0,
        ),
        Scenario(
            name="supply_disruption",
            demand_shock=0.0,
            supply_shock=0.20,
            policy_rate_change=0.0,
        ),
        Scenario(
            name="supply_improvement",
            demand_shock=0.0,
            supply_shock=-0.20,
            policy_rate_change=0.0,
        ),
        Scenario(
            name="tight_policy",
            demand_shock=0.0,
            supply_shock=0.0,
            policy_rate_change=0.50,
        ),
        Scenario(
            name="accommodative_policy",
            demand_shock=0.0,
            supply_shock=0.0,
            policy_rate_change=-0.50,
        ),
    ]


def run_scenario_benchmark(
    periods: int = DEFAULT_PERIODS,
) -> dict[str, Any]:
    """Run every controlled scenario."""

    if periods < 1:
        raise ValueError("periods must be at least 1")

    initial = initial_state()

    results: list[dict[str, Any]] = []

    for scenario in scenarios():
        simulation = simulate(
            initial=initial,
            periods=periods,
            scenario=scenario,
        )

        results.append(
            {
                "scenario": scenario.name,
                "demand_shock": scenario.demand_shock,
                "supply_shock": scenario.supply_shock,
                "policy_rate_change": scenario.policy_rate_change,
                "initial_gdp": simulation.initial_gdp,
                "final_gdp": simulation.final_gdp,
                "gdp_growth": simulation.gdp_growth,
                "average_inflation": (
                    simulation.average_inflation
                ),
                "average_unemployment": (
                    simulation.average_unemployment
                ),
            }
        )

    return {
        "benchmark": {
            "name": BENCHMARK_NAME,
            "version": BENCHMARK_VERSION,
        },
        "experiment": {
            "periods": periods,
        },
        "initial_state": {
            "period": initial.period,
            "gdp": initial.gdp,
            "inflation": initial.inflation,
            "unemployment": initial.unemployment,
        },
        "scenarios": results,
    }


def calculate_differences(
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Calculate each scenario's difference from baseline."""

    scenarios_data = result["scenarios"]

    baseline = next(
        item
        for item in scenarios_data
        if item["scenario"] == "baseline"
    )

    differences = []

    for item in scenarios_data:
        differences.append(
            {
                "scenario": item["scenario"],
                "final_gdp_difference": (
                    item["final_gdp"]
                    - baseline["final_gdp"]
                ),
                "growth_difference": (
                    item["gdp_growth"]
                    - baseline["gdp_growth"]
                ),
                "inflation_difference": (
                    item["average_inflation"]
                    - baseline["average_inflation"]
                ),
                "unemployment_difference": (
                    item["average_unemployment"]
                    - baseline["average_unemployment"]
                ),
            }
        )

    return differences


def validate_result(
    result: dict[str, Any],
) -> None:
    """Validate the scenario benchmark."""

    if not result["scenarios"]:
        raise ValueError("No scenarios were produced")

    names = [
        item["scenario"]
        for item in result["scenarios"]
    ]

    if "baseline" not in names:
        raise ValueError("Baseline scenario is missing")

    for item in result["scenarios"]:
        if item["final_gdp"] <= 0:
            raise ValueError(
                f"Invalid final GDP for {item['scenario']}"
            )


def save_result(
    result: dict[str, Any],
    output: Path,
) -> None:
    """Save scenario benchmark results."""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = dict(result)

    payload["differences_from_baseline"] = (
        calculate_differences(result)
    )

    output.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def print_summary(
    result: dict[str, Any],
) -> None:
    """Print scenario comparison results."""

    differences = calculate_differences(result)

    print()
    print("=" * 78)
    print("GEDT v11.0 SCENARIO BENCHMARK")
    print("=" * 78)
    print()

    print(
        f"Periods: {result['experiment']['periods']}"
    )

    print()
    print(
        f"{'Scenario':<25}"
        f"{'Final GDP':>14}"
        f"{'GDP Growth':>14}"
        f"{'Avg Inflation':>16}"
        f"{'Avg Unemployment':>18}"
    )

    print("-" * 78)

    for item in result["scenarios"]:
        print(
            f"{item['scenario']:<25}"
            f"{item['final_gdp']:>14.4f}"
            f"{item['gdp_growth']:>13.4%}"
            f"{item['average_inflation']:>15.4%}"
            f"{item['average_unemployment']:>17.4%}"
        )

    print()
    print("DIFFERENCE FROM BASELINE")
    print("-" * 78)

    for item in differences:
        print(
            f"{item['scenario']:<25}"
            f"GDP Δ={item['final_gdp_difference']:+.4f}  "
            f"Growth Δ={item['growth_difference']:+.4%}"
        )

    print()
    print("SCENARIO BENCHMARK: PASS")
    print("=" * 78)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the GEDT v11.0 scenario benchmark."
        )
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=DEFAULT_PERIODS,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/gedt_v11_scenarios.json"
        ),
    )

    args = parser.parse_args()

    try:
        result = run_scenario_benchmark(
            periods=args.periods,
        )

        validate_result(result)

        save_result(
            result,
            args.output,
        )

        print_summary(result)

        print(
            f"Saved: {args.output}"
        )

        return 0

    except Exception as exc:
        print(
            f"SCENARIO BENCHMARK FAILED: {exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())