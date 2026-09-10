#!/usr/bin/env python3
"""
Global Digital Twin - Integration Gate 5
========================================

Gate 5 objective:
    Add scenario analysis and Monte Carlo uncertainty propagation
    to the common Global Digital Twin state.

This gate evaluates:

    - Baseline
    - Sustainable transition
    - Rapid transition
    - Climate stress
    - Food stress
    - Energy crisis
    - Disaster stress
    - Resilience-first investment

Features:
    * CommonState data contract
    * Cross-domain interactions
    * Scenario engine
    * Monte Carlo simulation
    * Confidence intervals
    * Risk statistics
    * Scenario comparison
    * Deterministic seeds
    * JSON export
    * CSV export
    * Built-in self-tests

Standard library only.

Version: 5.0.0
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import sys
import time

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Any


VERSION = "5.0.0"


# ============================================================
# SCENARIOS
# ============================================================

SCENARIOS = {
    "baseline": {
        "climate_pressure": 1.00,
        "energy_transition": 1.00,
        "food_resilience": 1.00,
        "disaster_probability": 1.00,
        "resilience_investment": 1.00,
        "governance_quality": 1.00,
    },

    "sustainable": {
        "climate_pressure": 0.75,
        "energy_transition": 1.35,
        "food_resilience": 1.20,
        "disaster_probability": 0.85,
        "resilience_investment": 1.20,
        "governance_quality": 1.10,
    },

    "rapid_transition": {
        "climate_pressure": 0.60,
        "energy_transition": 1.70,
        "food_resilience": 1.10,
        "disaster_probability": 0.80,
        "resilience_investment": 1.15,
        "governance_quality": 1.05,
    },

    "climate_stress": {
        "climate_pressure": 1.60,
        "energy_transition": 0.90,
        "food_resilience": 0.85,
        "disaster_probability": 1.35,
        "resilience_investment": 0.95,
        "governance_quality": 0.95,
    },

    "food_stress": {
        "climate_pressure": 1.25,
        "energy_transition": 0.95,
        "food_resilience": 0.55,
        "disaster_probability": 1.20,
        "resilience_investment": 0.90,
        "governance_quality": 0.95,
    },

    "energy_crisis": {
        "climate_pressure": 1.15,
        "energy_transition": 0.55,
        "food_resilience": 0.90,
        "disaster_probability": 1.20,
        "resilience_investment": 0.95,
        "governance_quality": 0.95,
    },

    "disaster_stress": {
        "climate_pressure": 1.30,
        "energy_transition": 0.90,
        "food_resilience": 0.80,
        "disaster_probability": 2.20,
        "resilience_investment": 1.10,
        "governance_quality": 1.00,
    },

    "resilience_first": {
        "climate_pressure": 0.90,
        "energy_transition": 1.10,
        "food_resilience": 1.15,
        "disaster_probability": 0.90,
        "resilience_investment": 1.65,
        "governance_quality": 1.25,
    },
}


DOMAINS = (
    "economy",
    "climate",
    "food",
    "energy",
    "resilience",
    "governance",
    "sensors",
)


# ============================================================
# UTILITIES
# ============================================================

def clamp(
    value: float,
    low: float = 0.0,
    high: float = 100.0,
) -> float:

    return max(
        low,
        min(high, float(value)),
    )


def finite(value: Any) -> bool:

    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def mean(values: List[float]) -> float:

    if not values:
        return 0.0

    return sum(values) / len(values)


def percentile(
    values: List[float],
    p: float,
) -> float:

    if not values:
        return 0.0

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * p

    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower

    return (
        ordered[lower]
        + (ordered[upper] - ordered[lower])
        * fraction
    )


def sha256_object(value: Any) -> str:

    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


# ============================================================
# STATE
# ============================================================

@dataclass
class State:

    period: int

    gdp: float
    employment: float
    human_capital: float

    climate_risk: float
    emissions: float
    adaptation: float

    food_security: float
    food_price: float
    food_production: float

    renewable_energy: float
    energy_reliability: float
    energy_price: float

    infrastructure: float
    preparedness: float
    recovery: float

    governance: float
    transparency: float

    sensor_quality: float

    global_score: float = 0.0
    events: int = 0

    def validate(self) -> List[str]:

        errors = []

        for name, value in asdict(self).items():

            if name in {
                "period",
                "events",
            }:
                continue

            if not finite(value):
                errors.append(
                    f"{name} is not finite"
                )

        return errors


# ============================================================
# SIMULATION
# ============================================================

class GlobalDigitalTwinGate5:

    def __init__(
        self,
        scenario: str = "baseline",
        seed: int = 42,
    ):

        if scenario not in SCENARIOS:
            raise ValueError(
                f"Unknown scenario: {scenario}"
            )

        self.scenario = scenario
        self.params = SCENARIOS[scenario]

        self.seed = seed
        self.random = random.Random(seed)

        self.history: List[State] = []

    # --------------------------------------------------------
    # INITIAL STATE
    # --------------------------------------------------------

    def initial_state(self) -> State:

        return State(
            period=0,

            gdp=100.0,
            employment=95.0,
            human_capital=60.0,

            climate_risk=25.0,
            emissions=50.0,
            adaptation=40.0,

            food_security=80.0,
            food_price=100.0,
            food_production=100.0,

            renewable_energy=35.0,
            energy_reliability=96.0,
            energy_price=100.0,

            infrastructure=80.0,
            preparedness=70.0,
            recovery=72.0,

            governance=90.0,
            transparency=88.0,

            sensor_quality=90.0,
        )

    # --------------------------------------------------------
    # RANDOM UNCERTAINTY
    # --------------------------------------------------------

    def shock(
        self,
        magnitude: float,
    ) -> float:

        return self.random.gauss(
            0.0,
            magnitude,
        )

    # --------------------------------------------------------
    # ECONOMY
    # --------------------------------------------------------

    def update_economy(
        self,
        state: State,
    ) -> None:

        energy_effect = (
            state.energy_reliability - 90.0
        ) * 0.015

        climate_effect = (
            20.0 - state.climate_risk
        ) * 0.01

        food_effect = (
            state.food_security - 75.0
        ) * 0.008

        governance_effect = (
            state.governance - 75.0
        ) * 0.006

        growth = (
            2.0
            + energy_effect
            + climate_effect
            + food_effect
            + governance_effect
        )

        growth += self.shock(0.25)

        state.gdp *= (
            1.0 + growth / 100.0
        )

        state.employment += (
            growth * 0.20
            + self.shock(0.10)
        )

        state.human_capital += (
            0.25
            + (
                state.governance - 80.0
            ) * 0.01
        )

    # --------------------------------------------------------
    # CLIMATE
    # --------------------------------------------------------

    def update_climate(
        self,
        state: State,
    ) -> None:

        pressure = self.params[
            "climate_pressure"
        ]

        emissions_effect = (
            state.emissions - 40.0
        ) * 0.025

        transition_effect = (
            state.renewable_energy - 35.0
        ) * 0.015

        adaptation_effect = (
            state.adaptation - 40.0
        ) * 0.020

        state.climate_risk += (
            0.20 * pressure
            + emissions_effect * 0.01
            - transition_effect
            - adaptation_effect
            + self.shock(0.20)
        )

        state.climate_risk = clamp(
            state.climate_risk
        )

        state.emissions += (
            0.30 * pressure
            - transition_effect * 0.8
            + self.shock(0.15)
        )

        state.emissions = max(
            0.0,
            state.emissions,
        )

        state.adaptation += (
            0.30
            * self.params[
                "resilience_investment"
            ]
            + self.shock(0.08)
        )

        state.adaptation = clamp(
            state.adaptation
        )

    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    def update_energy(
        self,
        state: State,
    ) -> None:

        transition = self.params[
            "energy_transition"
        ]

        investment = (
            0.70 * transition
            + self.shock(0.15)
        )

        state.renewable_energy += investment

        state.renewable_energy = clamp(
            state.renewable_energy
        )

        reliability = (
            0.05
            + (
                state.renewable_energy - 35.0
            ) * 0.01
            - (
                state.climate_risk - 25.0
            ) * 0.005
        )

        state.energy_reliability += (
            reliability
            + self.shock(0.12)
        )

        state.energy_reliability = clamp(
            state.energy_reliability
        )

        state.energy_price += (
            0.10
            - (
                state.renewable_energy - 35.0
            ) * 0.02
            + self.shock(0.30)
        )

        state.energy_price = max(
            20.0,
            state.energy_price,
        )

    # --------------------------------------------------------
    # FOOD
    # --------------------------------------------------------

    def update_food(
        self,
        state: State,
    ) -> None:

        resilience = self.params[
            "food_resilience"
        ]

        climate_damage = (
            state.climate_risk - 20.0
        ) * 0.06

        production_change = (
            0.25 * resilience
            - climate_damage
            + self.shock(0.20)
        )

        state.food_production += (
            production_change
        )

        state.food_production = max(
            1.0,
            state.food_production,
        )

        state.food_security += (
            (
                state.food_production - 100.0
            ) * 0.015
            - (
                state.food_price - 100.0
            ) * 0.008
            + 0.15 * resilience
            + self.shock(0.10)
        )

        state.food_security = clamp(
            state.food_security
        )

        state.food_price += (
            (
                100.0
                - state.food_production
            ) * 0.025
            + self.shock(0.35)
        )

        state.food_price = max(
            20.0,
            state.food_price,
        )

    # --------------------------------------------------------
    # RESILIENCE
    # --------------------------------------------------------

    def update_resilience(
        self,
        state: State,
    ) -> None:

        investment = self.params[
            "resilience_investment"
        ]

        governance = self.params[
            "governance_quality"
        ]

        state.infrastructure += (
            0.30 * investment
            + self.shock(0.10)
        )

        state.preparedness += (
            0.35
            * investment
            * governance
            + self.shock(0.10)
        )

        state.recovery += (
            0.25
            * investment
            + self.shock(0.10)
        )

        state.infrastructure = clamp(
            state.infrastructure
        )

        state.preparedness = clamp(
            state.preparedness
        )

        state.recovery = clamp(
            state.recovery
        )

    # --------------------------------------------------------
    # GOVERNANCE
    # --------------------------------------------------------

    def update_governance(
        self,
        state: State,
    ) -> None:

        quality = self.params[
            "governance_quality"
        ]

        state.governance += (
            0.10 * quality
            + self.shock(0.05)
        )

        state.transparency += (
            0.08 * quality
            + self.shock(0.04)
        )

        state.governance = clamp(
            state.governance
        )

        state.transparency = clamp(
            state.transparency
        )

    # --------------------------------------------------------
    # SENSORS
    # --------------------------------------------------------

    def update_sensors(
        self,
        state: State,
    ) -> None:

        state.sensor_quality += (
            0.10
            + (
                state.governance - 80.0
            ) * 0.005
            + self.shock(0.04)
        )

        state.sensor_quality = clamp(
            state.sensor_quality
        )

    # --------------------------------------------------------
    # DISASTERS
    # --------------------------------------------------------

    def disaster_event(
        self,
        state: State,
    ) -> bool:

        probability = (
            0.08
            * self.params[
                "disaster_probability"
            ]
        )

        if self.random.random() >= probability:
            return False

        severity = self.random.uniform(
            5.0,
            25.0,
        )

        protection = (
            state.preparedness
            + state.infrastructure
        ) / 200.0

        effective = severity * (
            1.0 - protection * 0.60
        )

        state.infrastructure -= (
            effective * 0.30
        )

        state.preparedness -= (
            effective * 0.20
        )

        state.recovery -= (
            effective * 0.15
        )

        state.food_security -= (
            effective * 0.10
        )

        state.energy_reliability -= (
            effective * 0.08
        )

        state.gdp *= (
            1.0 - effective * 0.001
        )

        return True

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    def calculate_score(
        self,
        state: State,
    ) -> float:

        climate_score = (
            100.0
            - state.climate_risk
        )

        emissions_score = clamp(
            100.0
            - state.emissions
        )

        economic_score = clamp(
            50.0
            + (
                state.gdp - 100.0
            ) * 2.0
        )

        values = [
            state.employment,
            state.human_capital,
            climate_score,
            emissions_score,
            state.food_security,
            state.energy_reliability,
            state.infrastructure,
            state.preparedness,
            state.recovery,
            state.governance,
            state.transparency,
            state.sensor_quality,
            economic_score,
        ]

        state.global_score = clamp(
            mean(values)
        )

        return state.global_score

    # --------------------------------------------------------
    # STEP
    # --------------------------------------------------------

    def step(
        self,
        state: State,
    ) -> State:

        state.period += 1

        self.update_climate(state)
        self.update_energy(state)
        self.update_food(state)
        self.update_resilience(state)
        self.update_governance(state)
        self.update_sensors(state)
        self.update_economy(state)

        if self.disaster_event(state):
            state.events += 1

        self.calculate_score(state)

        return state

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    def run(
        self,
        periods: int = 20,
    ) -> List[State]:

        self.history.clear()

        state = self.initial_state()

        self.calculate_score(state)

        self.history.append(
            State(**asdict(state))
        )

        for _ in range(max(1, periods)):

            self.step(state)

            errors = state.validate()

            if errors:
                raise ValueError(
                    "; ".join(errors)
                )

            self.history.append(
                State(**asdict(state))
            )

        return self.history

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    def summary(self) -> Dict[str, Any]:

        if not self.history:
            return {}

        scores = [
            state.global_score
            for state in self.history
        ]

        final = self.history[-1]

        return {
            "scenario": self.scenario,
            "periods": len(self.history) - 1,
            "initial_score": round(
                scores[0],
                4,
            ),
            "final_score": round(
                scores[-1],
                4,
            ),
            "average_score": round(
                mean(scores),
                4,
            ),
            "minimum_score": round(
                min(scores),
                4,
            ),
            "maximum_score": round(
                max(scores),
                4,
            ),
            "final_gdp": round(
                final.gdp,
                4,
            ),
            "final_food_security": round(
                final.food_security,
                4,
            ),
            "final_energy_reliability": round(
                final.energy_reliability,
                4,
            ),
            "final_climate_risk": round(
                final.climate_risk,
                4,
            ),
            "disaster_events": final.events,
        }


# ============================================================
# MONTE CARLO
# ============================================================

@dataclass
class MonteCarloResult:

    scenario: str
    runs: int
    periods: int

    mean_final_score: float
    median_final_score: float

    p05_final_score: float
    p25_final_score: float
    p75_final_score: float
    p95_final_score: float

    standard_deviation: float

    probability_score_below_50: float
    probability_score_above_75: float

    mean_final_gdp: float
    mean_food_security: float
    mean_energy_reliability: float
    mean_climate_risk: float

    total_disaster_events: int

    fingerprint: str


class MonteCarloEngine:

    def __init__(
        self,
        periods: int = 20,
        runs: int = 100,
        seed: int = 42,
    ):

        self.periods = max(
            1,
            int(periods),
        )

        self.runs = max(
            1,
            int(runs),
        )

        self.seed = seed

    def run(
        self,
        scenario: str,
    ) -> MonteCarloResult:

        final_scores = []
        final_gdp = []
        final_food = []
        final_energy = []
        final_climate = []

        disasters = 0

        for run_id in range(self.runs):

            simulation = GlobalDigitalTwinGate5(
                scenario=scenario,
                seed=self.seed + run_id,
            )

            history = simulation.run(
                periods=self.periods
            )

            final = history[-1]

            final_scores.append(
                final.global_score
            )

            final_gdp.append(
                final.gdp
            )

            final_food.append(
                final.food_security
            )

            final_energy.append(
                final.energy_reliability
            )

            final_climate.append(
                final.climate_risk
            )

            disasters += final.events

        ordered = sorted(final_scores)

        result_data = {
            "scenario": scenario,
            "runs": self.runs,
            "periods": self.periods,
            "scores": [
                round(value, 8)
                for value in ordered
            ],
        }

        return MonteCarloResult(
            scenario=scenario,
            runs=self.runs,
            periods=self.periods,

            mean_final_score=round(
                mean(final_scores),
                4,
            ),

            median_final_score=round(
                statistics.median(final_scores),
                4,
            ),

            p05_final_score=round(
                percentile(
                    final_scores,
                    0.05,
                ),
                4,
            ),

            p25_final_score=round(
                percentile(
                    final_scores,
                    0.25,
                ),
                4,
            ),

            p75_final_score=round(
                percentile(
                    final_scores,
                    0.75,
                ),
                4,
            ),

            p95_final_score=round(
                percentile(
                    final_scores,
                    0.95,
                ),
                4,
            ),

            standard_deviation=round(
                statistics.pstdev(final_scores)
                if len(final_scores) > 1
                else 0.0,
                4,
            ),

            probability_score_below_50=round(
                sum(
                    score < 50.0
                    for score in final_scores
                ) / len(final_scores),
                4,
            ),

            probability_score_above_75=round(
                sum(
                    score > 75.0
                    for score in final_scores
                ) / len(final_scores),
                4,
            ),

            mean_final_gdp=round(
                mean(final_gdp),
                4,
            ),

            mean_food_security=round(
                mean(final_food),
                4,
            ),

            mean_energy_reliability=round(
                mean(final_energy),
                4,
            ),

            mean_climate_risk=round(
                mean(final_climate),
                4,
            ),

            total_disaster_events=disasters,

            fingerprint=sha256_object(
                result_data
            ),
        )


# ============================================================
# SCENARIO COMPARISON
# ============================================================

def compare_scenarios(
    periods: int,
    runs: int,
    seed: int,
) -> List[MonteCarloResult]:

    results = []

    for index, scenario in enumerate(
        SCENARIOS
    ):

        engine = MonteCarloEngine(
            periods=periods,
            runs=runs,
            seed=seed + index * 10000,
        )

        results.append(
            engine.run(scenario)
        )

    return results


# ============================================================
# REPORTING
# ============================================================

def print_monte_carlo(
    result: MonteCarloResult,
) -> None:

    print()
    print("=" * 72)
    print("MONTE CARLO RESULT")
    print("=" * 72)

    print(f"Scenario:              {result.scenario}")
    print(f"Runs:                  {result.runs}")
    print(f"Periods:               {result.periods}")

    print()
    print(
        f"Mean final score:      "
        f"{result.mean_final_score:.2f}"
    )

    print(
        f"Median final score:    "
        f"{result.median_final_score:.2f}"
    )

    print(
        f"5th percentile:        "
        f"{result.p05_final_score:.2f}"
    )

    print(
        f"25th percentile:       "
        f"{result.p25_final_score:.2f}"
    )

    print(
        f"75th percentile:       "
        f"{result.p75_final_score:.2f}"
    )

    print(
        f"95th percentile:       "
        f"{result.p95_final_score:.2f}"
    )

    print(
        f"Standard deviation:    "
        f"{result.standard_deviation:.2f}"
    )

    print()
    print(
        f"P(score < 50):         "
        f"{result.probability_score_below_50 * 100:.2f}%"
    )

    print(
        f"P(score > 75):         "
        f"{result.probability_score_above_75 * 100:.2f}%"
    )

    print()
    print(
        f"Mean final GDP:         "
        f"{result.mean_final_gdp:.2f}"
    )

    print(
        f"Mean food security:    "
        f"{result.mean_food_security:.2f}"
    )

    print(
        f"Mean energy reliability:"
        f" {result.mean_energy_reliability:.2f}"
    )

    print(
        f"Mean climate risk:     "
        f"{result.mean_climate_risk:.2f}"
    )

    print(
        f"Total disaster events: "
        f"{result.total_disaster_events}"
    )

    print()
    print(f"Fingerprint: {result.fingerprint}")
    print("=" * 72)


def print_comparison(
    results: List[MonteCarloResult],
) -> None:

    print()
    print("=" * 90)
    print("SCENARIO COMPARISON")
    print("=" * 90)

    print(
        f"{'Scenario':22s}"
        f"{'Mean':>10s}"
        f"{'P05':>10s}"
        f"{'P95':>10s}"
        f"{'Risk<50':>12s}"
        f"{'Food':>10s}"
        f"{'Energy':>10s}"
    )

    print("-" * 90)

    for result in results:

        print(
            f"{result.scenario:22s}"
            f"{result.mean_final_score:10.2f}"
            f"{result.p05_final_score:10.2f}"
            f"{result.p95_final_score:10.2f}"
            f"{result.probability_score_below_50 * 100:11.2f}%"
            f"{result.mean_food_security:10.2f}"
            f"{result.mean_energy_reliability:10.2f}"
        )

    print("=" * 90)


# ============================================================
# JSON
# ============================================================

def save_json(
    results: List[MonteCarloResult],
    filename: str,
) -> None:

    payload = {
        "version": VERSION,
        "generated_at": time.time(),
        "results": [
            asdict(result)
            for result in results
        ],
    }

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as handle:

        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
        )


# ============================================================
# CSV
# ============================================================

def save_csv(
    results: List[MonteCarloResult],
    filename: str,
) -> None:

    if not results:
        return

    rows = [
        asdict(result)
        for result in results
    ]

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# SELF TEST
# ============================================================

def self_test() -> int:

    print()
    print("GLOBAL DIGITAL TWIN GATE 5 SELF TEST")
    print("=" * 72)

    passed = 0
    failed = 0

    # Test 1
    try:

        assert len(SCENARIOS) >= 8
        assert "baseline" in SCENARIOS
        assert "sustainable" in SCENARIOS

        print("PASS: scenario registry")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: scenario registry — {exc}"
        )

        failed += 1

    # Test 2
    try:

        simulation = GlobalDigitalTwinGate5(
            scenario="baseline",
            seed=42,
        )

        history = simulation.run(
            periods=5
        )

        assert len(history) == 6

        for state in history:
            assert state.validate() == []

        print("PASS: deterministic simulation")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: simulation — {exc}"
        )

        failed += 1

    # Test 3
    try:

        simulation_a = GlobalDigitalTwinGate5(
            scenario="baseline",
            seed=123,
        )

        simulation_b = GlobalDigitalTwinGate5(
            scenario="baseline",
            seed=123,
        )

        a = simulation_a.run(5)
        b = simulation_b.run(5)

        assert [
            state.global_score
            for state in a
        ] == [
            state.global_score
            for state in b
        ]

        print("PASS: reproducibility")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: reproducibility — {exc}"
        )

        failed += 1

    # Test 4
    try:

        engine = MonteCarloEngine(
            periods=5,
            runs=10,
            seed=42,
        )

        result = engine.run(
            "baseline"
        )

        assert result.runs == 10
        assert result.periods == 5
        assert 0.0 <= result.p05_final_score
        assert (
            result.p05_final_score
            <= result.p95_final_score
        )

        print("PASS: Monte Carlo engine")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: Monte Carlo — {exc}"
        )

        failed += 1

    # Test 5
    try:

        result_a = MonteCarloEngine(
            periods=3,
            runs=5,
            seed=99,
        ).run("sustainable")

        result_b = MonteCarloEngine(
            periods=3,
            runs=5,
            seed=99,
        ).run("sustainable")

        assert (
            result_a.fingerprint
            == result_b.fingerprint
        )

        print("PASS: Monte Carlo reproducibility")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: Monte Carlo reproducibility — {exc}"
        )

        failed += 1

    # Test 6
    try:

        results = compare_scenarios(
            periods=3,
            runs=3,
            seed=42,
        )

        assert len(results) == len(
            SCENARIOS
        )

        print("PASS: scenario comparison")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: scenario comparison — {exc}"
        )

        failed += 1

    # Final
    print()
    print("=" * 72)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 72)

    if failed == 0:

        print(
            "GLOBAL DIGITAL TWIN GATE 5: PASS"
        )

        return 0

    print(
        "GLOBAL DIGITAL TWIN GATE 5: REVIEW"
    )

    return 1


# ============================================================
# CLI
# ============================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description=(
            "Global Digital Twin Integration Gate 5"
        )
    )

    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
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

    parser.add_argument(
        "--version",
        action="version",
        version=VERSION,
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.compare:

        results = compare_scenarios(
            periods=args.periods,
            runs=args.runs,
            seed=args.seed,
        )

        print_comparison(results)

        if args.json:
            save_json(
                results,
                args.json,
            )

        if args.csv:
            save_csv(
                results,
                args.csv,
            )

        return 0

    engine = MonteCarloEngine(
        periods=args.periods,
        runs=args.runs,
        seed=args.seed,
    )

    result = engine.run(
        args.scenario
    )

    print_monte_carlo(result)

    if args.json:

        save_json(
            [result],
            args.json,
        )

        print(
            f"\nJSON written to: {args.json}"
        )

    if args.csv:

        save_csv(
            [result],
            args.csv,
        )

        print(
            f"CSV written to: {args.csv}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())