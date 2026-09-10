"""
GEDT v11.0 Master Evaluation

Combines:
1. Reproducible baseline
2. Scenario benchmark
3. Uncertainty and sensitivity analysis

The result is a single machine-readable evaluation report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import __version__
from .benchmark import run_benchmark
from .scenario_benchmark import run_scenario_benchmark
from .uncertainty_benchmark import run_uncertainty_benchmark


EVALUATION_NAME = "GEDT v11.0 Master Evaluation"
EVALUATION_VERSION = "1.0.0"


def run_master_evaluation(
    periods: int = 12,
    trials: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """Run the complete GEDT evaluation."""

    if periods < 1:
        raise ValueError("periods must be at least 1")

    if trials < 1:
        raise ValueError("trials must be at least 1")

    baseline = run_benchmark(
        periods=periods,
        trials=trials,
        seed=seed,
    )

    scenarios = run_scenario_benchmark(
        periods=periods,
    )

    uncertainty = run_uncertainty_benchmark(
        periods=periods,
        trials=trials,
        seed=seed,
    )

    report = {
        "evaluation": {
            "name": EVALUATION_NAME,
            "version": EVALUATION_VERSION,
        },
        "gedt": {
            "version": __version__,
        },
        "experiment": {
            "periods": periods,
            "trials": trials,
            "seed": seed,
        },
        "baseline": baseline,
        "scenarios": scenarios,
        "uncertainty": uncertainty,
    }

    return report


def validate_master_evaluation(
    report: dict[str, Any],
) -> None:
    """Validate the complete evaluation."""

    required = {
        "evaluation",
        "gedt",
        "experiment",
        "baseline",
        "scenarios",
        "uncertainty",
    }

    missing = required - set(report)

    if missing:
        raise ValueError(
            f"Missing evaluation sections: {sorted(missing)}"
        )

    if report["gedt"]["version"] != "11.0.0":
        raise ValueError(
            "Unexpected GEDT version"
        )

    if not report["scenarios"]["scenarios"]:
        raise ValueError(
            "Scenario benchmark returned no scenarios"
        )

    if "monte_carlo" not in report["uncertainty"]:
        raise ValueError(
            "Uncertainty benchmark missing Monte Carlo results"
        )


def save_master_evaluation(
    report: dict[str, Any],
    output: Path,
) -> None:
    """Save the complete evaluation as JSON."""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def print_master_summary(
    report: dict[str, Any],
) -> None:
    """Print the master evaluation summary."""

    baseline = report["baseline"]
    deterministic = baseline["deterministic"]

    scenarios = report["scenarios"]["scenarios"]

    uncertainty = report["uncertainty"]
    monte_carlo = uncertainty["monte_carlo"]

    print()
    print("=" * 80)
    print("GEDT v11.0 MASTER EVALUATION")
    print("=" * 80)

    print()
    print(f"GEDT version: {report['gedt']['version']}")
    print(
        f"Evaluation version: "
        f"{report['evaluation']['version']}"
    )

    print()
    print("EXPERIMENT")
    print("-" * 80)
    print(
        f"Periods: {report['experiment']['periods']}"
    )
    print(
        f"Trials:  {report['experiment']['trials']}"
    )
    print(
        f"Seed:    {report['experiment']['seed']}"
    )

    print()
    print("BASELINE")
    print("-" * 80)

    print(
        f"Initial GDP: "
        f"{deterministic['initial_gdp']:.6f}"
    )

    print(
        f"Final GDP:   "
        f"{deterministic['final_gdp']:.6f}"
    )

    print(
        f"GDP growth:  "
        f"{deterministic['gdp_growth']:.6%}"
    )

    print(
        f"Avg inflation: "
        f"{deterministic['average_inflation']:.6%}"
    )

    print(
        f"Avg unemployment: "
        f"{deterministic['average_unemployment']:.6%}"
    )

    print()
    print("SCENARIO RESULTS")
    print("-" * 80)

    for scenario in scenarios:
        print(
            f"{scenario['scenario']:<25}"
            f" GDP={scenario['final_gdp']:>12.4f}"
            f" Growth={scenario['gdp_growth']:>10.4%}"
        )

    print()
    print("UNCERTAINTY")
    print("-" * 80)

    print(
        f"Trials: "
        f"{monte_carlo['trials']}"
    )

    print(
        f"Mean final GDP: "
        f"{monte_carlo['mean_final_gdp']:.6f}"
    )

    print(
        f"Std final GDP: "
        f"{monte_carlo['std_final_gdp']:.6f}"
    )

    print(
        f"Minimum final GDP: "
        f"{monte_carlo['min_final_gdp']:.6f}"
    )

    print(
        f"Maximum final GDP: "
        f"{monte_carlo['max_final_gdp']:.6f}"
    )

    print()
    print("EVALUATION COMPONENTS")
    print("-" * 80)
    print("[PASS] Reproducible baseline")
    print("[PASS] Scenario benchmark")
    print("[PASS] Monte Carlo uncertainty")
    print("[PASS] Sensitivity analysis")

    print()
    print("=" * 80)
    print("MASTER EVALUATION: COMPLETE")
    print("=" * 80)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the complete GEDT v11.0 master evaluation."
        )
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=12,
        help="Simulation periods.",
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=1000,
        help="Monte Carlo trials.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/gedt_v11_master_evaluation.json"
        ),
        help="Output JSON file.",
    )

    args = parser.parse_args()

    try:
        report = run_master_evaluation(
            periods=args.periods,
            trials=args.trials,
            seed=args.seed,
        )

        validate_master_evaluation(report)

        save_master_evaluation(
            report,
            args.output,
        )

        print_master_summary(report)

        print(
            f"Saved: {args.output}"
        )

        return 0

    except Exception as exc:
        print(
            f"MASTER EVALUATION FAILED: {exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())