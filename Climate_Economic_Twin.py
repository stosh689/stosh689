#!/usr/bin/env python3
"""
Climate Economic Twin
=====================

Gate 1 — Climate/Economy Simulation

Models interactions between:
    - Climate risk
    - Temperature pressure
    - Economic output
    - Productivity
    - Employment
    - Infrastructure
    - Energy transition
    - Sustainability
    - Adaptation investment
    - Climate shocks

Standard library only.

Run:
    python Climate_Economic_Twin.py

Self-test:
    python Climate_Economic_Twin.py --self-test

Compare scenarios:
    python Climate_Economic_Twin.py --compare

Save JSON:
    python Climate_Economic_Twin.py --json results.json
"""

from __future__ import annotations

import argparse
import csv
import json
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
    productivity: float = 100.0
    employment: float = 95.0
    capital: float = 100.0


@dataclass
class Climate:
    temperature_anomaly: float = 1.20
    climate_risk: float = 0.20
    environmental_health: float = 100.0


@dataclass
class Energy:
    fossil_share: float = 70.0
    renewable_share: float = 30.0
    energy_resilience: float = 80.0


@dataclass
class Adaptation:
    infrastructure: float = 80.0
    adaptation_capacity: float = 70.0
    annual_investment: float = 1.0


@dataclass
class State:
    period: int
    gdp: float
    productivity: float
    employment: float
    capital: float

    temperature_anomaly: float
    climate_risk: float
    environmental_health: float

    fossil_share: float
    renewable_share: float
    energy_resilience: float

    infrastructure: float
    adaptation_capacity: float
    annual_investment: float

    climate_damage: float
    resilience_score: float


@dataclass
class ScenarioSummary:
    scenario: str
    final_gdp: float
    gdp_change_percent: float
    final_climate_risk: float
    final_renewables: float
    final_resilience: float
    cumulative_damage: float


# ============================================================
# UTILITIES
# ============================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(maximum, value),
    )


def safe_mean(
    values: List[float],
) -> float:
    return mean(values) if values else 0.0


def percentage_change(
    initial: float,
    final: float,
) -> float:
    if initial == 0:
        return 0.0

    return ((final - initial) / initial) * 100.0


# ============================================================
# CLIMATE ECONOMIC TWIN
# ============================================================

class ClimateEconomicTwin:

    SCENARIOS = {
        "baseline",
        "green_transition",
        "climate_stress",
        "adaptation",
        "rapid_transition",
    }

    def __init__(
        self,
        scenario: str = "baseline",
        seed: int = 42,
    ):

        if scenario not in self.SCENARIOS:

            raise ValueError(
                f"Unknown scenario: {scenario}. "
                f"Choose from {sorted(self.SCENARIOS)}"
            )

        self.scenario = scenario
        self.rng = random.Random(seed)

        self.economy = Economy()
        self.climate = Climate()
        self.energy = Energy()
        self.adaptation = Adaptation()

    # --------------------------------------------------------
    # SCENARIO SETTINGS
    # --------------------------------------------------------

    def parameters(self) -> Dict[str, float]:

        params = {
            "economic_growth": 0.012,
            "emissions_reduction": 0.50,
            "renewable_growth": 0.50,
            "adaptation_growth": 0.30,
            "investment": 1.0,
        }

        if self.scenario == "green_transition":

            params.update(
                {
                    "economic_growth": 0.013,
                    "emissions_reduction": 1.00,
                    "renewable_growth": 1.20,
                    "adaptation_growth": 0.60,
                    "investment": 2.0,
                }
            )

        elif self.scenario == "climate_stress":

            params.update(
                {
                    "economic_growth": 0.005,
                    "emissions_reduction": -0.10,
                    "renewable_growth": 0.10,
                    "adaptation_growth": 0.10,
                    "investment": 0.50,
                }
            )

        elif self.scenario == "adaptation":

            params.update(
                {
                    "economic_growth": 0.010,
                    "emissions_reduction": 0.70,
                    "renewable_growth": 0.70,
                    "adaptation_growth": 1.50,
                    "investment": 3.0,
                }
            )

        elif self.scenario == "rapid_transition":

            params.update(
                {
                    "economic_growth": 0.009,
                    "emissions_reduction": 1.50,
                    "renewable_growth": 2.00,
                    "adaptation_growth": 1.00,
                    "investment": 4.0,
                }
            )

        return params

    # --------------------------------------------------------
    # CLIMATE SHOCK
    # --------------------------------------------------------

    def climate_shock(self) -> float:

        probability = (
            0.025
            + self.climate.climate_risk * 0.08
        )

        if self.scenario == "climate_stress":
            probability += 0.04

        if self.rng.random() > probability:
            return 0.0

        return clamp(
            self.rng.uniform(
                0.05,
                0.60,
            ),
            0.0,
            1.0,
        )

    # --------------------------------------------------------
    # ENERGY UPDATE
    # --------------------------------------------------------

    def update_energy(
        self,
        params: Dict[str, float],
        shock: float,
    ):

        renewable_change = (
            params["renewable_growth"]
            + self.rng.gauss(0.0, 0.10)
        )

        if shock > 0:
            renewable_change *= 0.80

        self.energy.renewable_share = clamp(
            self.energy.renewable_share
            + renewable_change,
            0.0,
            100.0,
        )

        self.energy.fossil_share = clamp(
            100.0
            - self.energy.renewable_share,
            0.0,
            100.0,
        )

        resilience_change = (
            params["renewable_growth"] * 0.25
            + params["investment"] * 0.10
            - shock * 8.0
        )

        self.energy.energy_resilience = clamp(
            self.energy.energy_resilience
            + resilience_change,
            0.0,
            100.0,
        )

    # --------------------------------------------------------
    # CLIMATE UPDATE
    # --------------------------------------------------------

    def update_climate(
        self,
        params: Dict[str, float],
        shock: float,
    ):

        emissions_effect = (
            self.energy.fossil_share
            / 100.0
            * 0.002
        )

        transition_effect = (
            self.energy.renewable_share
            / 100.0
            * 0.001
        )

        temperature_change = (
            emissions_effect
            - transition_effect
            + self.rng.gauss(0.0, 0.001)
            + shock * 0.01
        )

        self.climate.temperature_anomaly += (
            temperature_change
        )

        self.climate.temperature_anomaly = max(
            0.0,
            self.climate.temperature_anomaly,
        )

        risk_change = (
            self.climate.temperature_anomaly
            * 0.003
            + shock * 0.08
            - self.adaptation.adaptation_capacity
            * 0.0005
        )

        self.climate.climate_risk = clamp(
            self.climate.climate_risk
            + risk_change,
            0.0,
            1.0,
        )

        environmental_change = (
            -self.climate.climate_risk * 0.30
            + self.energy.renewable_share * 0.004
            - shock * 3.0
        )

        self.climate.environmental_health = clamp(
            self.climate.environmental_health
            + environmental_change,
            0.0,
            100.0,
        )

    # --------------------------------------------------------
    # ADAPTATION UPDATE
    # --------------------------------------------------------

    def update_adaptation(
        self,
        params: Dict[str, float],
        shock: float,
    ):

        investment = params["investment"]

        self.adaptation.annual_investment = investment

        infrastructure_change = (
            investment * 0.30
            + params["adaptation_growth"] * 0.10
            - shock * 8.0
        )

        self.adaptation.infrastructure = clamp(
            self.adaptation.infrastructure
            + infrastructure_change,
            0.0,
            100.0,
        )

        capacity_change = (
            params["adaptation_growth"] * 0.20
            + investment * 0.05
            - shock * 3.0
        )

        self.adaptation.adaptation_capacity = clamp(
            self.adaptation.adaptation_capacity
            + capacity_change,
            0.0,
            100.0,
        )

    # --------------------------------------------------------
    # ECONOMY UPDATE
    # --------------------------------------------------------

    def update_economy(
        self,
        params: Dict[str, float],
        shock: float,
    ):

        climate_damage = (
            self.climate.climate_risk
            * 0.008
            * (
                1.0
                - self.adaptation.adaptation_capacity
                / 200.0
            )
        )

        energy_penalty = (
            max(
                0.0,
                50.0
                - self.energy.energy_resilience,
            )
            * 0.0005
        )

        transition_cost = 0.0

        if self.scenario == "rapid_transition":
            transition_cost = 0.002

        growth = (
            params["economic_growth"]
            + self.rng.gauss(0.0, 0.003)
            - climate_damage
            - energy_penalty
            - transition_cost
            - shock * 0.08
        )

        self.economy.gdp *= max(
            0.50,
            1.0 + growth,
        )

        productivity_change = (
            params["economic_growth"] * 0.60
            + self.energy.renewable_share * 0.0001
            - climate_damage * 0.50
            - shock * 0.04
        )

        self.economy.productivity *= max(
            0.50,
            1.0 + productivity_change,
        )

        employment_change = (
            params["economic_growth"] * 2.0
            + self.rng.gauss(0.0, 0.10)
            - climate_damage * 20.0
            - shock * 4.0
        )

        self.economy.employment = clamp(
            self.economy.employment
            + employment_change,
            20.0,
            100.0,
        )

        capital_change = (
            growth * 0.70
            + params["investment"] * 0.002
            - shock * 0.04
        )

        self.economy.capital *= max(
            0.50,
            1.0 + capital_change,
        )

    # --------------------------------------------------------
    # RESILIENCE SCORE
    # --------------------------------------------------------

    def resilience_score(self) -> float:

        economic = (
            self.economy.employment * 0.15
            + min(
                self.economy.productivity,
                150.0,
            )
            / 1.5
            * 0.10
        )

        climate = (
            (1.0 - self.climate.climate_risk)
            * 100.0
            * 0.15
            + self.climate.environmental_health
            * 0.10
        )

        energy = (
            self.energy.energy_resilience
            * 0.15
            + self.energy.renewable_share
            * 0.10
        )

        adaptation = (
            self.adaptation.infrastructure
            * 0.10
            + self.adaptation.adaptation_capacity
            * 0.15
        )

        score = (
            economic
            + climate
            + energy
            + adaptation
        )

        return clamp(
            score,
            0.0,
            100.0,
        )

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    def measure(
        self,
        period: int,
        shock: float,
    ) -> State:

        climate_damage = (
            self.climate.climate_risk
            * 100.0
        )

        return State(
            period=period,

            gdp=self.economy.gdp,
            productivity=self.economy.productivity,
            employment=self.economy.employment,
            capital=self.economy.capital,

            temperature_anomaly=(
                self.climate.temperature_anomaly
            ),

            climate_risk=(
                self.climate.climate_risk
            ),

            environmental_health=(
                self.climate.environmental_health
            ),

            fossil_share=self.energy.fossil_share,
            renewable_share=self.energy.renewable_share,
            energy_resilience=self.energy.energy_resilience,

            infrastructure=(
                self.adaptation.infrastructure
            ),

            adaptation_capacity=(
                self.adaptation.adaptation_capacity
            ),

            annual_investment=(
                self.adaptation.annual_investment
            ),

            climate_damage=climate_damage,

            resilience_score=(
                self.resilience_score()
            ),
        )

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    def run(
        self,
        periods: int = 20,
    ) -> List[State]:

        if periods < 1:
            raise ValueError(
                "periods must be at least 1"
            )

        params = self.parameters()

        states = []

        for period in range(periods + 1):

            shock = 0.0

            if period > 0:

                shock = self.climate_shock()

                self.update_energy(
                    params,
                    shock,
                )

                self.update_adaptation(
                    params,
                    shock,
                )

                self.update_climate(
                    params,
                    shock,
                )

                self.update_economy(
                    params,
                    shock,
                )

            states.append(
                self.measure(
                    period,
                    shock,
                )
            )

        return states


# ============================================================
# SCENARIO SUMMARY
# ============================================================

def summarize(
    scenario: str,
    states: List[State],
) -> ScenarioSummary:

    first = states[0]
    final = states[-1]

    cumulative_damage = sum(
        state.climate_damage
        for state in states
    )

    return ScenarioSummary(
        scenario=scenario,
        final_gdp=final.gdp,
        gdp_change_percent=percentage_change(
            first.gdp,
            final.gdp,
        ),
        final_climate_risk=(
            final.climate_risk
        ),
        final_renewables=(
            final.renewable_share
        ),
        final_resilience=(
            final.resilience_score
        ),
        cumulative_damage=cumulative_damage,
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

    summaries = []

    for run_number in range(runs):

        twin = ClimateEconomicTwin(
            scenario=scenario,
            seed=seed + run_number,
        )

        states = twin.run(periods)

        summaries.append(
            summarize(
                scenario,
                states,
            )
        )

    return {
        "scenario": scenario,
        "runs": runs,
        "periods": periods,

        "mean_final_gdp": safe_mean(
            [
                item.final_gdp
                for item in summaries
            ]
        ),

        "mean_gdp_change_percent": safe_mean(
            [
                item.gdp_change_percent
                for item in summaries
            ]
        ),

        "mean_climate_risk": safe_mean(
            [
                item.final_climate_risk
                for item in summaries
            ]
        ),

        "mean_renewable_share": safe_mean(
            [
                item.final_renewables
                for item in summaries
            ]
        ),

        "mean_resilience": safe_mean(
            [
                item.final_resilience
                for item in summaries
            ]
        ),

        "mean_cumulative_damage": safe_mean(
            [
                item.cumulative_damage
                for item in summaries
            ]
        ),
    }


# ============================================================
# COMPARISON
# ============================================================

def compare(
    periods: int,
    runs: int,
    seed: int,
) -> List[Dict[str, float]]:

    scenarios = [
        "baseline",
        "green_transition",
        "climate_stress",
        "adaptation",
        "rapid_transition",
    ]

    results = []

    for index, scenario in enumerate(
        scenarios
    ):

        results.append(
            monte_carlo(
                scenario=scenario,
                periods=periods,
                runs=runs,
                seed=seed + index * 1000,
            )
        )

    return results


# ============================================================
# REPORTING
# ============================================================

def print_report(
    scenario: str,
    states: List[State],
) -> None:

    first = states[0]
    final = states[-1]

    print()
    print("=" * 75)
    print("CLIMATE ECONOMIC TWIN")
    print(f"Version: {VERSION}")
    print("=" * 75)

    print(f"Scenario: {scenario}")
    print(f"Periods:  {final.period}")

    print()
    print("ECONOMY")
    print("-" * 75)

    print(f"GDP:             {final.gdp:,.2f}")
    print(
        f"GDP change:      "
        f"{percentage_change(first.gdp, final.gdp):+.2f}%"
    )
    print(
        f"Productivity:    {final.productivity:.2f}"
    )
    print(
        f"Employment:      {final.employment:.2f}"
    )
    print(
        f"Capital:         {final.capital:.2f}"
    )

    print()
    print("CLIMATE")
    print("-" * 75)

    print(
        f"Temperature anomaly: "
        f"{final.temperature_anomaly:.3f}"
    )

    print(
        f"Climate risk:         "
        f"{final.climate_risk:.3f}"
    )

    print(
        f"Environmental health:"
        f" {final.environmental_health:.2f}"
    )

    print()
    print("ENERGY")
    print("-" * 75)

    print(
        f"Renewable share:  "
        f"{final.renewable_share:.2f}%"
    )

    print(
        f"Fossil share:     "
        f"{final.fossil_share:.2f}%"
    )

    print(
        f"Energy resilience:"
        f" {final.energy_resilience:.2f}"
    )

    print()
    print("ADAPTATION")
    print("-" * 75)

    print(
        f"Infrastructure:     "
        f"{final.infrastructure:.2f}"
    )

    print(
        f"Adaptation capacity:"
        f" {final.adaptation_capacity:.2f}"
    )

    print()
    print(
        f"RESILIENCE SCORE: "
        f"{final.resilience_score:.2f}/100"
    )

    print("=" * 75)


def print_comparison(
    results: List[Dict[str, float]],
) -> None:

    print()
    print("=" * 110)
    print("CLIMATE ECONOMIC SCENARIO COMPARISON")
    print("=" * 110)

    print(
        f"{'Scenario':<20}"
        f"{'GDP':>12}"
        f"{'GDP %':>12}"
        f"{'Climate Risk':>15}"
        f"{'Renewables':>15}"
        f"{'Resilience':>15}"
    )

    print("-" * 110)

    for item in results:

        print(
            f"{item['scenario']:<20}"
            f"{item['mean_final_gdp']:>12.2f}"
            f"{item['mean_gdp_change_percent']:>12.2f}"
            f"{item['mean_climate_risk']:>15.3f}"
            f"{item['mean_renewable_share']:>15.2f}"
            f"{item['mean_resilience']:>15.2f}"
        )

    print("=" * 110)


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
    states: List[State],
) -> None:

    rows = [
        asdict(state)
        for state in states
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
    print("CLIMATE ECONOMIC TWIN SELF TEST")
    print("=" * 65)

    # --------------------------------------------------------
    # Test 1
    # --------------------------------------------------------

    try:

        twin = ClimateEconomicTwin(
            scenario="baseline",
            seed=42,
        )

        states = twin.run(
            periods=5
        )

        assert len(states) == 6
        assert states[-1].gdp > 0

        print("PASS: basic simulation")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: basic simulation — {exc}"
        )

        failed += 1

    # --------------------------------------------------------
    # Test 2
    # --------------------------------------------------------

    try:

        twin = ClimateEconomicTwin(
            scenario="green_transition",
            seed=42,
        )

        states = twin.run(
            periods=10
        )

        for state in states:

            assert 0 <= state.climate_risk <= 1
            assert 0 <= state.renewable_share <= 100
            assert 0 <= state.fossil_share <= 100
            assert 0 <= state.resilience_score <= 100

        print("PASS: variable bounds")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: variable bounds — {exc}"
        )

        failed += 1

    # --------------------------------------------------------
    # Test 3
    # --------------------------------------------------------

    try:

        result = monte_carlo(
            scenario="baseline",
            periods=5,
            runs=10,
            seed=42,
        )

        assert result["runs"] == 10
        assert result["mean_final_gdp"] > 0

        print("PASS: Monte Carlo")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: Monte Carlo — {exc}"
        )

        failed += 1

    # --------------------------------------------------------
    # Test 4
    # --------------------------------------------------------

    try:

        results = compare(
            periods=5,
            runs=5,
            seed=42,
        )

        assert len(results) == 5

        scenario_names = {
            item["scenario"]
            for item in results
        }

        assert (
            "baseline"
            in scenario_names
        )

        assert (
            "green_transition"
            in scenario_names
        )

        print("PASS: scenario comparison")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: scenario comparison — {exc}"
        )

        failed += 1

    # --------------------------------------------------------
    # Test 5
    # --------------------------------------------------------

    try:

        twin = ClimateEconomicTwin(
            scenario="adaptation",
            seed=42,
        )

        states = twin.run(
            periods=10
        )

        assert (
            states[-1].adaptation_capacity
            > states[0].adaptation_capacity
        )

        print("PASS: adaptation dynamics")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: adaptation dynamics — {exc}"
        )

        failed += 1

    print("=" * 65)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")

    if failed == 0:

        print(
            "CLIMATE ECONOMIC TWIN SELF TEST: PASS"
        )

        return True

    print(
        "CLIMATE ECONOMIC TWIN SELF TEST: FAIL"
    )

    return False


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description="Climate Economic Twin"
    )

    parser.add_argument(
        "--scenario",
        choices=sorted(
            ClimateEconomicTwin.SCENARIOS
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
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
    )

    parser.add_argument(
        "--json",
        type=str,
        default="",
    )

    parser.add_argument(
        "--csv",
        type=str,
        default="",
    )

    args = parser.parse_args()

    if args.self_test:

        return (
            0
            if self_test()
            else 1
        )

    if args.periods < 1:

        print(
            "ERROR: periods must be at least 1."
        )

        return 1

    if args.runs < 1:

        print(
            "ERROR: runs must be at least 1."
        )

        return 1

    if args.compare:

        results = compare(
            periods=args.periods,
            runs=args.runs,
            seed=args.seed,
        )

        print_comparison(
            results
        )

        if args.json:

            save_json(
                args.json,
                results,
            )

            print(
                f"JSON saved: {args.json}"
            )

        return 0

    twin = ClimateEconomicTwin(
        scenario=args.scenario,
        seed=args.seed,
    )

    states = twin.run(
        periods=args.periods
    )

    print_report(
        args.scenario,
        states,
    )

    if args.csv:

        save_csv(
            args.csv,
            states,
        )

        print(
            f"CSV saved: {args.csv}"
        )

    if args.json:

        save_json(
            args.json,
            {
                "version": VERSION,
                "scenario": args.scenario,
                "states": [
                    asdict(state)
                    for state in states
                ],
            },
        )

        print(
            f"JSON saved: {args.json}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())