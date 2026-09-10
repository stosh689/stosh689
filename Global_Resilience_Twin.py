#!/usr/bin/env python3
"""
Global Resilience Twin
======================

Gate 1 — Core Resilience Simulation

A standalone, dependency-free simulation framework for exploring
economic resilience under environmental and disaster stress.

No external packages are required.

Run:
    python Global_Resilience_Twin.py

Self-test:
    python Global_Resilience_Twin.py --self-test

Example:
    python Global_Resilience_Twin.py --periods 20 --runs 100
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from dataclasses import asdict, dataclass
from statistics import mean
from typing import Dict, List


VERSION = "1.0.0"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Economy:
    gdp: float = 100.0
    employment: float = 95.0
    productivity: float = 100.0
    wealth: float = 100.0
    inequality: float = 0.30
    human_capital: float = 100.0


@dataclass
class Environment:
    climate_risk: float = 0.20
    environmental_health: float = 100.0
    sustainability: float = 70.0


@dataclass
class Infrastructure:
    energy_resilience: float = 80.0
    food_resilience: float = 80.0
    infrastructure_health: float = 90.0


@dataclass
class State:
    period: int
    gdp: float
    employment: float
    productivity: float
    wealth: float
    inequality: float
    human_capital: float
    climate_risk: float
    environmental_health: float
    sustainability: float
    energy_resilience: float
    food_resilience: float
    infrastructure_health: float
    disaster: float
    resilience_score: float


@dataclass
class SimulationResult:
    scenario: str
    states: List[State]


# ============================================================
# UTILITIES
# ============================================================

def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def safe_mean(values: List[float]) -> float:
    return mean(values) if values else 0.0


def percent_change(start: float, end: float) -> float:
    if abs(start) < 1e-12:
        return 0.0
    return ((end - start) / start) * 100.0


# ============================================================
# GLOBAL RESILIENCE TWIN
# ============================================================

class GlobalResilienceTwin:
    """
    Core simulation engine.

    The model is deliberately transparent:
    every major variable can be inspected and every shock
    is represented explicitly.
    """

    SCENARIOS = {
        "baseline",
        "sustainable",
        "climate_stress",
        "disaster",
        "investment",
    }

    def __init__(
        self,
        scenario: str = "baseline",
        seed: int = 42,
    ):
        if scenario not in self.SCENARIOS:
            raise ValueError(
                f"Unknown scenario '{scenario}'. "
                f"Choose from: {sorted(self.SCENARIOS)}"
            )

        self.scenario = scenario
        self.rng = random.Random(seed)

        self.economy = Economy()
        self.environment = Environment()
        self.infrastructure = Infrastructure()

    # --------------------------------------------------------
    # SCENARIO PARAMETERS
    # --------------------------------------------------------

    def scenario_parameters(self) -> Dict[str, float]:
        params = {
            "economic_growth": 0.012,
            "productivity_growth": 0.010,
            "employment_change": 0.05,
            "sustainability_change": 0.10,
            "climate_change": 0.005,
            "infrastructure_change": 0.10,
        }

        if self.scenario == "sustainable":
            params.update(
                {
                    "economic_growth": 0.014,
                    "productivity_growth": 0.012,
                    "sustainability_change": 0.60,
                    "climate_change": -0.004,
                    "infrastructure_change": 0.35,
                }
            )

        elif self.scenario == "climate_stress":
            params.update(
                {
                    "economic_growth": 0.006,
                    "productivity_growth": 0.004,
                    "employment_change": -0.05,
                    "sustainability_change": -0.20,
                    "climate_change": 0.020,
                    "infrastructure_change": -0.15,
                }
            )

        elif self.scenario == "disaster":
            params.update(
                {
                    "economic_growth": 0.008,
                    "productivity_growth": 0.006,
                    "employment_change": -0.10,
                    "sustainability_change": -0.10,
                    "climate_change": 0.010,
                    "infrastructure_change": -0.30,
                }
            )

        elif self.scenario == "investment":
            params.update(
                {
                    "economic_growth": 0.020,
                    "productivity_growth": 0.018,
                    "employment_change": 0.15,
                    "sustainability_change": 0.40,
                    "climate_change": -0.002,
                    "infrastructure_change": 0.70,
                }
            )

        return params

    # --------------------------------------------------------
    # DISASTER MODEL
    # --------------------------------------------------------

    def generate_disaster(self) -> float:
        """
        Returns a disaster intensity from 0 to 1.

        Most periods experience little or no disruption.
        Rare events can produce substantial shocks.
        """

        probability = 0.035

        if self.scenario == "disaster":
            probability = 0.12

        elif self.scenario == "climate_stress":
            probability = 0.08

        climate_multiplier = 1.0 + (
            self.environment.climate_risk * 1.5
        )

        probability *= climate_multiplier

        if self.rng.random() > probability:
            return 0.0

        intensity = self.rng.uniform(0.10, 0.70)

        return clamp(intensity, 0.0, 1.0)

    # --------------------------------------------------------
    # ECONOMY UPDATE
    # --------------------------------------------------------

    def update_economy(
        self,
        params: Dict[str, float],
        disaster: float,
    ) -> None:

        climate_penalty = self.environment.climate_risk * 0.004
        infrastructure_penalty = (
            max(0.0, 70.0 - self.infrastructure.infrastructure_health)
            * 0.0005
        )

        growth = (
            params["economic_growth"]
            + self.rng.gauss(0.0, 0.003)
            - climate_penalty
            - infrastructure_penalty
            - disaster * 0.08
        )

        self.economy.gdp *= max(0.50, 1.0 + growth)

        productivity_growth = (
            params["productivity_growth"]
            + self.rng.gauss(0.0, 0.002)
            - disaster * 0.05
        )

        self.economy.productivity *= max(
            0.50,
            1.0 + productivity_growth,
        )

        employment_change = (
            params["employment_change"]
            + self.rng.gauss(0.0, 0.08)
            - disaster * 3.0
        )

        self.economy.employment = clamp(
            self.economy.employment + employment_change,
            20.0,
            100.0,
        )

        wealth_growth = (
            growth * 0.8
            + productivity_growth * 0.5
            - disaster * 0.04
        )

        self.economy.wealth *= max(
            0.50,
            1.0 + wealth_growth,
        )

        inequality_change = (
            0.002
            + disaster * 0.025
            - self.economy.employment * 0.00002
        )

        if self.scenario in {"sustainable", "investment"}:
            inequality_change -= 0.004

        self.economy.inequality = clamp(
            self.economy.inequality + inequality_change,
            0.05,
            0.90,
        )

        human_capital_change = (
            0.20
            + self.economy.productivity * 0.0005
            - disaster * 1.0
        )

        if self.scenario in {"sustainable", "investment"}:
            human_capital_change += 0.25

        self.economy.human_capital = clamp(
            self.economy.human_capital + human_capital_change,
            20.0,
            200.0,
        )

    # --------------------------------------------------------
    # ENVIRONMENT UPDATE
    # --------------------------------------------------------

    def update_environment(
        self,
        params: Dict[str, float],
        disaster: float,
    ) -> None:

        climate_change = (
            params["climate_change"]
            + self.rng.gauss(0.0, 0.002)
            + disaster * 0.03
        )

        self.environment.climate_risk = clamp(
            self.environment.climate_risk + climate_change,
            0.0,
            1.0,
        )

        environmental_change = (
            -self.environment.climate_risk * 0.20
            + params["sustainability_change"] * 0.15
            - disaster * 2.0
        )

        self.environment.environmental_health = clamp(
            self.environment.environmental_health
            + environmental_change,
            0.0,
            100.0,
        )

        sustainability_change = (
            params["sustainability_change"]
            + self.rng.gauss(0.0, 0.05)
            - disaster * 1.5
        )

        self.environment.sustainability = clamp(
            self.environment.sustainability
            + sustainability_change,
            0.0,
            100.0,
        )

    # --------------------------------------------------------
    # INFRASTRUCTURE UPDATE
    # --------------------------------------------------------

    def update_infrastructure(
        self,
        params: Dict[str, float],
        disaster: float,
    ) -> None:

        change = (
            params["infrastructure_change"]
            + self.rng.gauss(0.0, 0.10)
            - disaster * 15.0
        )

        self.infrastructure.infrastructure_health = clamp(
            self.infrastructure.infrastructure_health + change,
            0.0,
            100.0,
        )

        energy_change = (
            params["infrastructure_change"] * 0.6
            - disaster * 12.0
            + self.rng.gauss(0.0, 0.08)
        )

        food_change = (
            params["infrastructure_change"] * 0.5
            - disaster * 10.0
            - self.environment.climate_risk * 1.5
            + self.rng.gauss(0.0, 0.08)
        )

        self.infrastructure.energy_resilience = clamp(
            self.infrastructure.energy_resilience + energy_change,
            0.0,
            100.0,
        )

        self.infrastructure.food_resilience = clamp(
            self.infrastructure.food_resilience + food_change,
            0.0,
            100.0,
        )

    # --------------------------------------------------------
    # RESILIENCE SCORE
    # --------------------------------------------------------

    def calculate_resilience(self) -> float:
        """
        Composite resilience index.

        Higher is better.
        """

        economic = (
            self.economy.employment * 0.15
            + clamp(self.economy.productivity, 0, 150)
            / 1.5
            * 0.10
            + clamp(self.economy.human_capital, 0, 150)
            / 1.5
            * 0.10
        )

        environmental = (
            self.environment.environmental_health * 0.10
            + self.environment.sustainability * 0.10
            + (1.0 - self.environment.climate_risk) * 100.0 * 0.10
        )

        infrastructure = (
            self.infrastructure.energy_resilience * 0.10
            + self.infrastructure.food_resilience * 0.10
            + self.infrastructure.infrastructure_health * 0.10
        )

        equity = (
            (1.0 - self.economy.inequality)
            * 100.0
            * 0.05
        )

        score = (
            economic
            + environmental
            + infrastructure
            + equity
        )

        return clamp(score, 0.0, 100.0)

    # --------------------------------------------------------
    # MEASURE STATE
    # --------------------------------------------------------

    def measure(
        self,
        period: int,
        disaster: float,
    ) -> State:

        return State(
            period=period,
            gdp=self.economy.gdp,
            employment=self.economy.employment,
            productivity=self.economy.productivity,
            wealth=self.economy.wealth,
            inequality=self.economy.inequality,
            human_capital=self.economy.human_capital,
            climate_risk=self.environment.climate_risk,
            environmental_health=self.environment.environmental_health,
            sustainability=self.environment.sustainability,
            energy_resilience=self.infrastructure.energy_resilience,
            food_resilience=self.infrastructure.food_resilience,
            infrastructure_health=self.infrastructure.infrastructure_health,
            disaster=disaster,
            resilience_score=self.calculate_resilience(),
        )

    # --------------------------------------------------------
    # RUN SIMULATION
    # --------------------------------------------------------

    def run(self, periods: int = 20) -> SimulationResult:

        if periods < 1:
            raise ValueError("periods must be at least 1")

        params = self.scenario_parameters()

        states = []

        for period in range(periods + 1):

            disaster = 0.0

            if period > 0:
                disaster = self.generate_disaster()

                self.update_economy(
                    params,
                    disaster,
                )

                self.update_environment(
                    params,
                    disaster,
                )

                self.update_infrastructure(
                    params,
                    disaster,
                )

            states.append(
                self.measure(
                    period,
                    disaster,
                )
            )

        return SimulationResult(
            scenario=self.scenario,
            states=states,
        )


# ============================================================
# MONTE CARLO
# ============================================================

def monte_carlo(
    scenario: str,
    periods: int,
    runs: int,
    seed: int,
) -> Dict[str, float]:

    final_gdp = []
    final_resilience = []
    final_employment = []
    disasters = []

    for run_number in range(runs):

        twin = GlobalResilienceTwin(
            scenario=scenario,
            seed=seed + run_number,
        )

        result = twin.run(periods)

        final = result.states[-1]

        final_gdp.append(final.gdp)
        final_resilience.append(final.resilience_score)
        final_employment.append(final.employment)

        disasters.append(
            sum(
                1
                for state in result.states
                if state.disaster > 0
            )
        )

    return {
        "scenario": scenario,
        "runs": runs,
        "periods": periods,
        "mean_final_gdp": safe_mean(final_gdp),
        "mean_final_resilience": safe_mean(
            final_resilience
        ),
        "mean_final_employment": safe_mean(
            final_employment
        ),
        "mean_disasters": safe_mean(disasters),
        "minimum_resilience": min(final_resilience),
        "maximum_resilience": max(final_resilience),
    }


# ============================================================
# SCENARIO COMPARISON
# ============================================================

def compare_scenarios(
    periods: int,
    runs: int,
    seed: int,
) -> List[Dict[str, float]]:

    results = []

    for index, scenario in enumerate(
        [
            "baseline",
            "sustainable",
            "climate_stress",
            "disaster",
            "investment",
        ]
    ):

        results.append(
            monte_carlo(
                scenario=scenario,
                periods=periods,
                runs=runs,
                seed=seed + index * 10000,
            )
        )

    return results


# ============================================================
# REPORTING
# ============================================================

def print_single_report(
    result: SimulationResult,
) -> None:

    first = result.states[0]
    final = result.states[-1]

    print()
    print("=" * 70)
    print("GLOBAL RESILIENCE TWIN")
    print(f"Version: {VERSION}")
    print("=" * 70)
    print(f"Scenario:              {result.scenario}")
    print(f"Periods:               {final.period}")
    print()
    print("FINAL STATE")
    print("-" * 70)
    print(f"GDP:                   {final.gdp:,.2f}")
    print(f"GDP change:            {percent_change(first.gdp, final.gdp):+.2f}%")
    print(f"Employment:            {final.employment:.2f}")
    print(f"Productivity:          {final.productivity:.2f}")
    print(f"Wealth:                {final.wealth:.2f}")
    print(f"Inequality:            {final.inequality:.3f}")
    print(f"Human capital:         {final.human_capital:.2f}")
    print()
    print("ENVIRONMENT")
    print("-" * 70)
    print(f"Climate risk:          {final.climate_risk:.3f}")
    print(f"Environmental health:  {final.environmental_health:.2f}")
    print(f"Sustainability:        {final.sustainability:.2f}")
    print()
    print("INFRASTRUCTURE")
    print("-" * 70)
    print(f"Energy resilience:     {final.energy_resilience:.2f}")
    print(f"Food resilience:       {final.food_resilience:.2f}")
    print(f"Infrastructure health: {final.infrastructure_health:.2f}")
    print()
    print(f"RESILIENCE SCORE:      {final.resilience_score:.2f}/100")
    print("=" * 70)


def print_comparison(
    results: List[Dict[str, float]],
) -> None:

    print()
    print("=" * 100)
    print("SCENARIO COMPARISON")
    print("=" * 100)

    header = (
        f"{'Scenario':<18}"
        f"{'GDP':>12}"
        f"{'Resilience':>14}"
        f"{'Employment':>14}"
        f"{'Disasters':>12}"
    )

    print(header)
    print("-" * 100)

    for result in results:

        print(
            f"{result['scenario']:<18}"
            f"{result['mean_final_gdp']:>12.2f}"
            f"{result['mean_final_resilience']:>14.2f}"
            f"{result['mean_final_employment']:>14.2f}"
            f"{result['mean_disasters']:>12.2f}"
        )

    print("=" * 100)


# ============================================================
# FILE OUTPUT
# ============================================================

def save_json(
    filename: str,
    data,
) -> None:

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
        )


def save_csv(
    filename: str,
    result: SimulationResult,
) -> None:

    rows = [
        asdict(state)
        for state in result.states
    ]

    if not rows:
        return

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys(),
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# SELF TEST
# ============================================================

def self_test() -> bool:

    passed = 0
    failed = 0

    print()
    print("GLOBAL RESILIENCE TWIN SELF TEST")
    print("=" * 60)

    # Test 1
    try:
        twin = GlobalResilienceTwin(
            scenario="baseline",
            seed=42,
        )

        result = twin.run(periods=5)

        assert len(result.states) == 6
        print("PASS: basic simulation")
        passed += 1

    except Exception as exc:
        print(f"FAIL: basic simulation — {exc}")
        failed += 1

    # Test 2
    try:
        twin = GlobalResilienceTwin(
            scenario="sustainable",
            seed=42,
        )

        result = twin.run(periods=10)

        for state in result.states:
            assert 0.0 <= state.climate_risk <= 1.0
            assert 0.0 <= state.resilience_score <= 100.0

        print("PASS: bounds validation")
        passed += 1

    except Exception as exc:
        print(f"FAIL: bounds validation — {exc}")
        failed += 1

    # Test 3
    try:
        result = monte_carlo(
            scenario="baseline",
            periods=5,
            runs=10,
            seed=42,
        )

        assert result["runs"] == 10
        assert result["mean_final_gdp"] > 0
        assert 0 <= result["mean_final_resilience"] <= 100

        print("PASS: Monte Carlo")
        passed += 1

    except Exception as exc:
        print(f"FAIL: Monte Carlo — {exc}")
        failed += 1

    # Test 4
    try:
        results = compare_scenarios(
            periods=5,
            runs=5,
            seed=42,
        )

        assert len(results) == 5

        scenarios = {
            item["scenario"]
            for item in results
        }

        assert "baseline" in scenarios
        assert "sustainable" in scenarios
        assert "investment" in scenarios

        print("PASS: scenario comparison")
        passed += 1

    except Exception as exc:
        print(f"FAIL: scenario comparison — {exc}")
        failed += 1

    # Test 5
    try:
        score = GlobalResilienceTwin(
            seed=42
        ).calculate_resilience()

        assert 0 <= score <= 100

        print("PASS: resilience scoring")
        passed += 1

    except Exception as exc:
        print(f"FAIL: resilience scoring — {exc}")
        failed += 1

    print("=" * 60)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")

    if failed == 0:
        print("GLOBAL RESILIENCE TWIN SELF TEST: PASS")
        return True

    print("GLOBAL RESILIENCE TWIN SELF TEST: FAIL")
    return False


# ============================================================
# COMMAND LINE
# ============================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description="Global Resilience Twin"
    )

    parser.add_argument(
        "--scenario",
        choices=sorted(
            GlobalResilienceTwin.SCENARIOS
        ),
        default="baseline",
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
        "--compare",
        action="store_true",
        help="Compare all scenarios.",
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in tests.",
    )

    parser.add_argument(
        "--json",
        type=str,
        default="",
        help="Save results to JSON.",
    )

    parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="Save single simulation to CSV.",
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return 0 if self_test() else 1

    if args.periods < 1:
        print("ERROR: --periods must be at least 1.")
        return 1

    if args.runs < 1:
        print("ERROR: --runs must be at least 1.")
        return 1

    if args.compare:

        results = compare_scenarios(
            periods=args.periods,
            runs=args.runs,
            seed=args.seed,
        )

        print_comparison(results)

        if args.json:
            save_json(
                args.json,
                results,
            )

        return 0

    twin = GlobalResilienceTwin(
        scenario=args.scenario,
        seed=args.seed,
    )

    result = twin.run(
        periods=args.periods
    )

    print_single_report(result)

    if args.csv:
        save_csv(
            args.csv,
            result,
        )
        print(f"\nCSV saved: {args.csv}")

    if args.json:
        save_json(
            args.json,
            {
                "version": VERSION,
                "scenario": result.scenario,
                "states": [
                    asdict(state)
                    for state in result.states
                ],
            },
        )
        print(f"JSON saved: {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())