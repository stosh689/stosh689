"""
Energy Transition Twin
======================

Gate 1: Standalone energy-system simulation.

Purpose
-------
Model interactions between:
- Energy demand
- Renewable generation
- Fossil generation
- Energy storage
- Grid reliability
- Energy affordability
- Carbon emissions
- Investment
- Energy-transition scenarios

Design goals
------------
- Standard library only
- Deterministic with a seed
- Reproducible experiments
- Built-in self-tests
- Monte Carlo simulation
- Scenario comparison
- JSON/CSV export
- Suitable foundation for later integration
  into the Global Digital Twin ecosystem

Version: 1.0.0
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from dataclasses import asdict, dataclass
from typing import Dict, List


VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def percent_change(old: float, new: float) -> float:
    if abs(old) < 1e-12:
        return 0.0
    return ((new - old) / old) * 100.0


# ---------------------------------------------------------------------------
# State models
# ---------------------------------------------------------------------------

@dataclass
class EnergySystem:
    demand: float = 100.0
    renewable_capacity: float = 45.0
    fossil_capacity: float = 75.0
    storage_capacity: float = 15.0
    storage_level: float = 7.5
    grid_reliability: float = 0.96


@dataclass
class Economy:
    energy_price: float = 0.15
    energy_affordability: float = 0.80
    investment: float = 10.0
    economic_output: float = 100.0


@dataclass
class Environment:
    renewable_share: float = 0.30
    fossil_share: float = 0.70
    emissions: float = 70.0
    carbon_intensity: float = 0.70


@dataclass
class State:
    period: int
    demand: float
    renewable_generation: float
    fossil_generation: float
    storage_level: float
    renewable_share: float
    emissions: float
    carbon_intensity: float
    energy_price: float
    affordability: float
    grid_reliability: float
    economic_output: float
    investment: float
    transition_score: float


@dataclass
class ScenarioSummary:
    scenario: str
    periods: int
    initial_emissions: float
    final_emissions: float
    emissions_change_pct: float
    initial_renewable_share: float
    final_renewable_share: float
    renewable_change_pct: float
    initial_price: float
    final_price: float
    price_change_pct: float
    final_affordability: float
    final_grid_reliability: float
    final_economic_output: float
    transition_score: float


# ---------------------------------------------------------------------------
# Energy Transition Twin
# ---------------------------------------------------------------------------

class EnergyTransitionTwin:

    SCENARIOS = {
        "baseline": {
            "renewable_investment": 0.8,
            "storage_investment": 0.25,
            "efficiency": 0.003,
            "demand_growth": 0.010,
            "fossil_reduction": 0.002,
            "grid_investment": 0.20,
            "price_pressure": 0.0,
        },
        "green_transition": {
            "renewable_investment": 2.2,
            "storage_investment": 0.80,
            "efficiency": 0.010,
            "demand_growth": 0.006,
            "fossil_reduction": 0.020,
            "grid_investment": 0.55,
            "price_pressure": 0.005,
        },
        "rapid_transition": {
            "renewable_investment": 3.5,
            "storage_investment": 1.40,
            "efficiency": 0.015,
            "demand_growth": 0.003,
            "fossil_reduction": 0.040,
            "grid_investment": 0.85,
            "price_pressure": 0.015,
        },
        "energy_crisis": {
            "renewable_investment": 0.40,
            "storage_investment": 0.10,
            "efficiency": 0.001,
            "demand_growth": 0.015,
            "fossil_reduction": 0.0,
            "grid_investment": 0.05,
            "price_pressure": 0.040,
        },
        "storage_first": {
            "renewable_investment": 1.40,
            "storage_investment": 2.00,
            "efficiency": 0.008,
            "demand_growth": 0.006,
            "fossil_reduction": 0.015,
            "grid_investment": 0.70,
            "price_pressure": 0.008,
        },
    }

    def __init__(
        self,
        scenario: str = "baseline",
        seed: int = 42,
    ):
        if scenario not in self.SCENARIOS:
            raise ValueError(
                f"Unknown scenario '{scenario}'. "
                f"Available: {', '.join(self.SCENARIOS)}"
            )

        self.scenario = scenario
        self.params = self.SCENARIOS[scenario]
        self.rng = random.Random(seed)

        self.energy = EnergySystem()
        self.economy = Economy()
        self.environment = Environment()

        self.history: List[State] = []

    # -----------------------------------------------------------------------
    # Renewable generation
    # -----------------------------------------------------------------------

    def renewable_generation(self) -> float:
        variability = self.rng.uniform(0.78, 1.08)

        generation = (
            self.energy.renewable_capacity
            * variability
            * 0.90
        )

        return max(0.0, generation)

    # -----------------------------------------------------------------------
    # Demand
    # -----------------------------------------------------------------------

    def update_demand(self) -> None:
        growth = self.params["demand_growth"]

        efficiency_reduction = self.params["efficiency"]

        self.energy.demand *= (
            1.0
            + growth
            - efficiency_reduction
        )

        self.energy.demand = max(
            1.0,
            self.energy.demand
        )

    # -----------------------------------------------------------------------
    # Capacity investment
    # -----------------------------------------------------------------------

    def update_capacity(self) -> None:
        renewable_addition = (
            self.params["renewable_investment"]
            * (1.0 + self.rng.uniform(-0.08, 0.08))
        )

        storage_addition = (
            self.params["storage_investment"]
            * (1.0 + self.rng.uniform(-0.08, 0.08))
        )

        fossil_change = self.params["fossil_reduction"]

        self.energy.renewable_capacity += max(
            0.0,
            renewable_addition,
        )

        self.energy.storage_capacity += max(
            0.0,
            storage_addition,
        )

        self.energy.fossil_capacity *= (
            1.0 - fossil_change
        )

        self.energy.fossil_capacity = max(
            5.0,
            self.energy.fossil_capacity,
        )

    # -----------------------------------------------------------------------
    # Storage
    # -----------------------------------------------------------------------

    def update_storage(
        self,
        surplus: float,
        deficit: float,
    ) -> float:
        if surplus > 0:

            charging_efficiency = 0.90

            available_space = (
                self.energy.storage_capacity
                - self.energy.storage_level
            )

            charge = min(
                surplus * charging_efficiency,
                available_space,
            )

            self.energy.storage_level += charge

            return surplus - charge / charging_efficiency

        if deficit > 0:

            discharge_efficiency = 0.90

            available_energy = (
                self.energy.storage_level
                * discharge_efficiency
            )

            discharge = min(
                deficit,
                available_energy,
            )

            self.energy.storage_level -= (
                discharge / discharge_efficiency
            )

            return deficit - discharge

        return 0.0

    # -----------------------------------------------------------------------
    # Grid reliability
    # -----------------------------------------------------------------------

    def update_grid_reliability(
        self,
        unmet_demand: float,
    ) -> None:

        stress = (
            unmet_demand
            / max(self.energy.demand, 1e-9)
        )

        investment = self.params["grid_investment"]

        improvement = (
            0.002
            + investment * 0.001
        )

        penalty = stress * 0.08

        self.energy.grid_reliability = clamp(
            self.energy.grid_reliability
            + improvement
            - penalty,
            0.70,
            0.999,
        )

    # -----------------------------------------------------------------------
    # Energy price
    # -----------------------------------------------------------------------

    def update_price(
        self,
        renewable_share: float,
        unmet_demand: float,
    ) -> None:

        fossil_pressure = (
            1.0 - renewable_share
        ) * 0.020

        renewable_benefit = (
            renewable_share * 0.012
        )

        shortage_pressure = (
            unmet_demand
            / max(self.energy.demand, 1e-9)
        ) * 0.25

        scenario_pressure = self.params["price_pressure"]

        change = (
            fossil_pressure
            - renewable_benefit
            + shortage_pressure
            + scenario_pressure
        )

        self.economy.energy_price *= (
            1.0 + change
        )

        self.economy.energy_price = clamp(
            self.economy.energy_price,
            0.05,
            1.50,
        )

    # -----------------------------------------------------------------------
    # Economy
    # -----------------------------------------------------------------------

    def update_economy(
        self,
        renewable_share: float,
        unmet_demand: float,
    ) -> None:

        transition_investment = (
            self.params["renewable_investment"]
            + self.params["storage_investment"]
            + self.params["grid_investment"]
        )

        energy_cost_effect = (
            self.economy.energy_price - 0.15
        )

        reliability_effect = (
            self.energy.grid_reliability - 0.96
        )

        growth = (
            0.012
            + renewable_share * 0.004
            + transition_investment * 0.0008
            + reliability_effect * 0.10
            - energy_cost_effect * 0.04
            - unmet_demand * 0.0005
        )

        self.economy.economic_output *= (
            1.0 + growth
        )

        self.economy.investment = (
            transition_investment
        )

        self.economy.energy_affordability = clamp(
            0.80
            - max(
                0.0,
                self.economy.energy_price - 0.15
            ) * 0.60
            + renewable_share * 0.10,
            0.0,
            1.0,
        )

    # -----------------------------------------------------------------------
    # Environment
    # -----------------------------------------------------------------------

    def update_environment(
        self,
        renewable_generation: float,
        fossil_generation: float,
    ) -> None:

        total_generation = (
            renewable_generation
            + fossil_generation
        )

        if total_generation <= 0:
            renewable_share = 0.0
        else:
            renewable_share = (
                renewable_generation
                / total_generation
            )

        fossil_share = 1.0 - renewable_share

        emissions_factor = 0.90

        emissions = (
            fossil_generation
            * emissions_factor
        )

        carbon_intensity = (
            emissions
            / max(total_generation, 1e-9)
        )

        self.environment.renewable_share = clamp(
            renewable_share,
            0.0,
            1.0,
        )

        self.environment.fossil_share = clamp(
            fossil_share,
            0.0,
            1.0,
        )

        self.environment.emissions = max(
            0.0,
            emissions,
        )

        self.environment.carbon_intensity = max(
            0.0,
            carbon_intensity,
        )

    # -----------------------------------------------------------------------
    # Transition score
    # -----------------------------------------------------------------------

    def transition_score(self) -> float:

        renewable_component = (
            self.environment.renewable_share
            * 40.0
        )

        emissions_component = (
            (1.0 - clamp(
                self.environment.carbon_intensity,
                0.0,
                1.0,
            ))
            * 25.0
        )

        reliability_component = (
            self.energy.grid_reliability
            * 20.0
        )

        affordability_component = (
            self.economy.energy_affordability
            * 15.0
        )

        return clamp(
            renewable_component
            + emissions_component
            + reliability_component
            + affordability_component,
            0.0,
            100.0,
        )

    # -----------------------------------------------------------------------
    # Measure system state
    # -----------------------------------------------------------------------

    def measure(
        self,
        period: int,
        renewable_generation: float,
        fossil_generation: float,
    ) -> State:

        total_generation = (
            renewable_generation
            + fossil_generation
        )

        renewable_share = (
            renewable_generation
            / max(total_generation, 1e-9)
        )

        emissions = (
            fossil_generation * 0.90
        )

        carbon_intensity = (
            emissions
            / max(total_generation, 1e-9)
        )

        return State(
            period=period,
            demand=self.energy.demand,
            renewable_generation=renewable_generation,
            fossil_generation=fossil_generation,
            storage_level=self.energy.storage_level,
            renewable_share=renewable_share,
            emissions=emissions,
            carbon_intensity=carbon_intensity,
            energy_price=self.economy.energy_price,
            affordability=self.economy.energy_affordability,
            grid_reliability=self.energy.grid_reliability,
            economic_output=self.economy.economic_output,
            investment=self.economy.investment,
            transition_score=self.transition_score(),
        )

    # -----------------------------------------------------------------------
    # One simulation period
    # -----------------------------------------------------------------------

    def step(self, period: int) -> State:

        self.update_demand()
        self.update_capacity()

        renewable = self.renewable_generation()

        renewable_used = min(
            renewable,
            self.energy.demand,
        )

        remaining_demand = (
            self.energy.demand
            - renewable_used
        )

        renewable_surplus = max(
            0.0,
            renewable - self.energy.demand,
        )

        remaining_surplus = self.update_storage(
            surplus=renewable_surplus,
            deficit=remaining_demand,
        )

        storage_used = (
            remaining_demand
            - remaining_surplus
        )

        fossil_needed = max(
            0.0,
            remaining_surplus,
        )

        fossil_generation = min(
            fossil_needed,
            self.energy.fossil_capacity,
        )

        supplied = (
            renewable_used
            + storage_used
            + fossil_generation
        )

        unmet_demand = max(
            0.0,
            self.energy.demand - supplied,
        )

        # Storage may be charged from renewable surplus.
        # Fossil generation is only used after renewable/storage.
        self.update_grid_reliability(
            unmet_demand
        )

        total_generation = (
            renewable_used
            + fossil_generation
        )

        renewable_share = (
            renewable_used
            / max(total_generation, 1e-9)
        )

        self.update_price(
            renewable_share,
            unmet_demand,
        )

        self.update_economy(
            renewable_share,
            unmet_demand,
        )

        self.update_environment(
            renewable_used,
            fossil_generation,
        )

        state = self.measure(
            period,
            renewable_used,
            fossil_generation,
        )

        self.history.append(state)

        return state

    # -----------------------------------------------------------------------
    # Run
    # -----------------------------------------------------------------------

    def run(self, periods: int = 20) -> List[State]:

        if periods < 1:
            raise ValueError("periods must be >= 1")

        for period in range(1, periods + 1):
            self.step(period)

        return self.history

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    def summary(self) -> ScenarioSummary:

        if not self.history:
            raise RuntimeError(
                "Simulation has not been run."
            )

        first = self.history[0]
        last = self.history[-1]

        return ScenarioSummary(
            scenario=self.scenario,
            periods=len(self.history),
            initial_emissions=first.emissions,
            final_emissions=last.emissions,
            emissions_change_pct=percent_change(
                first.emissions,
                last.emissions,
            ),
            initial_renewable_share=first.renewable_share,
            final_renewable_share=last.renewable_share,
            renewable_change_pct=percent_change(
                first.renewable_share,
                last.renewable_share,
            ),
            initial_price=first.energy_price,
            final_price=last.energy_price,
            price_change_pct=percent_change(
                first.energy_price,
                last.energy_price,
            ),
            final_affordability=last.affordability,
            final_grid_reliability=last.grid_reliability,
            final_economic_output=last.economic_output,
            transition_score=last.transition_score,
        )


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

def monte_carlo(
    scenario: str,
    periods: int,
    runs: int,
    seed: int,
) -> Dict[str, float]:

    if runs < 1:
        raise ValueError("runs must be >= 1")

    final_emissions = []
    renewable_share = []
    prices = []
    affordability = []
    reliability = []
    scores = []

    for run_number in range(runs):

        model = EnergyTransitionTwin(
            scenario=scenario,
            seed=seed + run_number,
        )

        model.run(periods)

        result = model.summary()

        final_emissions.append(
            result.final_emissions
        )

        renewable_share.append(
            result.final_renewable_share
        )

        prices.append(
            result.final_price
        )

        affordability.append(
            result.final_affordability
        )

        reliability.append(
            result.final_grid_reliability
        )

        scores.append(
            result.transition_score
        )

    return {
        "runs": float(runs),
        "mean_final_emissions": safe_mean(
            final_emissions
        ),
        "mean_renewable_share": safe_mean(
            renewable_share
        ),
        "mean_final_price": safe_mean(
            prices
        ),
        "mean_affordability": safe_mean(
            affordability
        ),
        "mean_grid_reliability": safe_mean(
            reliability
        ),
        "mean_transition_score": safe_mean(
            scores
        ),
        "min_transition_score": min(scores),
        "max_transition_score": max(scores),
    }


# ---------------------------------------------------------------------------
# Scenario comparison
# ---------------------------------------------------------------------------

def compare_scenarios(
    periods: int,
    seed: int,
) -> List[ScenarioSummary]:

    results = []

    for scenario in EnergyTransitionTwin.SCENARIOS:

        model = EnergyTransitionTwin(
            scenario=scenario,
            seed=seed,
        )

        model.run(periods)

        results.append(
            model.summary()
        )

    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_summary(summary: ScenarioSummary) -> None:

    print()
    print("=" * 70)
    print("ENERGY TRANSITION TWIN")
    print("=" * 70)
    print(f"Scenario:              {summary.scenario}")
    print(f"Periods:               {summary.periods}")
    print()
    print(
        f"Renewable share:       "
        f"{summary.initial_renewable_share:.3f}"
        f" -> "
        f"{summary.final_renewable_share:.3f}"
    )
    print(
        f"Emissions:             "
        f"{summary.initial_emissions:.2f}"
        f" -> "
        f"{summary.final_emissions:.2f}"
    )
    print(
        f"Emissions change:      "
        f"{summary.emissions_change_pct:.2f}%"
    )
    print(
        f"Energy price:          "
        f"${summary.initial_price:.3f}"
        f" -> "
        f"${summary.final_price:.3f}"
    )
    print(
        f"Price change:          "
        f"{summary.price_change_pct:.2f}%"
    )
    print(
        f"Affordability:         "
        f"{summary.final_affordability:.3f}"
    )
    print(
        f"Grid reliability:      "
        f"{summary.final_grid_reliability:.4f}"
    )
    print(
        f"Economic output:       "
        f"{summary.final_economic_output:.2f}"
    )
    print(
        f"Transition score:      "
        f"{summary.transition_score:.2f}/100"
    )
    print("=" * 70)


def print_comparison(
    results: List[ScenarioSummary],
) -> None:

    print()
    print("=" * 100)
    print("SCENARIO COMPARISON")
    print("=" * 100)

    header = (
        f"{'Scenario':<20}"
        f"{'Renewable':>12}"
        f"{'Emissions':>12}"
        f"{'Price':>12}"
        f"{'Reliability':>14}"
        f"{'Score':>10}"
    )

    print(header)
    print("-" * 100)

    for result in results:

        print(
            f"{result.scenario:<20}"
            f"{result.final_renewable_share:>12.3f}"
            f"{result.final_emissions:>12.2f}"
            f"{result.final_price:>12.3f}"
            f"{result.final_grid_reliability:>14.4f}"
            f"{result.transition_score:>10.2f}"
        )

    print("=" * 100)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def save_json(
    filename: str,
    scenario: ScenarioSummary,
    history: List[State],
) -> None:

    payload = {
        "version": VERSION,
        "summary": asdict(scenario),
        "history": [
            asdict(item)
            for item in history
        ],
    }

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
        )


def save_csv(
    filename: str,
    history: List[State],
) -> None:

    if not history:
        return

    rows = [
        asdict(item)
        for item in history
    ]

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test() -> bool:

    passed = 0
    failed = 0

    print()
    print("ENERGY TRANSITION TWIN SELF TEST")
    print("=" * 70)

    # Test 1
    try:
        model = EnergyTransitionTwin(
            scenario="baseline",
            seed=42,
        )

        model.run(10)

        assert len(model.history) == 10

        print("PASS: basic simulation")
        passed += 1

    except Exception as exc:
        print(f"FAIL: basic simulation -> {exc}")
        failed += 1

    # Test 2
    try:
        model = EnergyTransitionTwin(
            scenario="green_transition",
            seed=42,
        )

        model.run(10)

        summary = model.summary()

        assert 0.0 <= summary.final_renewable_share <= 1.0
        assert summary.final_emissions >= 0.0

        print("PASS: renewable and emissions bounds")
        passed += 1

    except Exception as exc:
        print(
            f"FAIL: renewable and emissions bounds -> {exc}"
        )
        failed += 1

    # Test 3
    try:
        result = monte_carlo(
            scenario="baseline",
            periods=5,
            runs=10,
            seed=42,
        )

        assert result["runs"] == 10.0
        assert result["mean_final_emissions"] >= 0.0

        print("PASS: Monte Carlo")
        passed += 1

    except Exception as exc:
        print(f"FAIL: Monte Carlo -> {exc}")
        failed += 1

    # Test 4
    try:
        results = compare_scenarios(
            periods=5,
            seed=42,
        )

        assert len(results) == 5

        print("PASS: scenario comparison")
        passed += 1

    except Exception as exc:
        print(
            f"FAIL: scenario comparison -> {exc}"
        )
        failed += 1

    # Test 5
    try:
        model = EnergyTransitionTwin(
            scenario="rapid_transition",
            seed=123,
        )

        model.run(10)

        score = model.summary().transition_score

        assert 0.0 <= score <= 100.0

        print("PASS: transition score")
        passed += 1

    except Exception as exc:
        print(
            f"FAIL: transition score -> {exc}"
        )
        failed += 1

    # Test 6
    try:
        model_a = EnergyTransitionTwin(
            scenario="baseline",
            seed=99,
        )

        model_b = EnergyTransitionTwin(
            scenario="baseline",
            seed=99,
        )

        model_a.run(10)
        model_b.run(10)

        assert (
            model_a.summary().final_emissions
            == model_b.summary().final_emissions
        )

        print("PASS: reproducibility")
        passed += 1

    except Exception as exc:
        print(
            f"FAIL: reproducibility -> {exc}"
        )
        failed += 1

    print("=" * 70)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")

    success = failed == 0

    if success:
        print("ENERGY TRANSITION TWIN SELF TEST: PASS")
    else:
        print("ENERGY TRANSITION TWIN SELF TEST: FAIL")

    print("=" * 70)

    return success


# ---------------------------------------------------------------------------
# Command line interface
# ---------------------------------------------------------------------------

def main() -> int:

    parser = argparse.ArgumentParser(
        description="Energy Transition Twin"
    )

    parser.add_argument(
        "--scenario",
        default="baseline",
        choices=list(
            EnergyTransitionTwin.SCENARIOS.keys()
        ),
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    parser.add_argument(
        "--compare",
        action="store_true",
    )

    parser.add_argument(
        "--monte-carlo",
        action="store_true",
    )

    parser.add_argument(
        "--json",
        default="",
    )

    parser.add_argument(
        "--csv",
        default="",
    )

    args = parser.parse_args()

    if args.self_test:

        return 0 if self_test() else 1

    if args.compare:

        results = compare_scenarios(
            periods=args.periods,
            seed=args.seed,
        )

        print_comparison(results)

        return 0

    model = EnergyTransitionTwin(
        scenario=args.scenario,
        seed=args.seed,
    )

    history = model.run(
        periods=args.periods
    )

    summary = model.summary()

    print_summary(summary)

    if args.monte_carlo:

        result = monte_carlo(
            scenario=args.scenario,
            periods=args.periods,
            runs=args.runs,
            seed=args.seed,
        )

        print()
        print("MONTE CARLO")
        print("-" * 70)

        for key, value in result.items():
            print(f"{key:<30}: {value:.6f}")

    if args.json:

        save_json(
            filename=args.json,
            scenario=summary,
            history=history,
        )

        print(
            f"\nJSON saved to: {args.json}"
        )

    if args.csv:

        save_csv(
            filename=args.csv,
            history=history,
        )

        print(
            f"CSV saved to: {args.csv}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())