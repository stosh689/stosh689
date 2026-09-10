"""GEDT v11 command-line execution path."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .algorithm_engine import (
    EconomicState,
    Scenario,
    compare_scenarios,
    engine_report,
    monte_carlo,
    run_baseline_experiment,
)
from .config import GEDTConfig


VERSION = "11.0.0"


def create_baseline_state(
    config: GEDTConfig,
) -> EconomicState:
    """Create the initial economic state."""

    return EconomicState(
        period=0,
        gdp=config.initial_gdp,
        inflation=config.initial_inflation,
        unemployment=config.initial_unemployment,
    )


def create_scenarios(
    config: GEDTConfig,
) -> list[Scenario]:
    """Create the standard GEDT scenario set."""

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
            supply_shock=-0.10,
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
    config: GEDTConfig | None = None,
) -> dict[str, Any]:
    """Run a complete reproducible GEDT experiment."""

    if config is None:
        config = GEDTConfig(
            periods=periods,
            trials=trials,
            seed=seed,
        )

    config.validate()

    initial_state = create_baseline_state(config)
    scenarios = create_scenarios(config)

    baseline = run_baseline_experiment(
        initial_state,
        periods=config.periods,
    )

    scenario_results = compare_scenarios(
        initial_state,
        scenarios,
        periods=config.periods,
    )

    monte_carlo_result = monte_carlo(
        initial_state,
        scenarios[0],
        periods=config.periods,
        trials=config.trials,
        seed=config.seed,
    )

    report = engine_report(
        initial_state=initial_state,
        periods=config.periods,
        trials=config.trials,
        seed=config.seed,
    )

    return {
        "gedt_version": VERSION,
        "config": config.to_dict(),
        "periods": config.periods,
        "trials": config.trials,
        "seed": config.seed,
        "initial_state": asdict(initial_state),
        "baseline": baseline,
        "scenario_results": scenario_results,
        "monte_carlo": monte_carlo_result,
        "engine_report": report,
    }


def save_results(
    results: dict[str, Any],
    path: str | Path,
) -> Path:
    """Save experiment results as JSON."""

    output_path = Path(path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            results,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return output_path


def build_parser() -> argparse.ArgumentParser:
    """Build the GEDT command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "GEDT v11 Global Economic Digital Twin"
        )
    )

    parser.add_argument(
        "--version",
        action="version",
        version=VERSION,
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
        "--config",
        type=str,
        help="Load experiment configuration from JSON.",
    )

    parser.add_argument(
        "--save-config",
        type=str,
        help="Save the active configuration to JSON.",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Save experiment results to JSON.",
    )

    return parser


def print_summary(
    results: dict[str, Any],
) -> None:
    """Print a concise experiment summary."""

    print()
    print("GEDT v11.0")
    print("=" * 40)
    print(
        f"Periods: {results['periods']}"
    )
    print(
        f"Trials:  {results['trials']}"
    )
    print(
        f"Seed:    {results['seed']}"
    )
    print()

    baseline = results["baseline"]

    if isinstance(baseline, dict):
        print("Baseline:")
        print(
            json.dumps(
                baseline,
                indent=2,
                default=str,
            )
        )

    print()
    print("Experiment completed.")
    print("=" * 40)


def main(
    argv: list[str] | None = None,
) -> int:
    """Run GEDT from the command line."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.config:
        config = GEDTConfig.load(args.config)
    else:
        config = GEDTConfig(
            periods=args.periods,
            trials=args.trials,
            seed=args.seed,
        )

    config.validate()

    if args.save_config:
        saved_config = config.save(
            args.save_config
        )
        print(
            f"Configuration saved: {saved_config}"
        )

    results = run_gedt(
        config=config,
    )

    print_summary(results)

    if args.output:
        output_path = save_results(
            results,
            args.output,
        )
        print(
            f"Results saved: {output_path}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())