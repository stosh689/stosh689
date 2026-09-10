"""
Global Digital Twin
===================

Integration Gate 1

A dependency-free orchestration layer for a global digital-twin
research platform.

Integrated domains:
    - Economy / GEDT
    - Climate
    - Food security
    - Energy transition
    - Disaster resilience
    - AI governance
    - Sensor / CIDAR observations

Design principles:
    - Python standard library only
    - Reproducible simulations
    - Common state representation
    - Scenario analysis
    - Monte Carlo experiments
    - Resilience scoring
    - Governance scoring
    - JSON / CSV export
    - Built-in self-tests

Version: 1.0.0
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from dataclasses import asdict, dataclass
from typing import Dict, List


VERSION = "1.0.0"


# ============================================================================
# Utility functions
# ============================================================================

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def pct_change(old: float, new: float) -> float:
    if abs(old) < 1e-12:
        return 0.0
    return ((new - old) / old) * 100.0


def stable_hash(payload: str) -> str:
    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


# ============================================================================
# Domain state
# ============================================================================

@dataclass
class EconomyState:
    output: float = 100.0
    productivity: float = 1.00
    employment: float = 0.94
    investment: float = 10.0
    inequality: float = 0.35


@dataclass
class ClimateState:
    temperature_anomaly: float = 1.20
    climate_risk: float = 0.25
    emissions: float = 100.0
    adaptation: float = 0.25


@dataclass
class FoodState:
    production: float = 100.0
    food_price: float = 1.00
    food_security: float = 0.80
    supply_resilience: float = 0.70


@dataclass
class EnergyState:
    demand: float = 100.0
    renewable_share: float = 0.30
    energy_price: float = 0.15
    storage: float = 0.50
    grid_reliability: float = 0.96


@dataclass
class DisasterState:
    infrastructure: float = 0.85
    preparedness: float = 0.60
    active_shock: float = 0.00
    recovery: float = 0.70


@dataclass
class GovernanceState:
    transparency: float = 0.85
    accountability: float = 0.85
    safety: float = 0.90
    human_oversight: float = 0.90


@dataclass
class SensorState:
    observed_depth: float = 20.0
    uncertainty: float = 0.50
    sensor_confidence: float = 0.95


@dataclass
class GlobalState:
    period: int
    economy: EconomyState
    climate: ClimateState
    food: FoodState
    energy: EnergyState
    disaster: DisasterState
    governance: GovernanceState
    sensors: SensorState
    resilience_index: float
    sustainability_index: float
    human_welfare_index: float
    global_system_score: float


@dataclass
class ScenarioSummary:
    scenario: str
    periods: int
    final_output: float
    output_change_pct: float
    final_emissions: float
    emissions_change_pct: float
    final_renewable_share: float
    final_food_security: float
    final_energy_price: float
    final_resilience: float
    final_sustainability: float
    final_human_welfare: float
    final_governance: float
    final_global_score: float


# ============================================================================
# Global Digital Twin
# ============================================================================

class GlobalDigitalTwin:

    SCENARIOS = {
        "baseline": {
            "economic_growth": 0.010,
            "green_investment": 0.010,
            "climate_pressure": 0.010,
            "food_investment": 0.005,
            "energy_transition": 0.010,
            "preparedness": 0.005,
            "governance": 0.002,
            "shock_probability": 0.08,
        },

        "sustainable": {
            "economic_growth": 0.012,
            "green_investment": 0.030,
            "climate_pressure": 0.006,
            "food_investment": 0.020,
            "energy_transition": 0.035,
            "preparedness": 0.020,
            "governance": 0.010,
            "shock_probability": 0.05,
        },

        "rapid_transition": {
            "economic_growth": 0.013,
            "green_investment": 0.050,
            "climate_pressure": 0.003,
            "food_investment": 0.025,
            "energy_transition": 0.060,
            "preparedness": 0.025,
            "governance": 0.015,
            "shock_probability": 0.04,
        },

        "crisis": {
            "economic_growth": -0.015,
            "green_investment": 0.002,
            "climate_pressure": 0.040,
            "food_investment": 0.001,
            "energy_transition": 0.002,
            "preparedness": 0.001,
            "governance": -0.005,
            "shock_probability": 0.25,
        },

        "resilience_first": {
            "economic_growth": 0.008,
            "green_investment": 0.025,
            "climate_pressure": 0.008,
            "food_investment": 0.030,
            "energy_transition": 0.030,
            "preparedness": 0.040,
            "governance": 0.012,
            "shock_probability": 0.06,
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

        self.economy = EconomyState()
        self.climate = ClimateState()
        self.food = FoodState()
        self.energy = EnergyState()
        self.disaster = DisasterState()
        self.governance = GovernanceState()
        self.sensors = SensorState()

        self.history: List[GlobalState] = []

    # ------------------------------------------------------------------------
    # Economy
    # ------------------------------------------------------------------------

    def update_economy(self) -> None:

        growth = self.params["economic_growth"]

        energy_penalty = max(
            0.0,
            self.energy.energy_price - 0.15,
        ) * 0.04

        food_penalty = max(
            0.0,
            self.food.food_price - 1.0,
        ) * 0.025

        disaster_penalty = (
            self.disaster.active_shock * 0.08
        )

        climate_penalty = (
            self.climate.climate_risk * 0.01
        )

        productivity_gain = (
            self.economy.productivity * 0.002
        )

        net_growth = (
            growth
            + productivity_gain
            - energy_penalty
            - food_penalty
            - disaster_penalty
            - climate_penalty
        )

        self.economy.output *= (
            1.0 + net_growth
        )

        self.economy.productivity = clamp(
            self.economy.productivity
            + self.params["green_investment"] * 0.02,
            0.50,
            2.00,
        )

        self.economy.investment = (
            self.params["green_investment"] * 100.0
        )

        self.economy.employment = clamp(
            self.economy.employment
            + net_growth * 0.20
            - self.disaster.active_shock * 0.02,
            0.50,
            0.99,
        )

        self.economy.inequality = clamp(
            self.economy.inequality
            - self.params["governance"] * 0.10
            + max(0.0, -net_growth) * 0.05,
            0.10,
            0.70,
        )

    # ------------------------------------------------------------------------
    # Climate
    # ------------------------------------------------------------------------

    def update_climate(self) -> None:

        emissions_reduction = (
            self.params["energy_transition"]
            * 1.5
        )

        natural_pressure = (
            self.params["climate_pressure"]
        )

        self.climate.emissions *= clamp(
            1.0
            + natural_pressure
            - emissions_reduction,
            0.70,
            1.05,
        )

        self.climate.emissions = max(
            5.0,
            self.climate.emissions,
        )

        self.climate.temperature_anomaly += (
            self.climate.emissions
            / 100000.0
        )

        self.climate.adaptation = clamp(
            self.climate.adaptation
            + self.params["preparedness"] * 0.30,
            0.0,
            1.0,
        )

        raw_risk = (
            0.15
            + self.climate.temperature_anomaly * 0.10
            + self.climate.emissions / 1000.0
        )

        self.climate.climate_risk = clamp(
            raw_risk
            * (1.0 - self.climate.adaptation * 0.40),
            0.0,
            1.0,
        )

    # ------------------------------------------------------------------------
    # Energy
    # ------------------------------------------------------------------------

    def update_energy(self) -> None:

        demand_growth = (
            0.005
            + self.params["economic_growth"] * 0.25
        )

        self.energy.demand *= (
            1.0 + demand_growth
        )

        transition = (
            self.params["energy_transition"]
        )

        self.energy.renewable_share = clamp(
            self.energy.renewable_share
            + transition,
            0.0,
            0.99,
        )

        self.energy.storage = clamp(
            self.energy.storage
            + transition * 0.80,
            0.0,
            1.0,
        )

        renewable_benefit = (
            self.energy.renewable_share
            * 0.015
        )

        climate_pressure = (
            self.climate.climate_risk
            * 0.020
        )

        shock_pressure = (
            self.disaster.active_shock
            * 0.10
        )

        self.energy.energy_price *= (
            1.0
            - renewable_benefit
            + climate_pressure
            + shock_pressure
        )

        self.energy.energy_price = clamp(
            self.energy.energy_price,
            0.05,
            2.00,
        )

        self.energy.grid_reliability = clamp(
            self.energy.grid_reliability
            + transition * 0.05
            + self.params["preparedness"] * 0.02
            - self.disaster.active_shock * 0.10,
            0.60,
            0.999,
        )

    # ------------------------------------------------------------------------
    # Food
    # ------------------------------------------------------------------------

    def update_food(self) -> None:

        investment = (
            self.params["food_investment"]
        )

        climate_damage = (
            self.climate.climate_risk * 0.025
        )

        energy_cost = max(
            0.0,
            self.energy.energy_price - 0.15,
        ) * 0.04

        resilience_gain = (
            self.food.supply_resilience * 0.002
        )

        production_change = (
            investment
            + resilience_gain
            - climate_damage
            - energy_cost
            - self.disaster.active_shock * 0.06
        )

        self.food.production *= (
            1.0 + production_change
        )

        self.food.supply_resilience = clamp(
            self.food.supply_resilience
            + investment * 0.30
            + self.params["preparedness"] * 0.10,
            0.0,
            1.0,
        )

        shortage = max(
            0.0,
            100.0 - self.food.production,
        ) / 100.0

        self.food.food_price *= (
            1.0
            + shortage * 0.08
            + self.disaster.active_shock * 0.10
            - investment * 0.05
        )

        self.food.food_price = clamp(
            self.food.food_price,
            0.40,
            5.00,
        )

        self.food.food_security = clamp(
            0.85
            + self.food.supply_resilience * 0.10
            - max(
                0.0,
                self.food.food_price - 1.0,
            ) * 0.25
            - self.climate.climate_risk * 0.10
            - self.disaster.active_shock * 0.15,
            0.0,
            1.0,
        )

    # ------------------------------------------------------------------------
    # Disaster
    # ------------------------------------------------------------------------

    def update_disaster(self) -> None:

        probability = (
            self.params["shock_probability"]
            + self.climate.climate_risk * 0.04
        )

        if self.rng.random() < probability:

            magnitude = self.rng.uniform(
                0.05,
                0.25,
            )

            preparedness_reduction = (
                self.disaster.preparedness
                * 0.35
            )

            self.disaster.active_shock = clamp(
                magnitude
                * (1.0 - preparedness_reduction),
                0.0,
                0.50,
            )

        else:

            self.disaster.active_shock *= 0.70

        self.disaster.preparedness = clamp(
            self.disaster.preparedness
            + self.params["preparedness"] * 0.50,
            0.0,
            1.0,
        )

        damage = (
            self.disaster.active_shock
            * 0.05
        )

        self.disaster.infrastructure = clamp(
            self.disaster.infrastructure
            - damage
            + self.disaster.preparedness * 0.003,
            0.30,
            1.0,
        )

        self.disaster.recovery = clamp(
            self.disaster.recovery
            + self.disaster.preparedness * 0.003
            - self.disaster.active_shock * 0.01,
            0.30,
            1.0,
        )

    # ------------------------------------------------------------------------
    # AI governance
    # ------------------------------------------------------------------------

    def update_governance(self) -> None:

        improvement = (
            self.params["governance"]
        )

        stress_penalty = (
            self.disaster.active_shock * 0.01
        )

        self.governance.transparency = clamp(
            self.governance.transparency
            + improvement
            - stress_penalty,
            0.50,
            1.0,
        )

        self.governance.accountability = clamp(
            self.governance.accountability
            + improvement
            - stress_penalty,
            0.50,
            1.0,
        )

        self.governance.safety = clamp(
            self.governance.safety
            + improvement * 1.2
            - stress_penalty,
            0.50,
            1.0,
        )

        self.governance.human_oversight = clamp(
            self.governance.human_oversight
            + improvement
            - stress_penalty,
            0.50,
            1.0,
        )

    # ------------------------------------------------------------------------
    # CIDAR / sensor observation
    # ------------------------------------------------------------------------

    def update_sensors(self) -> None:

        true_depth = 20.0 + (
            self.disaster.active_shock * 2.0
        )

        measurement_noise = self.rng.gauss(
            0.0,
            0.20,
        )

        observed = (
            true_depth
            + measurement_noise
        )

        self.sensors.observed_depth = observed

        self.sensors.uncertainty = clamp(
            0.20
            + self.disaster.active_shock,
            0.05,
            2.00,
        )

        self.sensors.sensor_confidence = clamp(
            1.0
            - self.sensors.uncertainty * 0.20,
            0.50,
            0.99,
        )

    # ------------------------------------------------------------------------
    # Composite indices
    # ------------------------------------------------------------------------

    def calculate_resilience(self) -> float:

        economic = (
            self.economy.employment
        )

        infrastructure = (
            self.disaster.infrastructure
        )

        preparedness = (
            self.disaster.preparedness
        )

        energy = (
            self.energy.grid_reliability
        )

        food = (
            self.food.food_security
        )

        score = (
            economic * 20.0
            + infrastructure * 20.0
            + preparedness * 15.0
            + energy * 15.0
            + food * 15.0
            + self.disaster.recovery * 15.0
        )

        return clamp(score, 0.0, 100.0)

    def calculate_sustainability(self) -> float:

        renewable = (
            self.energy.renewable_share
        )

        emissions_factor = clamp(
            1.0
            - self.climate.emissions / 150.0,
            0.0,
            1.0,
        )

        climate_adaptation = (
            self.climate.adaptation
        )

        food_resilience = (
            self.food.supply_resilience
        )

        score = (
            renewable * 35.0
            + emissions_factor * 30.0
            + climate_adaptation * 20.0
            + food_resilience * 15.0
        )

        return clamp(score, 0.0, 100.0)

    def calculate_human_welfare(self) -> float:

        employment = (
            self.economy.employment
        )

        food = (
            self.food.food_security
        )

        affordability = clamp(
            1.0
            - max(
                0.0,
                self.energy.energy_price - 0.15,
            ),
            0.0,
            1.0,
        )

        inequality = (
            1.0 - self.economy.inequality
        )

        governance = mean([
            self.governance.transparency,
            self.governance.accountability,
            self.governance.safety,
            self.governance.human_oversight,
        ])

        score = (
            employment * 20.0
            + food * 25.0
            + affordability * 20.0
            + inequality * 15.0
            + governance * 20.0
        )

        return clamp(score, 0.0, 100.0)

    def calculate_global_score(
        self,
        resilience: float,
        sustainability: float,
        welfare: float,
    ) -> float:

        governance = mean([
            self.governance.transparency,
            self.governance.accountability,
            self.governance.safety,
            self.governance.human_oversight,
        ]) * 100.0

        return clamp(
            resilience * 0.30
            + sustainability * 0.25
            + welfare * 0.30
            + governance * 0.15,
            0.0,
            100.0,
        )

    # ------------------------------------------------------------------------
    # Measure
    # ------------------------------------------------------------------------

    def measure(self, period: int) -> GlobalState:

        resilience = self.calculate_resilience()

        sustainability = (
            self.calculate_sustainability()
        )

        welfare = (
            self.calculate_human_welfare()
        )

        global_score = self.calculate_global_score(
            resilience,
            sustainability,
            welfare,
        )

        return GlobalState(
            period=period,
            economy=EconomyState(
                **asdict(self.economy)
            ),
            climate=ClimateState(
                **asdict(self.climate)
            ),
            food=FoodState(
                **asdict(self.food)
            ),
            energy=EnergyState(
                **asdict(self.energy)
            ),
            disaster=DisasterState(
                **asdict(self.disaster)
            ),
            governance=GovernanceState(
                **asdict(self.governance)
            ),
            sensors=SensorState(
                **asdict(self.sensors)
            ),
            resilience_index=resilience,
            sustainability_index=sustainability,
            human_welfare_index=welfare,
            global_system_score=global_score,
        )

    # ------------------------------------------------------------------------
    # One period
    # ------------------------------------------------------------------------

    def step(self, period: int) -> GlobalState:

        self.update_disaster()
        self.update_climate()
        self.update_energy()
        self.update_food()
        self.update_economy()
        self.update_governance()
        self.update_sensors()

        state = self.measure(period)

        self.history.append(state)

        return state

    # ------------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------------

    def run(self, periods: int = 20) -> List[GlobalState]:

        if periods < 1:
            raise ValueError(
                "periods must be >= 1"
            )

        for period in range(
            1,
            periods + 1,
        ):
            self.step(period)

        return self.history

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    def summary(self) -> ScenarioSummary:

        if not self.history:
            raise RuntimeError(
                "Run the simulation first."
            )

        first = self.history[0]
        last = self.history[-1]

        first_governance = mean([
            first.governance.transparency,
            first.governance.accountability,
            first.governance.safety,
            first.governance.human_oversight,
        ])

        final_governance = mean([
            last.governance.transparency,
            last.governance.accountability,
            last.governance.safety,
            last.governance.human_oversight,
        ])

        return ScenarioSummary(
            scenario=self.scenario,
            periods=len(self.history),
            final_output=last.economy.output,
            output_change_pct=pct_change(
                first.economy.output,
                last.economy.output,
            ),
            final_emissions=last.climate.emissions,
            emissions_change_pct=pct_change(
                first.climate.emissions,
                last.climate.emissions,
            ),
            final_renewable_share=(
                last.energy.renewable_share
            ),
            final_food_security=(
                last.food.food_security
            ),
            final_energy_price=(
                last.energy.energy_price
            ),
            final_resilience=(
                last.resilience_index
            ),
            final_sustainability=(
                last.sustainability_index
            ),
            final_human_welfare=(
                last.human_welfare_index
            ),
            final_governance=(
                final_governance * 100.0
            ),
            final_global_score=(
                last.global_system_score
            ),
        )


# ============================================================================
# Monte Carlo
# ============================================================================

def monte_carlo(
    scenario: str,
    periods: int,
    runs: int,
    seed: int,
) -> Dict[str, float]:

    if runs < 1:
        raise ValueError(
            "runs must be >= 1"
        )

    outputs = []
    emissions = []
    renewable = []
    food = []
    resilience = []
    sustainability = []
    welfare = []
    global_scores = []

    for run_number in range(runs):

        model = GlobalDigitalTwin(
            scenario=scenario,
            seed=seed + run_number,
        )

        model.run(periods)

        result = model.summary()

        outputs.append(
            result.final_output
        )

        emissions.append(
            result.final_emissions
        )

        renewable.append(
            result.final_renewable_share
        )

        food.append(
            result.final_food_security
        )

        resilience.append(
            result.final_resilience
        )

        sustainability.append(
            result.final_sustainability
        )

        welfare.append(
            result.final_human_welfare
        )

        global_scores.append(
            result.final_global_score
        )

    return {
        "runs": float(runs),
        "mean_output": mean(outputs),
        "mean_emissions": mean(emissions),
        "mean_renewable_share": mean(renewable),
        "mean_food_security": mean(food),
        "mean_resilience": mean(resilience),
        "mean_sustainability": mean(sustainability),
        "mean_human_welfare": mean(welfare),
        "mean_global_score": mean(global_scores),
        "minimum_global_score": min(global_scores),
        "maximum_global_score": max(global_scores),
    }


# ============================================================================
# Scenario comparison
# ============================================================================

def compare_scenarios(
    periods: int,
    seed: int,
) -> List[ScenarioSummary]:

    results = []

    for scenario in GlobalDigitalTwin.SCENARIOS:

        model = GlobalDigitalTwin(
            scenario=scenario,
            seed=seed,
        )

        model.run(periods)

        results.append(
            model.summary()
        )

    return results


# ============================================================================
# Reporting
# ============================================================================

def print_summary(
    summary: ScenarioSummary,
) -> None:

    print()
    print("=" * 78)
    print("GLOBAL DIGITAL TWIN")
    print("=" * 78)

    print(
        f"Scenario:              {summary.scenario}"
    )

    print(
        f"Periods:               {summary.periods}"
    )

    print()

    print(
        f"Economic output:       "
        f"{summary.final_output:.2f}"
    )

    print(
        f"Output change:         "
        f"{summary.output_change_pct:.2f}%"
    )

    print(
        f"Emissions:             "
        f"{summary.final_emissions:.2f}"
    )

    print(
        f"Emissions change:      "
        f"{summary.emissions_change_pct:.2f}%"
    )

    print(
        f"Renewable share:       "
        f"{summary.final_renewable_share:.3f}"
    )

    print(
        f"Food security:         "
        f"{summary.final_food_security:.3f}"
    )

    print(
        f"Energy price:          "
        f"${summary.final_energy_price:.3f}"
    )

    print(
        f"Resilience index:      "
        f"{summary.final_resilience:.2f}/100"
    )

    print(
        f"Sustainability:        "
        f"{summary.final_sustainability:.2f}/100"
    )

    print(
        f"Human welfare:         "
        f"{summary.final_human_welfare:.2f}/100"
    )

    print(
        f"AI governance:         "
        f"{summary.final_governance:.2f}/100"
    )

    print(
        f"GLOBAL SYSTEM SCORE:   "
        f"{summary.final_global_score:.2f}/100"
    )

    print("=" * 78)


def print_comparison(
    results: List[ScenarioSummary],
) -> None:

    print()
    print("=" * 120)
    print("GLOBAL DIGITAL TWIN — SCENARIO COMPARISON")
    print("=" * 120)

    print(
        f"{'Scenario':<20}"
        f"{'Output':>12}"
        f"{'Emissions':>13}"
        f"{'Renewable':>13}"
        f"{'Food':>10}"
        f"{'Resilience':>13}"
        f"{'Welfare':>11}"
        f"{'Score':>10}"
    )

    print("-" * 120)

    for result in results:

        print(
            f"{result.scenario:<20}"
            f"{result.final_output:>12.2f}"
            f"{result.final_emissions:>13.2f}"
            f"{result.final_renewable_share:>13.3f}"
            f"{result.final_food_security:>10.3f}"
            f"{result.final_resilience:>13.2f}"
            f"{result.final_human_welfare:>11.2f}"
            f"{result.final_global_score:>10.2f}"
        )

    print("=" * 120)


# ============================================================================
# Export
# ============================================================================

def save_json(
    filename: str,
    summary: ScenarioSummary,
    history: List[GlobalState],
) -> None:

    payload = {
        "version": VERSION,
        "artifact": "Global Digital Twin",
        "summary": asdict(summary),
        "history": [
            asdict(state)
            for state in history
        ],
    }

    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )

    payload["integrity_sha256"] = stable_hash(
        serialized
    )

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
    history: List[GlobalState],
) -> None:

    if not history:
        return

    rows = []

    for state in history:

        row = {
            "period": state.period,

            "economic_output":
                state.economy.output,

            "employment":
                state.economy.employment,

            "inequality":
                state.economy.inequality,

            "temperature_anomaly":
                state.climate.temperature_anomaly,

            "climate_risk":
                state.climate.climate_risk,

            "emissions":
                state.climate.emissions,

            "food_production":
                state.food.production,

            "food_price":
                state.food.food_price,

            "food_security":
                state.food.food_security,

            "energy_demand":
                state.energy.demand,

            "renewable_share":
                state.energy.renewable_share,

            "energy_price":
                state.energy.energy_price,

            "grid_reliability":
                state.energy.grid_reliability,

            "infrastructure":
                state.disaster.infrastructure,

            "preparedness":
                state.disaster.preparedness,

            "active_shock":
                state.disaster.active_shock,

            "governance_safety":
                state.governance.safety,

            "human_oversight":
                state.governance.human_oversight,

            "sensor_confidence":
                state.sensors.sensor_confidence,

            "resilience_index":
                state.resilience_index,

            "sustainability_index":
                state.sustainability_index,

            "human_welfare_index":
                state.human_welfare_index,

            "global_system_score":
                state.global_system_score,
        }

        rows.append(row)

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


# ============================================================================
# Self-test
# ============================================================================

def self_test() -> bool:

    passed = 0
    failed = 0

    print()
    print("GLOBAL DIGITAL TWIN SELF TEST")
    print("=" * 78)

    # Test 1
    try:

        model = GlobalDigitalTwin(
            scenario="baseline",
            seed=42,
        )

        history = model.run(10)

        assert len(history) == 10

        print("PASS: basic integrated simulation")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: basic integrated simulation -> {exc}"
        )

        failed += 1

    # Test 2
    try:

        model = GlobalDigitalTwin(
            scenario="sustainable",
            seed=42,
        )

        model.run(10)

        summary = model.summary()

        assert (
            0.0
            <= summary.final_renewable_share
            <= 1.0
        )

        assert (
            0.0
            <= summary.final_food_security
            <= 1.0
        )

        print("PASS: domain bounds")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: domain bounds -> {exc}"
        )

        failed += 1

    # Test 3
    try:

        model = GlobalDigitalTwin(
            scenario="rapid_transition",
            seed=42,
        )

        model.run(15)

        score = model.summary().final_global_score

        assert 0.0 <= score <= 100.0

        print("PASS: global system score")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: global system score -> {exc}"
        )

        failed += 1

    # Test 4
    try:

        result = monte_carlo(
            scenario="baseline",
            periods=5,
            runs=10,
            seed=42,
        )

        assert result["runs"] == 10.0

        assert (
            0.0
            <= result["mean_global_score"]
            <= 100.0
        )

        print("PASS: Monte Carlo integration")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: Monte Carlo integration -> {exc}"
        )

        failed += 1

    # Test 5
    try:

        results = compare_scenarios(
            periods=5,
            seed=42,
        )

        assert len(results) == 5

        print("PASS: multi-domain scenarios")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: multi-domain scenarios -> {exc}"
        )

        failed += 1

    # Test 6
    try:

        model_a = GlobalDigitalTwin(
            scenario="baseline",
            seed=123,
        )

        model_b = GlobalDigitalTwin(
            scenario="baseline",
            seed=123,
        )

        model_a.run(10)
        model_b.run(10)

        score_a = (
            model_a.summary().final_global_score
        )

        score_b = (
            model_b.summary().final_global_score
        )

        assert score_a == score_b

        print("PASS: reproducibility")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: reproducibility -> {exc}"
        )

        failed += 1

    # Test 7
    try:

        model = GlobalDigitalTwin(
            scenario="resilience_first",
            seed=99,
        )

        model.run(10)

        state = model.history[-1]

        assert state.sensors.sensor_confidence > 0.0
        assert state.resilience_index >= 0.0
        assert state.sustainability_index >= 0.0
        assert state.human_welfare_index >= 0.0

        print("PASS: cross-domain state integrity")
        passed += 1

    except Exception as exc:

        print(
            f"FAIL: cross-domain state integrity -> {exc}"
        )

        failed += 1

    print("=" * 78)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")

    success = failed == 0

    if success:
        print("GLOBAL DIGITAL TWIN SELF TEST: PASS")
    else:
        print("GLOBAL DIGITAL TWIN SELF TEST: FAIL")

    print("=" * 78)

    return success


# ============================================================================
# Command-line interface
# ============================================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Global Digital Twin — Integration Gate 1"
        )
    )

    parser.add_argument(
        "--scenario",
        default="baseline",
        choices=list(
            GlobalDigitalTwin.SCENARIOS.keys()
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

        return (
            0
            if self_test()
            else 1
        )

    if args.compare:

        results = compare_scenarios(
            periods=args.periods,
            seed=args.seed,
        )

        print_comparison(results)

        return 0

    model = GlobalDigitalTwin(
        scenario=args.scenario,
        seed=args.seed,
    )

    history = model.run(
        periods=args.periods
    )

    summary = model.summary()

    print_summary(summary)

    if args.monte_carlo:

        results = monte_carlo(
            scenario=args.scenario,
            periods=args.periods,
            runs=args.runs,
            seed=args.seed,
        )

        print()
        print("MONTE CARLO RESULTS")
        print("-" * 78)

        for key, value in results.items():

            print(
                f"{key:<30}: {value:.6f}"
            )

    if args.json:

        save_json(
            filename=args.json,
            summary=summary,
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