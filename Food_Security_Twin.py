#!/usr/bin/env python3
"""
Food Security Twin
==================

Gate 1 — Food System Simulation

Models interactions between:

    - Food production
    - Food supply
    - Food prices
    - Household purchasing power
    - Agricultural resilience
    - Water availability
    - Climate pressure
    - Supply-chain disruption
    - Food waste
    - Emergency reserves
    - Food security

Standard library only.

Run:
    python Food_Security_Twin.py

Self-test:
    python Food_Security_Twin.py --self-test

Compare scenarios:
    python Food_Security_Twin.py --compare
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
class Agriculture:
    production: float = 100.0
    productivity: float = 100.0
    water_availability: float = 90.0
    soil_health: float = 85.0
    resilience: float = 75.0


@dataclass
class SupplyChain:
    transport_capacity: float = 90.0
    storage_capacity: float = 80.0
    disruption_risk: float = 0.15
    emergency_reserves: float = 70.0


@dataclass
class FoodMarket:
    supply: float = 100.0
    demand: float = 100.0
    price_index: float = 100.0
    food_waste: float = 12.0
    affordability: float = 80.0


@dataclass
class Climate:
    climate_pressure: float = 0.20
    extreme_weather: float = 0.10


@dataclass
class State:
    period: int

    production: float
    productivity: float
    water_availability: float
    soil_health: float
    agricultural_resilience: float

    transport_capacity: float
    storage_capacity: float
    disruption_risk: float
    emergency_reserves: float

    supply: float
    demand: float
    price_index: float
    food_waste: float
    affordability: float

    climate_pressure: float
    extreme_weather: float

    food_security_score: float
    food_shock: float


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

    return (
        (final - initial)
        / initial
        * 100.0
    )


# ============================================================
# FOOD SECURITY TWIN
# ============================================================

class FoodSecurityTwin:

    SCENARIOS = {
        "baseline",
        "climate_stress",
        "sustainable_agriculture",
        "supply_resilience",
        "food_crisis",
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
                f"Choose from {sorted(self.SCENARIOS)}"
            )

        self.scenario = scenario
        self.rng = random.Random(seed)

        self.agriculture = Agriculture()
        self.supply_chain = SupplyChain()
        self.market = FoodMarket()
        self.climate = Climate()

    # ========================================================
    # SCENARIO PARAMETERS
    # ========================================================

    def parameters(self) -> Dict[str, float]:

        params = {
            "production_growth": 0.50,
            "water_change": -0.10,
            "soil_change": 0.05,
            "transport_change": 0.10,
            "storage_change": 0.10,
            "reserve_change": 0.20,
            "climate_change": 0.005,
            "waste_change": -0.10,
            "investment": 0.50,
        }

        if self.scenario == "climate_stress":

            params.update(
                {
                    "production_growth": -0.30,
                    "water_change": -0.80,
                    "soil_change": -0.20,
                    "transport_change": -0.20,
                    "storage_change": -0.10,
                    "reserve_change": -0.20,
                    "climate_change": 0.025,
                    "waste_change": 0.10,
                    "investment": 0.20,
                }
            )

        elif self.scenario == "sustainable_agriculture":

            params.update(
                {
                    "production_growth": 0.80,
                    "water_change": 0.50,
                    "soil_change": 0.50,
                    "transport_change": 0.20,
                    "storage_change": 0.20,
                    "reserve_change": 0.50,
                    "climate_change": -0.004,
                    "waste_change": -0.50,
                    "investment": 1.50,
                }
            )

        elif self.scenario == "supply_resilience":

            params.update(
                {
                    "production_growth": 0.50,
                    "water_change": 0.00,
                    "soil_change": 0.05,
                    "transport_change": 0.80,
                    "storage_change": 1.00,
                    "reserve_change": 1.20,
                    "climate_change": 0.003,
                    "waste_change": -0.30,
                    "investment": 2.00,
                }
            )

        elif self.scenario == "food_crisis":

            params.update(
                {
                    "production_growth": -1.00,
                    "water_change": -1.50,
                    "soil_change": -0.50,
                    "transport_change": -1.00,
                    "storage_change": -0.80,
                    "reserve_change": -2.00,
                    "climate_change": 0.040,
                    "waste_change": 0.50,
                    "investment": 0.10,
                }
            )

        elif self.scenario == "investment":

            params.update(
                {
                    "production_growth": 1.20,
                    "water_change": 0.80,
                    "soil_change": 0.70,
                    "transport_change": 0.70,
                    "storage_change": 0.80,
                    "reserve_change": 1.00,
                    "climate_change": -0.002,
                    "waste_change": -0.60,
                    "investment": 3.00,
                }
            )

        return params

    # ========================================================
    # FOOD SHOCK
    # ========================================================

    def food_shock(self) -> float:

        probability = (
            0.025
            + self.climate.climate_pressure * 0.08
            + self.supply_chain.disruption_risk * 0.05
        )

        if self.scenario == "climate_stress":
            probability += 0.05

        if self.scenario == "food_crisis":
            probability += 0.12

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

    # ========================================================
    # CLIMATE
    # ========================================================

    def update_climate(
        self,
        params: Dict[str, float],
        shock: float,
    ) -> None:

        change = (
            params["climate_change"]
            + self.rng.gauss(0.0, 0.002)
            + shock * 0.015
        )

        self.climate.climate_pressure = clamp(
            self.climate.climate_pressure + change,
            0.0,
            1.0,
        )

        weather_change = (
            self.climate.climate_pressure * 0.01
            + shock * 0.05
        )

        self.climate.extreme_weather = clamp(
            self.climate.extreme_weather
            + weather_change,
            0.0,
            1.0,
        )

    # ========================================================
    # AGRICULTURE
    # ========================================================

    def update_agriculture(
        self,
        params: Dict[str, float],
        shock: float,
    ) -> None:

        water_change = (
            params["water_change"]
            - self.climate.climate_pressure * 0.30
            - shock * 10.0
            + self.rng.gauss(0.0, 0.10)
        )

        self.agriculture.water_availability = clamp(
            self.agriculture.water_availability
            + water_change,
            0.0,
            100.0,
        )

        soil_change = (
            params["soil_change"]
            - self.climate.climate_pressure * 0.05
            + self.rng.gauss(0.0, 0.03)
        )

        self.agriculture.soil_health = clamp(
            self.agriculture.soil_health
            + soil_change,
            0.0,
            100.0,
        )

        resilience_change = (
            params["investment"] * 0.15
            + params["soil_change"] * 0.10
            - shock * 8.0
        )

        self.agriculture.resilience = clamp(
            self.agriculture.resilience
            + resilience_change,
            0.0,
            100.0,
        )

        productivity_change = (
            params["production_growth"] * 0.01
            + self.agriculture.soil_health * 0.0002
            + self.agriculture.water_availability * 0.0002
            - self.climate.climate_pressure * 0.01
            - shock * 0.08
        )

        self.agriculture.productivity *= max(
            0.50,
            1.0 + productivity_change,
        )

        production_change = (
            productivity_change
            + self.agriculture.resilience * 0.0005
        )

        self.agriculture.production *= max(
            0.50,
            1.0 + production_change,
        )

    # ========================================================
    # SUPPLY CHAIN
    # ========================================================

    def update_supply_chain(
        self,
        params: Dict[str, float],
        shock: float,
    ) -> None:

        transport_change = (
            params["transport_change"]
            + params["investment"] * 0.05
            - shock * 10.0
            + self.rng.gauss(0.0, 0.10)
        )

        self.supply_chain.transport_capacity = clamp(
            self.supply_chain.transport_capacity
            + transport_change,
            0.0,
            100.0,
        )

        storage_change = (
            params["storage_change"]
            + params["investment"] * 0.05
            - shock * 8.0
            + self.rng.gauss(0.0, 0.10)
        )

        self.supply_chain.storage_capacity = clamp(
            self.supply_chain.storage_capacity
            + storage_change,
            0.0,
            100.0,
        )

        disruption_change = (
            self.climate.climate_pressure * 0.002
            + shock * 0.08
            - params["investment"] * 0.001
        )

        self.supply_chain.disruption_risk = clamp(
            self.supply_chain.disruption_risk
            + disruption_change,
            0.0,
            1.0,
        )

        reserve_change = (
            params["reserve_change"]
            + params["investment"] * 0.10
            - shock * 15.0
        )

        self.supply_chain.emergency_reserves = clamp(
            self.supply_chain.emergency_reserves
            + reserve_change,
            0.0,
            100.0,
        )

    # ========================================================
    # MARKET
    # ========================================================

    def update_market(
        self,
        params: Dict[str, float],
        shock: float,
    ) -> None:

        supply_effect = (
            self.agriculture.production
            * 0.60
            + self.supply_chain.transport_capacity
            * 0.20
            + self.supply_chain.storage_capacity
            * 0.20
        ) / 100.0

        reserve_buffer = (
            self.supply_chain.emergency_reserves
            / 100.0
            * 0.20
        )

        self.market.supply = max(
            1.0,
            100.0
            * supply_effect
            + reserve_buffer * 100.0
            - shock * 30.0,
        )

        demand_change = (
            0.20
            + self.rng.gauss(0.0, 0.05)
        )

        self.market.demand = clamp(
            self.market.demand
            + demand_change,
            50.0,
            150.0,
        )

        shortage = (
            self.market.demand
            - self.market.supply
        )

        price_change = (
            shortage * 0.08
            + self.climate.climate_pressure * 0.50
            + shock * 8.0
            - self.agriculture.production * 0.0005
        )

        self.market.price_index = clamp(
            self.market.price_index
            + price_change,
            20.0,
            500.0,
        )

        waste_change = (
            params["waste_change"]
            + shock * 1.0
            + self.supply_chain.storage_capacity
            * -0.002
        )

        self.market.food_waste = clamp(
            self.market.food_waste
            + waste_change,
            0.0,
            50.0,
        )

        affordability = (
            100.0
            - (self.market.price_index - 100.0)
            * 0.35
            - self.market.food_waste * 0.50
        )

        self.market.affordability = clamp(
            affordability,
            0.0,
            100.0,
        )

    # ========================================================
    # FOOD SECURITY SCORE
    # ========================================================

    def food_security_score(self) -> float:

        availability = clamp(
            self.market.supply,
            0.0,
            150.0,
        ) / 1.5

        affordability = (
            self.market.affordability
        )

        agricultural = (
            self.agriculture.resilience
        )

        infrastructure = (
            self.supply_chain.transport_capacity
            * 0.50
            + self.supply_chain.storage_capacity
            * 0.50
        )

        water = (
            self.agriculture.water_availability
        )

        climate = (
            (1.0 - self.climate.climate_pressure)
            * 100.0
        )

        reserves = (
            self.supply_chain.emergency_reserves
        )

        score = (
            availability * 0.20
            + affordability * 0.20
            + agricultural * 0.15
            + infrastructure * 0.15
            + water * 0.10
            + climate * 0.10
            + reserves * 0.10
        )

        return clamp(
            score,
            0.0,
            100.0,
        )

    # ========================================================
    # STATE
    # ========================================================

    def measure(
        self,
        period: int,
        shock: float,
    ) -> State:

        return State(
            period=period,

            production=(
                self.agriculture.production
            ),

            productivity=(
                self.agriculture.productivity
            ),

            water_availability=(
                self.agriculture.water_availability
            ),

            soil_health=(
                self.agriculture.soil_health
            ),

            agricultural_resilience=(
                self.agriculture.resilience
            ),

            transport_capacity=(
                self.supply_chain.transport_capacity
            ),

            storage_capacity=(
                self.supply_chain.storage_capacity
            ),

            disruption_risk=(
                self.supply_chain.disruption_risk
            ),

            emergency_reserves=(
                self.supply_chain.emergency_reserves
            ),

            supply=self.market.supply,

            demand=self.market.demand,

            price_index=self.market.price_index,

            food_waste=self.market.food_waste,

            affordability=self.market.affordability,

            climate_pressure=(
                self.climate.climate_pressure
            ),

            extreme_weather=(
                self.climate.extreme_weather
            ),

            food_security_score=(
                self.food_security_score()
            ),

            food_shock=shock,
        )

    # ========================================================
    # RUN
    # ========================================================

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

                shock = self.food_shock()

                self.update_climate(
                    params,
                    shock,
                )

                self.update_agriculture(
                    params,
                    shock,
                )

                self.update_supply_chain(
                    params,
                    shock,
                )

                self.update_market(
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
# MONTE CARLO
# ============================================================

def monte_carlo(
    scenario: str,
    periods: int,
    runs: int,
    seed: int,
) -> Dict[str, float]:

    scores = []
    prices = []
    production = []
    affordability = []

    for run_number in range(runs):

        twin = FoodSecurityTwin(
            scenario=scenario,
            seed=seed + run_number,
        )

        states = twin.run(
            periods
        )

        final = states[-1]

        scores.append(
            final.food_security_score
        )

        prices.append(
            final.price_index
        )

        production.append(
            final.production
        )

        affordability.append(
            final.affordability
        )

    return {
        "scenario": scenario,
        "runs": runs,
        "periods": periods,
        "mean_food_security": safe_mean(scores),
        "mean_food_price_index": safe_mean(prices),
        "mean_production": safe_mean(production),
        "mean_affordability": safe_mean(
            affordability
        ),
    }


# ============================================================
# SCENARIO COMPARISON
# ============================================================

def compare(
    periods: int,
    runs: int,
    seed: int,
) -> List[Dict[str, float]]:

    scenarios = [
        "baseline",
        "climate_stress",
        "sustainable_agriculture",
        "supply_resilience",
        "food_crisis",
        "investment",
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
    print("FOOD SECURITY TWIN")
    print(f"Version: {VERSION}")
    print("=" * 75)

    print(f"Scenario: {scenario}")
    print(f"Periods:  {final.period}")

    print()
    print("AGRICULTURE")
    print("-" * 75)

    print(
        f"Production:          "
        f"{final.production:.2f}"
    )

    print(
        f"Productivity:        "
        f"{final.productivity:.2f}"
    )

    print(
        f"Water availability:  "
        f"{final.water_availability:.2f}"
    )

    print(
        f"Soil health:         "
        f"{final.soil_health:.2f}"
    )

    print(
        f"Farm resilience:     "
        f"{final.agricultural_resilience:.2f}"
    )

    print()
    print("SUPPLY CHAIN")
    print("-" * 75)

    print(
        f"Transport capacity:  "
        f"{final.transport_capacity:.2f}"
    )

    print(
        f"Storage capacity:    "
        f"{final.storage_capacity:.2f}"
    )

    print(
        f"Disruption risk:     "
        f"{final.disruption_risk:.3f}"
    )

    print(
        f"Emergency reserves:  "
        f"{final.emergency_reserves:.2f}"
    )

    print()
    print("FOOD MARKET")
    print("-" * 75)

    print(
        f"Supply:              "
        f"{final.supply:.2f}"
    )

    print(
        f"Demand:              "
        f"{final.demand:.2f}"
    )

    print(
        f"Price index:         "
        f"{final.price_index:.2f}"
    )

    print(
        f"Food waste:          "
        f"{final.food_waste:.2f}%"
    )

    print(
        f"Affordability:       "
        f"{final.affordability:.2f}"
    )

    print()
    print("CLIMATE")
    print("-" * 75)

    print(
        f"Climate pressure:    "
        f"{final.climate_pressure:.3f}"
    )

    print(
        f"Extreme weather:     "
        f"{final.extreme_weather:.3f}"
    )

    print()
    print(
        f"FOOD SECURITY SCORE: "
        f"{final.food_security_score:.2f}/100"
    )

    print(
        f"Production change:   "
        f"{percentage_change(first.production, final.production):+.2f}%"
    )

    print("=" * 75)


def print_comparison(
    results: List[Dict[str, float]],
) -> None:

    print()
    print("=" * 110)
    print("FOOD SECURITY SCENARIO COMPARISON")
    print("=" * 110)

    print(
        f"{'Scenario':<25}"
        f"{'Security':>14}"
        f"{'Price':>14}"
        f"{'Production':>16}"
        f"{'Affordability':>18}"
    )

    print("-" * 110)

    for item in results:

        print(
            f"{item['scenario']:<25}"
            f"{item['mean_food_security']:>14.2f}"
            f"{item['mean_food_price_index']:>14.2f}"
            f"{item['mean_production']:>16.2f}"
            f"{item['mean_affordability']:>18.2f}"
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
    print("FOOD SECURITY TWIN SELF TEST")
    print("=" * 65)

    # Test 1
    try:

        twin = FoodSecurityTwin(
            scenario="baseline",
            seed=42,
        )

        states = twin.run(
            periods=5
        )

        assert len(states) == 6
        assert states[-1].production > 0

        print("PASS: basic simulation")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: basic simulation — {exc}"
        )

        failed += 1

    # Test 2
    try:

        twin = FoodSecurityTwin(
            scenario="sustainable_agriculture",
            seed=42,
        )

        states = twin.run(
            periods=10
        )

        for state in states:

            assert 0 <= state.water_availability <= 100
            assert 0 <= state.soil_health <= 100
            assert 0 <= state.disruption_risk <= 1
            assert 0 <= state.food_security_score <= 100
            assert 0 <= state.affordability <= 100

        print("PASS: variable bounds")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: variable bounds — {exc}"
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

        assert result["runs"] == 10
        assert result["mean_food_security"] >= 0

        print("PASS: Monte Carlo")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: Monte Carlo — {exc}"
        )

        failed += 1

    # Test 4
    try:

        results = compare(
            periods=5,
            runs=5,
            seed=42,
        )

        assert len(results) == 6

        names = {
            item["scenario"]
            for item in results
        }

        assert "food_crisis" in names
        assert "investment" in names

        print("PASS: scenario comparison")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: scenario comparison — {exc}"
        )

        failed += 1

    # Test 5
    try:

        twin = FoodSecurityTwin(
            scenario="supply_resilience",
            seed=42,
        )

        states = twin.run(
            periods=10
        )

        assert (
            states[-1].storage_capacity
            > states[0].storage_capacity
        )

        print("PASS: supply resilience dynamics")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: supply resilience dynamics — {exc}"
        )

        failed += 1

    print("=" * 65)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")

    if failed == 0:

        print(
            "FOOD SECURITY TWIN SELF TEST: PASS"
        )

        return True

    print(
        "FOOD SECURITY TWIN SELF TEST: FAIL"
    )

    return False


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description="Food Security Twin"
    )

    parser.add_argument(
        "--scenario",
        choices=sorted(
            FoodSecurityTwin.SCENARIOS
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

    twin = FoodSecurityTwin(
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