"""
GEDT v11.0 Scientific Evaluation

Transforms benchmark results into a structured evaluation of:

- baseline behaviour
- scenario response
- uncertainty
- robustness
- reproducibility
- numerical validity

This module does not claim that the model predicts the real economy.
It evaluates the behaviour and reproducibility of the implemented model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .master_evaluation import (
    run_master_evaluation,
    validate_master_evaluation,
)


EVALUATION_NAME = "GEDT v11.0 Scientific Evaluation"
EVALUATION_VERSION = "1.0.0"


def _number(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _scenario_results(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return scenario records from a master report."""
    scenarios = report.get("scenarios", {})

    if not isinstance(scenarios, dict):
        return []

    values = scenarios.get("scenarios", [])

    if not isinstance(values, list):
        return []

    return [
        item
        for item in values
        if isinstance(item, dict)
    ]


def calculate_baseline_metrics(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Calculate baseline scientific metrics."""

    deterministic = (
        report
        .get("baseline", {})
        .get("deterministic", {})
    )

    initial_gdp = _number(
        deterministic.get("initial_gdp")
    )

    final_gdp = _number(
        deterministic.get("final_gdp")
    )

    growth = _number(
        deterministic.get("gdp_growth")
    )

    average_inflation = _number(
        deterministic.get("average_inflation")
    )

    average_unemployment = _number(
        deterministic.get("average_unemployment")
    )

    absolute_change = final_gdp - initial_gdp

    if initial_gdp != 0:
        relative_change = absolute_change / initial_gdp
    else:
        relative_change = 0.0

    return {
        "initial_gdp": initial_gdp,
        "final_gdp": final_gdp,
        "absolute_gdp_change": absolute_change,
        "relative_gdp_change": relative_change,
        "reported_gdp_growth": growth,
        "average_inflation": average_inflation,
        "average_unemployment": average_unemployment,
        "gdp_positive": final_gdp > 0,
        "numerically_valid": (
            initial_gdp >= 0
            and final_gdp >= 0
        ),
    }


def calculate_scenario_metrics(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate scenario dispersion relative to baseline."""

    scenarios = _scenario_results(report)

    baseline = next(
        (
            item
            for item in scenarios
            if item.get("scenario") == "baseline"
        ),
        None,
    )

    if baseline is None and scenarios:
        baseline = scenarios[0]

    if baseline is None:
        return {
            "scenario_count": 0,
            "strongest_positive": None,
            "strongest_negative": None,
            "scenario_dispersion": 0.0,
        }

    baseline_gdp = _number(
        baseline.get("final_gdp")
    )

    comparisons = []

    for scenario in scenarios:
        final_gdp = _number(
            scenario.get("final_gdp")
        )

        difference = final_gdp - baseline_gdp

        comparisons.append(
            {
                "scenario": scenario.get(
                    "scenario",
                    "unknown",
                ),
                "final_gdp": final_gdp,
                "difference_from_baseline": difference,
            }
        )

    non_baseline = [
        item
        for item in comparisons
        if item["scenario"] != "baseline"
    ]

    if non_baseline:
        strongest_positive = max(
            non_baseline,
            key=lambda item: item[
                "difference_from_baseline"
            ],
        )

        strongest_negative = min(
            non_baseline,
            key=lambda item: item[
                "difference_from_baseline"
            ],
        )

        values = [
            item["difference_from_baseline"]
            for item in non_baseline
        ]

        dispersion = max(values) - min(values)
    else:
        strongest_positive = None
        strongest_negative = None
        dispersion = 0.0

    return {
        "scenario_count": len(scenarios),
        "baseline_final_gdp": baseline_gdp,
        "strongest_positive": strongest_positive,
        "strongest_negative": strongest_negative,
        "scenario_dispersion": dispersion,
        "comparisons": comparisons,
    }


def calculate_uncertainty_metrics(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate Monte Carlo uncertainty."""

    uncertainty = report.get(
        "uncertainty",
        {},
    )

    monte_carlo = uncertainty.get(
        "monte_carlo",
        {},
    )

    mean = _number(
        monte_carlo.get("mean_final_gdp")
    )

    std = _number(
        monte_carlo.get("std_final_gdp")
    )

    minimum = _number(
        monte_carlo.get("min_final_gdp")
    )

    maximum = _number(
        monte_carlo.get("max_final_gdp")
    )

    coefficient_of_variation = (
        abs(std / mean)
        if mean != 0
        else 0.0
    )

    return {
        "trials": int(
            _number(
                monte_carlo.get("trials")
            )
        ),
        "mean_final_gdp": mean,
        "std_final_gdp": std,
        "min_final_gdp": minimum,
        "max_final_gdp": maximum,
        "range_final_gdp": maximum - minimum,
        "coefficient_of_variation": (
            coefficient_of_variation
        ),
        "finite_results": all(
            value == value
            for value in (
                mean,
                std,
                minimum,
                maximum,
            )
        ),
    }


def calculate_reproducibility_metrics(
    periods: int,
    trials: int,
    seed: int,
) -> dict[str, Any]:
    """Verify deterministic reproducibility."""

    first = run_master_evaluation(
        periods=periods,
        trials=trials,
        seed=seed,
    )

    second = run_master_evaluation(
        periods=periods,
        trials=trials,
        seed=seed,
    )

    identical = first == second

    return {
        "same_seed": seed,
        "identical_runs": identical,
        "reproducible": identical,
    }


def build_scientific_evaluation(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Build scientific metrics from a master evaluation."""

    validate_master_evaluation(report)

    baseline = calculate_baseline_metrics(
        report
    )

    scenarios = calculate_scenario_metrics(
        report
    )

    uncertainty = calculate_uncertainty_metrics(
        report
    )

    experiment = report["experiment"]

    reproducibility = calculate_reproducibility_metrics(
        periods=int(experiment["periods"]),
        trials=int(experiment["trials"]),
        seed=int(experiment["seed"]),
    )

    checks = {
        "baseline_valid": baseline[
            "numerically_valid"
        ],
        "positive_final_gdp": baseline[
            "gdp_positive"
        ],
        "scenario_coverage": (
            scenarios["scenario_count"] >= 1
        ),
        "uncertainty_available": (
            uncertainty["trials"] >= 1
        ),
        "finite_uncertainty_results": (
            uncertainty["finite_results"]
        ),
        "reproducible": reproducibility[
            "reproducible"
        ],
    }

    passed_checks = sum(
        1
        for value in checks.values()
        if value
    )

    total_checks = len(checks)

    score = (
        passed_checks / total_checks
        if total_checks
        else 0.0
    )

    status = (
        "PASS"
        if passed_checks == total_checks
        else "REVIEW"
    )

    return {
        "evaluation": {
            "name": EVALUATION_NAME,
            "version": EVALUATION_VERSION,
        },
        "gedt": report["gedt"],
        "experiment": experiment,
        "baseline_metrics": baseline,
        "scenario_metrics": scenarios,
        "uncertainty_metrics": uncertainty,
        "reproducibility_metrics": reproducibility,
        "quality_checks": checks,
        "quality_score": score,
        "quality_percentage": score * 100.0,
        "status": status,
    }


def validate_scientific_evaluation(
    evaluation: dict[str, Any],
) -> None:
    """Validate the scientific evaluation report."""

    required = {
        "evaluation",
        "gedt",
        "experiment",
        "baseline_metrics",
        "scenario_metrics",
        "uncertainty_metrics",
        "reproducibility_metrics",
        "quality_checks",
        "quality_score",
        "quality_percentage",
        "status",
    }

    missing = required - set(evaluation)

    if missing:
        raise ValueError(
            f"Missing scientific evaluation sections: "
            f"{sorted(missing)}"
        )

    score = _number(
        evaluation["quality_score"]
    )

    if not 0.0 <= score <= 1.0:
        raise ValueError(
            "quality_score must be between 0 and 1"
        )

    percentage = _number(
        evaluation["quality_percentage"]
    )

    if not 0.0 <= percentage <= 100.0:
        raise ValueError(
            "quality_percentage must be between 0 and 100"
        )

    if evaluation["status"] not in {
        "PASS",
        "REVIEW",
    }:
        raise ValueError(
            "Invalid scientific evaluation status"
        )


def save_scientific_evaluation(
    evaluation: dict[str, Any],
    output: Path,
) -> None:
    """Save scientific evaluation to JSON."""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            evaluation,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def print_scientific_summary(
    evaluation: dict[str, Any],
) -> None:
    """Print a human-readable scientific evaluation."""

    print()
    print("=" * 80)
    print("GEDT v11.0 SCIENTIFIC EVALUATION")
    print("=" * 80)

    baseline = evaluation["baseline_metrics"]
    scenarios = evaluation["scenario_metrics"]
    uncertainty = evaluation["uncertainty_metrics"]
    reproducibility = evaluation[
        "reproducibility_metrics"
    ]

    print()
    print("BASELINE")
    print("-" * 80)
    print(
        f"Initial GDP: {baseline['initial_gdp']:.6f}"
    )
    print(
        f"Final GDP:   {baseline['final_gdp']:.6f}"
    )
    print(
        f"GDP change:  "
        f"{baseline['relative_gdp_change']:.6%}"
    )

    print()
    print("SCENARIOS")
    print("-" * 80)
    print(
        f"Scenario count: "
        f"{scenarios['scenario_count']}"
    )
    print(
        f"Scenario dispersion: "
        f"{scenarios['scenario_dispersion']:.6f}"
    )

    if scenarios["strongest_positive"]:
        print(
            "Strongest positive scenario: "
            f"{scenarios['strongest_positive']['scenario']}"
        )

    if scenarios["strongest_negative"]:
        print(
            "Strongest negative scenario: "
            f"{scenarios['strongest_negative']['scenario']}"
        )

    print()
    print("UNCERTAINTY")
    print("-" * 80)
    print(
        f"Trials: {uncertainty['trials']}"
    )
    print(
        f"Mean final GDP: "
        f"{uncertainty['mean_final_gdp']:.6f}"
    )
    print(
        f"Std final GDP: "
        f"{uncertainty['std_final_gdp']:.6f}"
    )
    print(
        f"Coefficient of variation: "
        f"{uncertainty['coefficient_of_variation']:.6%}"
    )

    print()
    print("REPRODUCIBILITY")
    print("-" * 80)
    print(
        f"Identical repeated runs: "
        f"{reproducibility['identical_runs']}"
    )

    print()
    print("QUALITY CHECKS")
    print("-" * 80)

    for name, passed in evaluation[
        "quality_checks"
    ].items():
        status = "PASS" if passed else "FAIL"
        print(
            f"[{status}] {name}"
        )

    print()
    print(
        f"Quality score: "
        f"{evaluation['quality_percentage']:.1f}%"
    )

    print(
        f"Overall status: "
        f"{evaluation['status']}"
    )

    print()
    print("=" * 80)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run GEDT v11.0 scientific evaluation."
        )
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=12,
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/gedt_v11_scientific_evaluation.json"
        ),
    )

    args = parser.parse_args()

    try:
        master = run_master_evaluation(
            periods=args.periods,
            trials=args.trials,
            seed=args.seed,
        )

        evaluation = build_scientific_evaluation(
            master
        )

        validate_scientific_evaluation(
            evaluation
        )

        save_scientific_evaluation(
            evaluation,
            args.output,
        )

        print_scientific_summary(
            evaluation
        )

        print(
            f"Saved: {args.output}"
        )

        return 0

    except Exception as exc:
        print(
            f"SCIENTIFIC EVALUATION FAILED: {exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())