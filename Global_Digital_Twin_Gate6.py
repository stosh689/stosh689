"""
Global Digital Twin - Gate 6
Resilience Optimization Engine

Objective
---------
Determine which combination of interventions produces the strongest
global outcome under a constrained resource budget and uncertainty.

Gate 6 extends Gate 5 from:

    "What could happen?"

to:

    "Which intervention portfolio is most robust?"

Design principles
-----------------
- Standard library only
- Deterministic and reproducible
- Explicit assumptions
- Resource constrained
- Multi-objective scoring
- Monte Carlo uncertainty analysis
- Downside-risk penalty
- Equity and human-welfare considerations
- JSON / CSV export
- Built-in self-test

This is a research prototype, not a real-world forecasting authority.
Results depend on the assumptions and parameters used by the model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, List, Tuple


# ============================================================================
# VERSION
# ============================================================================

VERSION = "6.0.0"
GATE_NAME = "GLOBAL DIGITAL TWIN GATE 6"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def safe_mean(values: Iterable[float], default: float = 0.0) -> float:
    values = list(values)
    if not values:
        return default
    return statistics.mean(values)


def percentile(values: List[float], p: float) -> float:
    """Linear-interpolated percentile."""
    if not values:
        return 0.0

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    weight = position - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight


def fingerprint(data: object) -> str:
    payload = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


# ============================================================================
# INTERVENTIONS
# ============================================================================

@dataclass(frozen=True)
class Intervention:
    name: str
    cost: float

    economy: float
    climate: float
    food: float
    energy: float
    resilience: float
    governance: float
    welfare: float
    equity: float

    description: str


INTERVENTIONS: Dict[str, Intervention] = {
    "education": Intervention(
        name="education",
        cost=10.0,
        economy=1.5,
        climate=0.3,
        food=0.7,
        energy=0.3,
        resilience=0.7,
        governance=1.0,
        welfare=2.0,
        equity=2.0,
        description="Human-capital and education investment.",
    ),

    "renewables": Intervention(
        name="renewables",
        cost=15.0,
        economy=1.0,
        climate=2.5,
        food=0.2,
        energy=2.5,
        resilience=1.5,
        governance=0.2,
        welfare=1.0,
        equity=0.8,
        description="Renewable-energy deployment.",
    ),

    "food_resilience": Intervention(
        name="food_resilience",
        cost=12.0,
        economy=0.7,
        climate=0.8,
        food=3.0,
        energy=0.2,
        resilience=2.0,
        governance=0.2,
        welfare=1.8,
        equity=2.0,
        description="Agricultural and food-supply resilience.",
    ),

    "infrastructure": Intervention(
        name="infrastructure",
        cost=18.0,
        economy=2.0,
        climate=0.5,
        food=0.5,
        energy=1.0,
        resilience=3.0,
        governance=0.3,
        welfare=1.8,
        equity=1.0,
        description="Resilient physical infrastructure.",
    ),

    "adaptation": Intervention(
        name="adaptation",
        cost=14.0,
        economy=0.5,
        climate=2.0,
        food=1.2,
        energy=0.5,
        resilience=2.8,
        governance=0.2,
        welfare=1.7,
        equity=1.5,
        description="Climate adaptation and risk reduction.",
    ),

    "governance": Intervention(
        name="governance",
        cost=8.0,
        economy=0.8,
        climate=0.5,
        food=0.4,
        energy=0.4,
        resilience=1.0,
        governance=3.0,
        welfare=1.2,
        equity=1.8,
        description="Institutional transparency and accountability.",
    ),

    "disaster_preparedness": Intervention(
        name="disaster_preparedness",
        cost=11.0,
        economy=0.4,
        climate=0.4,
        food=0.6,
        energy=0.8,
        resilience=3.2,
        governance=0.5,
        welfare=1.8,
        equity=1.6,
        description="Emergency preparedness and response capacity.",
    ),

    "data_sensors": Intervention(
        name="data_sensors",
        cost=7.0,
        economy=0.4,
        climate=0.8,
        food=0.5,
        energy=0.7,
        resilience=1.7,
        governance=1.0,
        welfare=0.7,
        equity=0.5,
        description="Improved sensing, monitoring and data quality.",
    ),
}


# ============================================================================
# SCENARIOS
# ============================================================================

SCENARIOS = {
    "baseline": {
        "growth": 1.0,
        "climate_stress": 0.0,
        "food_stress": 0.0,
        "energy_stress": 0.0,
        "disaster_probability": 0.035,
    },

    "sustainable": {
        "growth": 1.05,
        "climate_stress": -0.35,
        "food_stress": -0.15,
        "energy_stress": -0.20,
        "disaster_probability": 0.030,
    },

    "rapid_transition": {
        "growth": 1.08,
        "climate_stress": -0.45,
        "food_stress": -0.10,
        "energy_stress": -0.25,
        "disaster_probability": 0.028,
    },

    "climate_stress": {
        "growth": 0.85,
        "climate_stress": 0.75,
        "food_stress": 0.35,
        "energy_stress": 0.20,
        "disaster_probability": 0.055,
    },

    "food_stress": {
        "growth": 0.90,
        "climate_stress": 0.25,
        "food_stress": 0.85,
        "energy_stress": 0.10,
        "disaster_probability": 0.045,
    },

    "energy_crisis": {
        "growth": 0.82,
        "climate_stress": 0.20,
        "food_stress": 0.20,
        "energy_stress": 0.90,
        "disaster_probability": 0.045,
    },

    "disaster_stress": {
        "growth": 0.88,
        "climate_stress": 0.35,
        "food_stress": 0.30,
        "energy_stress": 0.30,
        "disaster_probability": 0.080,
    },

    "resilience_first": {
        "growth": 0.98,
        "climate_stress": -0.20,
        "food_stress": -0.20,
        "energy_stress": -0.20,
        "disaster_probability": 0.022,
    },
}


# ============================================================================
# STATE
# ============================================================================

@dataclass
class State:
    period: int = 0

    gdp: float = 100.0
    employment: float = 94.0
    human_welfare: float = 65.0
    equity: float = 60.0

    climate_risk: float = 35.0
    food_security: float = 72.0
    energy_reliability: float = 94.0
    resilience: float = 60.0
    governance: float = 65.0
    data_quality: float = 70.0

    disaster_events: int = 0
    global_score: float = 0.0

    events: List[str] = field(default_factory=list)


@dataclass
class SimulationResult:
    scenario: str
    allocation: Dict[str, int]
    periods: int

    final_score: float
    final_gdp: float
    final_food_security: float
    final_energy_reliability: float
    final_climate_risk: float
    final_resilience: float
    final_welfare: float
    final_equity: float
    final_governance: float

    disaster_events: int
    fingerprint: str


@dataclass
class PortfolioResult:
    allocation: Dict[str, int]
    cost: float

    mean_score: float
    median_score: float
    p05_score: float
    p25_score: float
    p75_score: float
    p95_score: float
    standard_deviation: float

    probability_below_50: float
    probability_above_75: float

    mean_food_security: float
    mean_energy_reliability: float
    mean_climate_risk: float
    mean_resilience: float
    mean_welfare: float
    mean_equity: float

    total_disaster_events: int

    objective_score: float
    fingerprint: str


@dataclass
class OptimizationResult:
    scenario: str
    budget: float
    periods: int
    runs: int

    baseline: PortfolioResult
    optimized: PortfolioResult

    improvement: float
    risk_reduction: float
    welfare_improvement: float
    equity_improvement: float

    candidates_evaluated: int
    fingerprint: str


# ============================================================================
# ENGINE
# ============================================================================

class GlobalDigitalTwinGate6:

    def __init__(
        self,
        scenario: str = "baseline",
        seed: int = 42,
    ):
        if scenario not in SCENARIOS:
            raise ValueError(
                f"Unknown scenario '{scenario}'. "
                f"Available: {', '.join(SCENARIOS)}"
            )

        self.scenario = scenario
        self.config = SCENARIOS[scenario]
        self.seed = seed

    # ----------------------------------------------------------------------
    # Initial state
    # ----------------------------------------------------------------------

    def initial_state(self) -> State:
        return State()

    # ----------------------------------------------------------------------
    # Portfolio effects
    # ----------------------------------------------------------------------

    @staticmethod
    def portfolio_effects(
        allocation: Dict[str, int]
    ) -> Dict[str, float]:

        effects = {
            "economy": 0.0,
            "climate": 0.0,
            "food": 0.0,
            "energy": 0.0,
            "resilience": 0.0,
            "governance": 0.0,
            "welfare": 0.0,
            "equity": 0.0,
        }

        for name, units in allocation.items():

            if name not in INTERVENTIONS:
                continue

            intervention = INTERVENTIONS[name]

            # Diminishing returns prevent unlimited stacking.
            multiplier = 1.0 - 0.08 * max(0, units - 1)
            multiplier = max(0.55, multiplier)

            effects["economy"] += intervention.economy * units * multiplier
            effects["climate"] += intervention.climate * units * multiplier
            effects["food"] += intervention.food * units * multiplier
            effects["energy"] += intervention.energy * units * multiplier
            effects["resilience"] += intervention.resilience * units * multiplier
            effects["governance"] += intervention.governance * units * multiplier
            effects["welfare"] += intervention.welfare * units * multiplier
            effects["equity"] += intervention.equity * units * multiplier

        return effects

    # ----------------------------------------------------------------------
    # Simulation
    # ----------------------------------------------------------------------

    def simulate(
        self,
        allocation: Dict[str, int] | None = None,
        periods: int = 20,
        seed: int | None = None,
    ) -> SimulationResult:

        if allocation is None:
            allocation = {}

        rng = random.Random(self.seed if seed is None else seed)

        state = self.initial_state()
        effects = self.portfolio_effects(allocation)

        for period in range(1, periods + 1):

            state.period = period

            # Random uncertainty.
            economic_noise = rng.gauss(0.0, 0.25)
            climate_noise = rng.gauss(0.0, 0.35)
            food_noise = rng.gauss(0.0, 0.30)
            energy_noise = rng.gauss(0.0, 0.30)

            # --------------------------------------------------------------
            # Economy
            # --------------------------------------------------------------

            growth = (
                self.config["growth"]
                + effects["economy"] * 0.018
                - self.config["energy_stress"] * 0.20
                - self.config["climate_stress"] * 0.10
                + economic_noise / 100.0
            )

            state.gdp *= max(0.80, growth)

            employment_change = (
                effects["economy"] * 0.03
                + effects["welfare"] * 0.01
                - self.config["energy_stress"] * 0.15
                - self.config["climate_stress"] * 0.08
                + economic_noise * 0.05
            )

            state.employment = clamp(
                state.employment + employment_change,
                70.0,
                99.5,
            )

            # --------------------------------------------------------------
            # Climate
            # --------------------------------------------------------------

            climate_change = (
                self.config["climate_stress"] * 0.45
                - effects["climate"] * 0.035
                - effects["resilience"] * 0.010
                + climate_noise * 0.20
            )

            state.climate_risk = clamp(
                state.climate_risk + climate_change,
                0.0,
                100.0,
            )

            # --------------------------------------------------------------
            # Energy
            # --------------------------------------------------------------

            energy_change = (
                effects["energy"] * 0.055
                + effects["resilience"] * 0.012
                - self.config["energy_stress"] * 0.60
                - climate_noise * 0.05
                + energy_noise * 0.15
            )

            state.energy_reliability = clamp(
                state.energy_reliability + energy_change,
                40.0,
                100.0,
            )

            # --------------------------------------------------------------
            # Food
            # --------------------------------------------------------------

            food_change = (
                effects["food"] * 0.065
                + effects["resilience"] * 0.018
                - self.config["food_stress"] * 0.65
                - self.config["climate_stress"] * 0.15
                + food_noise * 0.15
            )

            state.food_security = clamp(
                state.food_security + food_change,
                30.0,
                100.0,
            )

            # --------------------------------------------------------------
            # Governance
            # --------------------------------------------------------------

            governance_change = (
                effects["governance"] * 0.055
                + effects["data_quality"] * 0.01
            )

            state.governance = clamp(
                state.governance + governance_change,
                20.0,
                100.0,
            )

            # --------------------------------------------------------------
            # Resilience
            # --------------------------------------------------------------

            resilience_change = (
                effects["resilience"] * 0.060
                + effects["governance"] * 0.018
                - self.config["climate_stress"] * 0.12
                + effects["data_quality"] * 0.005
            )

            state.resilience = clamp(
                state.resilience + resilience_change,
                20.0,
                100.0,
            )

            # --------------------------------------------------------------
            # Data quality
            # --------------------------------------------------------------

            data_change = effects["resilience"] * 0.012

            state.data_quality = clamp(
                state.data_quality + data_change,
                20.0,
                100.0,
            )

            # --------------------------------------------------------------
            # Human welfare
            # --------------------------------------------------------------

            welfare_change = (
                effects["welfare"] * 0.045
                + effects["equity"] * 0.020
                + (state.employment - 90.0) * 0.015
                - state.climate_risk * 0.004
                - self.config["food_stress"] * 0.20
            )

            state.human_welfare = clamp(
                state.human_welfare + welfare_change,
                20.0,
                100.0,
            )

            # --------------------------------------------------------------
            # Equity
            # --------------------------------------------------------------

            equity_change = (
                effects["equity"] * 0.050
                + effects["governance"] * 0.015
                - self.config["food_stress"] * 0.05
            )

            state.equity = clamp(
                state.equity + equity_change,
                20.0,
                100.0,
            )

            # --------------------------------------------------------------
            # Disaster event
            # --------------------------------------------------------------

            preparedness_factor = (
                1.0
                - min(0.70, effects["resilience"] * 0.012)
                - min(0.20, effects["data_quality"] * 0.002)
            )

            disaster_probability = (
                self.config["disaster_probability"]
                * max(0.20, preparedness_factor)
            )

            if rng.random() < disaster_probability:

                state.disaster_events += 1

                damage = rng.uniform(1.0, 5.0)

                state.gdp *= max(0.94, 1.0 - damage / 100.0)

                state.food_security = clamp(
                    state.food_security - damage * 0.60
                )

                state.energy_reliability = clamp(
                    state.energy_reliability - damage * 0.50
                )

                state.resilience = clamp(
                    state.resilience - damage * 0.30
                )

                state.human_welfare = clamp(
                    state.human_welfare - damage * 0.50
                )

                state.events.append(
                    f"period_{period}:disaster:{damage:.2f}"
                )

        state.global_score = self.global_score(state)

        return SimulationResult(
            scenario=self.scenario,
            allocation=dict(allocation),
            periods=periods,
            final_score=state.global_score,
            final_gdp=state.gdp,
            final_food_security=state.food_security,
            final_energy_reliability=state.energy_reliability,
            final_climate_risk=state.climate_risk,
            final_resilience=state.resilience,
            final_welfare=state.human_welfare,
            final_equity=state.equity,
            final_governance=state.governance,
            disaster_events=state.disaster_events,
            fingerprint=fingerprint(asdict(state)),
        )

    # ----------------------------------------------------------------------
    # Global objective
    # ----------------------------------------------------------------------

    @staticmethod
    def global_score(state: State) -> float:

        climate_health = 100.0 - state.climate_risk

        score = (
            state.human_welfare * 0.22
            + state.gdp / 2.0 * 0.12
            + state.employment * 0.08
            + state.food_security * 0.13
            + state.energy_reliability * 0.10
            + state.resilience * 0.13
            + state.governance * 0.08
            + climate_health * 0.08
            + state.equity * 0.06
        )

        return clamp(score)

    # ----------------------------------------------------------------------
    # Monte Carlo
    # ----------------------------------------------------------------------

    def monte_carlo(
        self,
        allocation: Dict[str, int],
        periods: int = 20,
        runs: int = 100,
        seed: int | None = None,
    ) -> PortfolioResult:

        base_seed = self.seed if seed is None else seed

        results: List[SimulationResult] = []

        for run in range(runs):

            result = self.simulate(
                allocation=allocation,
                periods=periods,
                seed=base_seed + run,
            )

            results.append(result)

        scores = [r.final_score for r in results]

        mean_score = safe_mean(scores)
        median_score = statistics.median(scores) if scores else 0.0

        p05 = percentile(scores, 0.05)
        p25 = percentile(scores, 0.25)
        p75 = percentile(scores, 0.75)
        p95 = percentile(scores, 0.95)

        std = statistics.stdev(scores) if len(scores) > 1 else 0.0

        below_50 = (
            sum(score < 50.0 for score in scores)
            / max(1, len(scores))
        )

        above_75 = (
            sum(score > 75.0 for score in scores)
            / max(1, len(scores))
        )

        costs = self.portfolio_cost(allocation)

        mean_food = safe_mean(
            r.final_food_security for r in results
        )

        mean_energy = safe_mean(
            r.final_energy_reliability for r in results
        )

        mean_climate = safe_mean(
            r.final_climate_risk for r in results
        )

        mean_resilience = safe_mean(
            r.final_resilience for r in results
        )

        mean_welfare = safe_mean(
            r.final_welfare for r in results
        )

        mean_equity = safe_mean(
            r.final_equity for r in results
        )

        total_disasters = sum(
            r.disaster_events for r in results
        )

        objective = self.portfolio_objective(
            mean_score=mean_score,
            p05_score=p05,
            probability_below_50=below_50,
            food=mean_food,
            energy=mean_energy,
            climate=mean_climate,
            resilience=mean_resilience,
            welfare=mean_welfare,
            equity=mean_equity,
            cost=costs,
        )

        return PortfolioResult(
            allocation=dict(allocation),
            cost=costs,
            mean_score=mean_score,
            median_score=median_score,
            p05_score=p05,
            p25_score=p25,
            p75_score=p75,
            p95_score=p95,
            standard_deviation=std,
            probability_below_50=below_50,
            probability_above_75=above_75,
            mean_food_security=mean_food,
            mean_energy_reliability=mean_energy,
            mean_climate_risk=mean_climate,
            mean_resilience=mean_resilience,
            mean_welfare=mean_welfare,
            mean_equity=mean_equity,
            total_disaster_events=total_disasters,
            objective_score=objective,
            fingerprint=fingerprint({
                "allocation": allocation,
                "scenario": self.scenario,
                "periods": periods,
                "runs": runs,
                "seed": base_seed,
            }),
        )

    # ----------------------------------------------------------------------
    # Cost
    # ----------------------------------------------------------------------

    @staticmethod
    def portfolio_cost(
        allocation: Dict[str, int]
    ) -> float:

        total = 0.0

        for name, units in allocation.items():

            if name not in INTERVENTIONS:
                continue

            total += (
                INTERVENTIONS[name].cost
                * max(0, units)
            )

        return total

    # ----------------------------------------------------------------------
    # Objective function
    # ----------------------------------------------------------------------

    @staticmethod
    def portfolio_objective(
        mean_score: float,
        p05_score: float,
        probability_below_50: float,
        food: float,
        energy: float,
        climate: float,
        resilience: float,
        welfare: float,
        equity: float,
        cost: float,
    ) -> float:

        climate_health = 100.0 - climate

        raw = (
            mean_score * 0.30
            + p05_score * 0.18
            + food * 0.10
            + energy * 0.08
            + resilience * 0.10
            + welfare * 0.10
            + equity * 0.07
            + climate_health * 0.07
        )

        # Strong penalty for catastrophic downside.
        risk_penalty = probability_below_50 * 20.0

        # Small budget penalty.
        cost_penalty = cost * 0.015

        return raw - risk_penalty - cost_penalty

    # ----------------------------------------------------------------------
    # Generate candidate portfolios
    # ----------------------------------------------------------------------

    def generate_candidates(
        self,
        budget: float,
        max_units: int = 2,
    ) -> Iterable[Dict[str, int]]:

        names = list(INTERVENTIONS.keys())

        # Include no-intervention baseline.
        yield {}

        for values in itertools.product(
            range(max_units + 1),
            repeat=len(names),
        ):

            allocation = {
                name: value
                for name, value in zip(names, values)
                if value > 0
            }

            if not allocation:
                continue

            cost = self.portfolio_cost(allocation)

            if cost <= budget:
                yield allocation

    # ----------------------------------------------------------------------
    # Optimization
    # ----------------------------------------------------------------------

    def optimize(
        self,
        budget: float = 60.0,
        periods: int = 20,
        runs: int = 100,
        max_units: int = 1,
    ) -> OptimizationResult:

        baseline = self.monte_carlo(
            allocation={},
            periods=periods,
            runs=runs,
            seed=self.seed,
        )

        best: PortfolioResult | None = None
        candidates = 0

        for allocation in self.generate_candidates(
            budget=budget,
            max_units=max_units,
        ):

            candidates += 1

            result = self.monte_carlo(
                allocation=allocation,
                periods=periods,
                runs=runs,
                seed=self.seed,
            )

            if best is None:
                best = result
                continue

            if result.objective_score > best.objective_score:
                best = result

        if best is None:
            raise RuntimeError("No feasible portfolio found.")

        improvement = (
            best.mean_score
            - baseline.mean_score
        )

        risk_reduction = (
            baseline.probability_below_50
            - best.probability_below_50
        )

        welfare_improvement = (
            best.mean_welfare
            - baseline.mean_welfare
        )

        equity_improvement = (
            best.mean_equity
            - baseline.mean_equity
        )

        return OptimizationResult(
            scenario=self.scenario,
            budget=budget,
            periods=periods,
            runs=runs,
            baseline=baseline,
            optimized=best,
            improvement=improvement,
            risk_reduction=risk_reduction,
            welfare_improvement=welfare_improvement,
            equity_improvement=equity_improvement,
            candidates_evaluated=candidates,
            fingerprint=fingerprint({
                "scenario": self.scenario,
                "budget": budget,
                "periods": periods,
                "runs": runs,
                "baseline": asdict(baseline),
                "optimized": asdict(best),
            }),
        )


# ============================================================================
# REPORTING
# ============================================================================

def allocation_text(allocation: Dict[str, int]) -> str:

    if not allocation:
        return "none"

    return ", ".join(
        f"{name} x{units}"
        for name, units in sorted(allocation.items())
    )


def print_portfolio(
    title: str,
    portfolio: PortfolioResult,
) -> None:

    print()
    print(title)
    print("=" * 72)

    print(f"Allocation:              {allocation_text(portfolio.allocation)}")
    print(f"Cost:                    {portfolio.cost:.2f}")

    print()
    print(f"Mean final score:        {portfolio.mean_score:.2f}")
    print(f"Median final score:      {portfolio.median_score:.2f}")
    print(f"5th percentile:          {portfolio.p05_score:.2f}")
    print(f"25th percentile:         {portfolio.p25_score:.2f}")
    print(f"75th percentile:         {portfolio.p75_score:.2f}")
    print(f"95th percentile:         {portfolio.p95_score:.2f}")
    print(f"Standard deviation:      {portfolio.standard_deviation:.2f}")

    print()
    print(
        f"P(score < 50):           "
        f"{portfolio.probability_below_50 * 100:.2f}%"
    )

    print(
        f"P(score > 75):           "
        f"{portfolio.probability_above_75 * 100:.2f}%"
    )

    print()
    print(f"Food security:           {portfolio.mean_food_security:.2f}")
    print(f"Energy reliability:      {portfolio.mean_energy_reliability:.2f}")
    print(f"Climate risk:            {portfolio.mean_climate_risk:.2f}")
    print(f"Resilience:              {portfolio.mean_resilience:.2f}")
    print(f"Human welfare:           {portfolio.mean_welfare:.2f}")
    print(f"Equity:                  {portfolio.mean_equity:.2f}")

    print()
    print(f"Total disaster events:   {portfolio.total_disaster_events}")
    print(f"Objective score:         {portfolio.objective_score:.2f}")
    print(f"Fingerprint:             {portfolio.fingerprint}")


def print_optimization(
    result: OptimizationResult,
) -> None:

    print()
    print("=" * 72)
    print(f"{GATE_NAME} - OPTIMIZATION")
    print("=" * 72)

    print(f"Version:                 {VERSION}")
    print(f"Scenario:                {result.scenario}")
    print(f"Budget:                  {result.budget:.2f}")
    print(f"Periods:                 {result.periods}")
    print(f"Monte Carlo runs:        {result.runs}")
    print(
        f"Candidates evaluated:   "
        f"{result.candidates_evaluated}"
    )

    print_portfolio(
        "BASELINE PORTFOLIO",
        result.baseline,
    )

    print_portfolio(
        "OPTIMIZED PORTFOLIO",
        result.optimized,
    )

    print()
    print("OPTIMIZATION IMPACT")
    print("=" * 72)

    print(
        f"Mean score improvement:  "
        f"{result.improvement:+.2f}"
    )

    print(
        f"Risk reduction:          "
        f"{result.risk_reduction * 100:+.2f} percentage points"
    )

    print(
        f"Welfare improvement:     "
        f"{result.welfare_improvement:+.2f}"
    )

    print(
        f"Equity improvement:      "
        f"{result.equity_improvement:+.2f}"
    )

    print()
    print(f"Gate 6 fingerprint:       {result.fingerprint}")

    print()
    print("=" * 72)


# ============================================================================
# JSON / CSV
# ============================================================================

def save_json(
    result: OptimizationResult,
    path: str,
) -> None:

    data = asdict(result)

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            data,
            handle,
            indent=2,
            sort_keys=True,
        )


def save_csv(
    result: OptimizationResult,
    path: str,
) -> None:

    rows = [
        {
            "portfolio": "baseline",
            "scenario": result.scenario,
            "cost": result.baseline.cost,
            "mean_score": result.baseline.mean_score,
            "p05_score": result.baseline.p05_score,
            "p95_score": result.baseline.p95_score,
            "probability_below_50":
                result.baseline.probability_below_50,
            "food_security":
                result.baseline.mean_food_security,
            "energy_reliability":
                result.baseline.mean_energy_reliability,
            "climate_risk":
                result.baseline.mean_climate_risk,
            "resilience":
                result.baseline.mean_resilience,
            "welfare":
                result.baseline.mean_welfare,
            "equity":
                result.baseline.mean_equity,
            "objective":
                result.baseline.objective_score,
            "allocation":
                allocation_text(result.baseline.allocation),
        },
        {
            "portfolio": "optimized",
            "scenario": result.scenario,
            "cost": result.optimized.cost,
            "mean_score": result.optimized.mean_score,
            "p05_score": result.optimized.p05_score,
            "p95_score": result.optimized.p95_score,
            "probability_below_50":
                result.optimized.probability_below_50,
            "food_security":
                result.optimized.mean_food_security,
            "energy_reliability":
                result.optimized.mean_energy_reliability,
            "climate_risk":
                result.optimized.mean_climate_risk,
            "resilience":
                result.optimized.mean_resilience,
            "welfare":
                result.optimized.mean_welfare,
            "equity":
                result.optimized.mean_equity,
            "objective":
                result.optimized.objective_score,
            "allocation":
                allocation_text(result.optimized.allocation),
        },
    ]

    fieldnames = list(rows[0].keys())

    with open(
        path,
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================================
# SELF TEST
# ============================================================================

def self_test() -> bool:

    print()
    print(f"{GATE_NAME} SELF TEST")
    print("=" * 72)

    passed = 0
    failed = 0

    def check(
        name: str,
        condition: bool,
    ) -> None:

        nonlocal passed, failed

        if condition:
            print(f"PASS: {name}")
            passed += 1
        else:
            print(f"FAIL: {name}")
            failed += 1

    # Test 1
    check(
        "intervention registry",
        len(INTERVENTIONS) >= 8,
    )

    # Test 2
    engine = GlobalDigitalTwinGate6(
        scenario="baseline",
        seed=42,
    )

    result_a = engine.simulate(
        allocation={},
        periods=10,
        seed=42,
    )

    check(
        "basic simulation",
        0.0 <= result_a.final_score <= 100.0,
    )

    # Test 3
    result_b = engine.simulate(
        allocation={},
        periods=10,
        seed=42,
    )

    check(
        "deterministic simulation",
        result_a.fingerprint == result_b.fingerprint,
    )

    # Test 4
    cost = engine.portfolio_cost(
        {
            "education": 1,
            "renewables": 1,
        }
    )

    check(
        "portfolio costing",
        abs(cost - 25.0) < 1e-9,
    )

    # Test 5
    mc_a = engine.monte_carlo(
        allocation={},
        periods=10,
        runs=20,
        seed=42,
    )

    mc_b = engine.monte_carlo(
        allocation={},
        periods=10,
        runs=20,
        seed=42,
    )

    check(
        "Monte Carlo reproducibility",
        mc_a.fingerprint == mc_b.fingerprint,
    )

    # Test 6
    candidate_list = list(
        engine.generate_candidates(
            budget=20.0,
            max_units=1,
        )
    )

    check(
        "budget constraint",
        all(
            engine.portfolio_cost(candidate) <= 20.0 + 1e-9
            for candidate in candidate_list
        ),
    )

    # Test 7
    optimization = engine.optimize(
        budget=25.0,
        periods=5,
        runs=10,
        max_units=1,
    )

    check(
        "optimization result",
        optimization.optimized.cost <= 25.0 + 1e-9,
    )

    # Test 8
    check(
        "optimization fingerprint",
        len(optimization.fingerprint) == 64,
    )

    print()
    print("=" * 72)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 72)

    if failed == 0:
        print(f"{GATE_NAME}: PASS")
        return True

    print(f"{GATE_NAME}: FAIL")
    return False


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Global Digital Twin Gate 6 - "
            "Resilience Optimization Engine"
        )
    )

    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS.keys()),
        default="baseline",
    )

    parser.add_argument(
        "--budget",
        type=float,
        default=60.0,
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
        "--max-units",
        type=int,
        default=1,
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
        "--json",
        dest="json_path",
        default=None,
    )

    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=None,
    )

    return parser


def main() -> int:

    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return 0 if self_test() else 1

    if args.budget < 0:
        parser.error("--budget must be >= 0")

    if args.periods <= 0:
        parser.error("--periods must be > 0")

    if args.runs <= 0:
        parser.error("--runs must be > 0")

    if args.max_units < 0:
        parser.error("--max-units must be >= 0")

    engine = GlobalDigitalTwinGate6(
        scenario=args.scenario,
        seed=args.seed,
    )

    result = engine.optimize(
        budget=args.budget,
        periods=args.periods,
        runs=args.runs,
        max_units=args.max_units,
    )

    print_optimization(result)

    if args.json_path:
        save_json(
            result,
            args.json_path,
        )

        print()
        print(
            f"JSON written to: {args.json_path}"
        )

    if args.csv_path:
        save_csv(
            result,
            args.csv_path,
        )

        print(
            f"CSV written to: {args.csv_path}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())