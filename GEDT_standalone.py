"""
GEDT - Global Economic Digital Twin
====================================

Standalone computational economics simulation.

Version: 1.0.0
Python: 3.9+
External dependencies: NONE

Purpose
-------
GEDT models a simplified economy containing households/firms as agents
and explores relationships between:

- Human capital
- Education
- Investment
- Innovation
- Productivity
- Employment
- Economic shocks
- Inequality
- Economic output
- Sustainability

The model is intentionally transparent and reproducible.

This is a research prototype, NOT a forecasting model for real-world
economic policy or investment decisions.

License: MIT
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Tuple


VERSION = "1.0.0"


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Agent:
    """Represents one economic agent."""

    agent_id: int
    human_capital: float
    wealth: float
    productivity: float
    education: float
    employment: float
    innovation: float
    sustainability: float


@dataclass
class EconomyState:
    """Represents the economy at one point in time."""

    period: int
    gdp: float
    productivity: float
    employment: float
    unemployment: float
    average_wealth: float
    inequality: float
    human_capital: float
    innovation: float
    education: float
    sustainability: float


@dataclass
class ScenarioResult:
    """Summary of one complete simulation."""

    scenario: str
    periods: int
    agents: int
    final_gdp: float
    gdp_growth: float
    final_employment: float
    final_unemployment: float
    final_inequality: float
    final_human_capital: float
    final_innovation: float
    final_education: float
    final_sustainability: float
    total_shocks: int


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clamp(value: float, minimum: float, maximum: float) -> float:
    """Keep a value inside a defined range."""
    return max(minimum, min(maximum, value))


def safe_mean(values: List[float]) -> float:
    """Return a safe arithmetic mean."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def safe_growth(initial: float, final: float) -> float:
    """Calculate percentage growth safely."""
    if initial == 0:
        return 0.0
    return ((final - initial) / abs(initial)) * 100.0


def gini(values: List[float]) -> float:
    """
    Calculate the Gini coefficient.

    0 = perfect equality
    1 = maximum inequality
    """
    if not values:
        return 0.0

    cleaned = [max(0.0, float(v)) for v in values]

    total = sum(cleaned)

    if total <= 0:
        return 0.0

    ordered = sorted(cleaned)
    n = len(ordered)

    weighted_sum = sum(
        (index + 1) * value
        for index, value in enumerate(ordered)
    )

    result = (
        (2.0 * weighted_sum) / (n * total)
        - (n + 1.0) / n
    )

    return clamp(result, 0.0, 1.0)


# ============================================================
# ECONOMIC DIGITAL TWIN
# ============================================================

class GEDT:
    """
    Global Economic Digital Twin simulation engine.
    """

    def __init__(
        self,
        agents: int = 100,
        periods: int = 50,
        seed: int = 42,
        scenario: str = "baseline",
    ):
        if agents < 2:
            raise ValueError("agents must be at least 2")

        if periods < 1:
            raise ValueError("periods must be at least 1")

        self.agent_count = agents
        self.periods = periods
        self.seed = seed
        self.scenario = scenario.lower()

        self.rng = random.Random(seed)

        self.population: List[Agent] = []
        self.history: List[EconomyState] = []

        self.total_shocks = 0

        self._initialize_population()

    # --------------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------------

    def _initialize_population(self) -> None:
        """Create the initial population."""

        for agent_id in range(self.agent_count):

            education = clamp(
                self.rng.gauss(0.60, 0.15),
                0.10,
                1.00,
            )

            human_capital = clamp(
                education + self.rng.gauss(0.05, 0.10),
                0.10,
                1.50,
            )

            wealth = max(
                1000.0,
                self.rng.lognormvariate(
                    math.log(25000.0),
                    0.45,
                ),
            )

            productivity = clamp(
                0.70
                + human_capital * 0.40
                + self.rng.gauss(0.0, 0.10),
                0.20,
                2.50,
            )

            employment = clamp(
                self.rng.gauss(0.90, 0.08),
                0.50,
                1.00,
            )

            innovation = clamp(
                self.rng.gauss(0.50, 0.15),
                0.00,
                1.00,
            )

            sustainability = clamp(
                self.rng.gauss(0.55, 0.15),
                0.00,
                1.00,
            )

            self.population.append(
                Agent(
                    agent_id=agent_id,
                    human_capital=human_capital,
                    wealth=wealth,
                    productivity=productivity,
                    education=education,
                    employment=employment,
                    innovation=innovation,
                    sustainability=sustainability,
                )
            )

    # --------------------------------------------------------
    # SCENARIO PARAMETERS
    # --------------------------------------------------------

    def parameters(self) -> Dict[str, float]:
        """Return parameters for the selected scenario."""

        scenarios = {
            "baseline": {
                "education": 0.020,
                "investment": 0.030,
                "innovation": 0.025,
                "sustainability": 0.015,
                "shock_probability": 0.05,
                "shock_strength": 0.08,
            },
            "education": {
                "education": 0.055,
                "investment": 0.030,
                "innovation": 0.030,
                "sustainability": 0.020,
                "shock_probability": 0.05,
                "shock_strength": 0.08,
            },
            "innovation": {
                "education": 0.025,
                "investment": 0.045,
                "innovation": 0.070,
                "sustainability": 0.020,
                "shock_probability": 0.05,
                "shock_strength": 0.08,
            },
            "sustainable": {
                "education": 0.035,
                "investment": 0.035,
                "innovation": 0.045,
                "sustainability": 0.070,
                "shock_probability": 0.04,
                "shock_strength": 0.06,
            },
            "crisis": {
                "education": 0.010,
                "investment": 0.005,
                "innovation": 0.005,
                "sustainability": 0.005,
                "shock_probability": 0.15,
                "shock_strength": 0.15,
            },
        }

        if self.scenario not in scenarios:
            raise ValueError(
                "Unknown scenario: "
                + self.scenario
                + ". Choose from: "
                + ", ".join(scenarios.keys())
            )

        return scenarios[self.scenario]

    # --------------------------------------------------------
    # AGENT UPDATE
    # --------------------------------------------------------

    def update_agent(
        self,
        agent: Agent,
        params: Dict[str, float],
    ) -> None:
        """Update one agent for one period."""

        # Education increases human capital.
        education_gain = (
            params["education"]
            * (1.0 - agent.education)
        )

        agent.education = clamp(
            agent.education + education_gain,
            0.0,
            1.0,
        )

        # Human capital responds to education.
        agent.human_capital = clamp(
            agent.human_capital
            + 0.030 * agent.education
            - 0.005 * (1.0 - agent.education),
            0.10,
            2.50,
        )

        # Innovation responds to human capital and investment.
        innovation_gain = (
            params["innovation"]
            * agent.human_capital
            * (0.5 + agent.education)
        )

        agent.innovation = clamp(
            agent.innovation + innovation_gain,
            0.0,
            2.50,
        )

        # Investment improves productivity.
        investment_effect = (
            params["investment"]
            * (0.5 + agent.innovation)
        )

        agent.productivity = clamp(
            agent.productivity
            + investment_effect
            + 0.020 * agent.human_capital
            - 0.010 * (1.0 - agent.sustainability),
            0.20,
            5.00,
        )

        # Sustainability improves gradually.
        sustainability_gain = (
            params["sustainability"]
            * (1.0 - agent.sustainability)
        )

        agent.sustainability = clamp(
            agent.sustainability + sustainability_gain,
            0.0,
            1.0,
        )

        # Employment responds to productivity.
        employment_change = (
            0.015 * (agent.productivity - 1.0)
            + 0.010 * agent.human_capital
            - 0.005 * (1.0 - agent.sustainability)
        )

        agent.employment = clamp(
            agent.employment + employment_change,
            0.0,
            1.0,
        )

        # Wealth accumulation.
        income = (
            25000.0
            * agent.productivity
            * agent.employment
        )

        investment_cost = (
            income
            * params["investment"]
            * 0.25
        )

        consumption = income * 0.65

        wealth_change = (
            income
            - consumption
            - investment_cost
        )

        agent.wealth = max(
            500.0,
            agent.wealth + wealth_change,
        )

    # --------------------------------------------------------
    # SHOCKS
    # --------------------------------------------------------

    def apply_shock(
        self,
        params: Dict[str, float],
    ) -> bool:
        """
        Randomly apply an economy-wide shock.

        Returns True if a shock occurred.
        """

        if self.rng.random() >= params["shock_probability"]:
            return False

        strength = params["shock_strength"]

        self.total_shocks += 1

        for agent in self.population:

            agent.productivity *= (
                1.0 - strength
            )

            agent.employment *= (
                1.0 - strength * 0.50
            )

            agent.wealth *= (
                1.0 - strength * 0.25
            )

            agent.innovation *= (
                1.0 - strength * 0.20
            )

        return True

    # --------------------------------------------------------
    # ECONOMIC MEASUREMENT
    # --------------------------------------------------------

    def measure(self, period: int) -> EconomyState:
        """Calculate macroeconomic indicators."""

        gdp = sum(
            25000.0
            * agent.productivity
            * agent.employment
            for agent in self.population
        )

        productivity = safe_mean(
            [a.productivity for a in self.population]
        )

        employment = safe_mean(
            [a.employment for a in self.population]
        )

        unemployment = 1.0 - employment

        average_wealth = safe_mean(
            [a.wealth for a in self.population]
        )

        inequality = gini(
            [a.wealth for a in self.population]
        )

        human_capital = safe_mean(
            [a.human_capital for a in self.population]
        )

        innovation = safe_mean(
            [a.innovation for a in self.population]
        )

        education = safe_mean(
            [a.education for a in self.population]
        )

        sustainability = safe_mean(
            [a.sustainability for a in self.population]
        )

        return EconomyState(
            period=period,
            gdp=gdp,
            productivity=productivity,
            employment=employment,
            unemployment=unemployment,
            average_wealth=average_wealth,
            inequality=inequality,
            human_capital=human_capital,
            innovation=innovation,
            education=education,
            sustainability=sustainability,
        )

    # --------------------------------------------------------
    # SIMULATION
    # --------------------------------------------------------

    def run(self) -> List[EconomyState]:
        """Run the complete simulation."""

        params = self.parameters()

        self.history = []

        initial_state = self.measure(0)
        self.history.append(initial_state)

        for period in range(1, self.periods + 1):

            for agent in self.population:
                self.update_agent(agent, params)

            self.apply_shock(params)

            state = self.measure(period)

            self.history.append(state)

        return self.history

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    def summary(self) -> ScenarioResult:
        """Return a summarized simulation result."""

        if not self.history:
            raise RuntimeError(
                "Simulation has not been run."
            )

        initial = self.history[0]
        final = self.history[-1]

        return ScenarioResult(
            scenario=self.scenario,
            periods=self.periods,
            agents=self.agent_count,
            final_gdp=final.gdp,
            gdp_growth=safe_growth(
                initial.gdp,
                final.gdp,
            ),
            final_employment=final.employment,
            final_unemployment=final.unemployment,
            final_inequality=final.inequality,
            final_human_capital=final.human_capital,
            final_innovation=final.innovation,
            final_education=final.education,
            final_sustainability=final.sustainability,
            total_shocks=self.total_shocks,
        )


# ============================================================
# MONTE CARLO
# ============================================================

def monte_carlo(
    scenario: str,
    runs: int = 100,
    agents: int = 100,
    periods: int = 50,
    seed: int = 42,
) -> Dict[str, object]:
    """
    Run repeated GEDT simulations.

    Returns mean and standard deviation for major indicators.
    """

    if runs < 1:
        raise ValueError("runs must be at least 1")

    results: List[ScenarioResult] = []

    for run_number in range(runs):

        model = GEDT(
            agents=agents,
            periods=periods,
            seed=seed + run_number,
            scenario=scenario,
        )

        model.run()

        results.append(model.summary())

    gdp_values = [
        result.final_gdp
        for result in results
    ]

    growth_values = [
        result.gdp_growth
        for result in results
    ]

    unemployment_values = [
        result.final_unemployment
        for result in results
    ]

    inequality_values = [
        result.final_inequality
        for result in results
    ]

    innovation_values = [
        result.final_innovation
        for result in results
    ]

    education_values = [
        result.final_education
        for result in results
    ]

    sustainability_values = [
        result.final_sustainability
        for result in results
    ]

    return {
        "scenario": scenario,
        "runs": runs,
        "agents": agents,
        "periods": periods,

        "gdp_mean": safe_mean(gdp_values),
        "gdp_std": statistics.pstdev(gdp_values),

        "growth_mean": safe_mean(growth_values),
        "growth_std": statistics.pstdev(growth_values),

        "unemployment_mean": safe_mean(
            unemployment_values
        ),

        "inequality_mean": safe_mean(
            inequality_values
        ),

        "innovation_mean": safe_mean(
            innovation_values
        ),

        "education_mean": safe_mean(
            education_values
        ),

        "sustainability_mean": safe_mean(
            sustainability_values
        ),
    }


# ============================================================
# SCENARIO COMPARISON
# ============================================================

def compare_scenarios(
    scenarios: List[str],
    agents: int,
    periods: int,
    runs: int,
    seed: int,
) -> List[Dict[str, object]]:
    """Compare multiple economic scenarios."""

    output = []

    for index, scenario in enumerate(scenarios):

        result = monte_carlo(
            scenario=scenario,
            runs=runs,
            agents=agents,
            periods=periods,
            seed=seed + index * 10000,
        )

        output.append(result)

    return output


# ============================================================
# FILE OUTPUT
# ============================================================

def save_history_csv(
    history: List[EconomyState],
    filename: str,
) -> None:
    """Save time-series results to CSV."""

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(
                asdict(history[0]).keys()
            ),
        )

        writer.writeheader()

        for state in history:
            writer.writerow(asdict(state))


def save_json(
    data: object,
    filename: str,
) -> None:
    """Save JSON output."""

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


# ============================================================
# REPORTING
# ============================================================

def print_summary(result: ScenarioResult) -> None:
    """Print one scenario summary."""

    print()
    print("=" * 60)
    print("GEDT SCENARIO RESULT")
    print("=" * 60)

    print(f"Scenario:              {result.scenario}")
    print(f"Agents:                {result.agents}")
    print(f"Periods:               {result.periods}")
    print(f"Final GDP:             {result.final_gdp:,.2f}")
    print(f"GDP growth:            {result.gdp_growth:.2f}%")
    print(
        f"Employment:            "
        f"{result.final_employment * 100:.2f}%"
    )
    print(
        f"Unemployment:          "
        f"{result.final_unemployment * 100:.2f}%"
    )
    print(
        f"Inequality (Gini):     "
        f"{result.final_inequality:.4f}"
    )
    print(
        f"Human capital:         "
        f"{result.final_human_capital:.4f}"
    )
    print(
        f"Innovation:            "
        f"{result.final_innovation:.4f}"
    )
    print(
        f"Education:             "
        f"{result.final_education:.4f}"
    )
    print(
        f"Sustainability:        "
        f"{result.final_sustainability:.4f}"
    )
    print(
        f"Economic shocks:       "
        f"{result.total_shocks}"
    )

    print("=" * 60)


def print_monte_carlo(result: Dict[str, object]) -> None:
    """Print Monte Carlo results."""

    print()
    print("=" * 60)
    print("GEDT MONTE CARLO")
    print("=" * 60)

    print("Scenario:", result["scenario"])
    print("Runs:", result["runs"])
    print("Agents:", result["agents"])
    print("Periods:", result["periods"])

    print()
    print(
        f"GDP mean:              "
        f"{float(result['gdp_mean']):,.2f}"
    )

    print(
        f"GDP standard deviation:"
        f" {float(result['gdp_std']):,.2f}"
    )

    print(
        f"Growth mean:            "
        f"{float(result['growth_mean']):.2f}%"
    )

    print(
        f"Growth standard deviation:"
        f" {float(result['growth_std']):.2f}%"
    )

    print(
        f"Unemployment mean:     "
        f"{float(result['unemployment_mean']) * 100:.2f}%"
    )

    print(
        f"Inequality mean:       "
        f"{float(result['inequality_mean']):.4f}"
    )

    print(
        f"Innovation mean:       "
        f"{float(result['innovation_mean']):.4f}"
    )

    print(
        f"Education mean:        "
        f"{float(result['education_mean']):.4f}"
    )

    print(
        f"Sustainability mean:   "
        f"{float(result['sustainability_mean']):.4f}"
    )

    print("=" * 60)


# ============================================================
# SELF TEST
# ============================================================

def self_test() -> bool:
    """Run deterministic internal tests."""

    passed = 0
    failed = 0

    print("GEDT SELF TEST")
    print("=" * 60)

    # Test 1
    try:
        assert clamp(2.0, 0.0, 1.0) == 1.0
        assert clamp(-1.0, 0.0, 1.0) == 0.0
        passed += 1
        print("PASS: utility functions")
    except Exception as exc:
        failed += 1
        print("FAIL: utility functions:", exc)

    # Test 2
    try:
        values = [1.0, 1.0, 1.0, 1.0]
        assert abs(gini(values)) < 1e-10
        passed += 1
        print("PASS: inequality calculation")
    except Exception as exc:
        failed += 1
        print("FAIL: inequality calculation:", exc)

    # Test 3
    try:
        model = GEDT(
            agents=20,
            periods=10,
            seed=42,
            scenario="baseline",
        )

        history = model.run()

        assert len(history) == 11
        assert history[-1].gdp > 0
        passed += 1
        print("PASS: economic simulation")
    except Exception as exc:
        failed += 1
        print("FAIL: economic simulation:", exc)

    # Test 4
    try:
        model = GEDT(
            agents=20,
            periods=5,
            seed=42,
            scenario="education",
        )

        model.run()

        result = model.summary()

        assert result.final_gdp > 0
        assert 0.0 <= result.final_inequality <= 1.0
        passed += 1
        print("PASS: scenario engine")
    except Exception as exc:
        failed += 1
        print("FAIL: scenario engine:", exc)

    # Test 5
    try:
        result = monte_carlo(
            scenario="baseline",
            runs=5,
            agents=10,
            periods=5,
            seed=42,
        )

        assert result["runs"] == 5
        assert float(result["gdp_mean"]) > 0
        passed += 1
        print("PASS: Monte Carlo engine")
    except Exception as exc:
        failed += 1
        print("FAIL: Monte Carlo engine:", exc)

    # Test 6
    try:
        scenarios = [
            "baseline",
            "education",
            "innovation",
            "sustainable",
            "crisis",
        ]

        results = compare_scenarios(
            scenarios=scenarios,
            agents=10,
            periods=3,
            runs=2,
            seed=42,
        )

        assert len(results) == 5

        for result in results:
            assert float(result["gdp_mean"]) > 0

        passed += 1
        print("PASS: scenario comparison")
    except Exception as exc:
        failed += 1
        print("FAIL: scenario comparison:", exc)

    print("=" * 60)
    print("PASSED:", passed)
    print("FAILED:", failed)

    if failed == 0:
        print("GEDT SELF TEST: PASS")
        return True

    print("GEDT SELF TEST: FAIL")
    return False


# ============================================================
# COMMAND LINE INTERFACE
# ============================================================

def main() -> int:
    """GEDT command-line interface."""

    parser = argparse.ArgumentParser(
        description=(
            "Global Economic Digital Twin "
            "standalone simulation"
        )
    )

    parser.add_argument(
        "--agents",
        type=int,
        default=100,
        help="Number of economic agents.",
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=50,
        help="Number of simulation periods.",
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Monte Carlo runs.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default="baseline",
        choices=[
            "baseline",
            "education",
            "innovation",
            "sustainable",
            "crisis",
        ],
        help="Economic scenario.",
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
        "--csv",
        default="gedt_results.csv",
        help="CSV output filename.",
    )

    parser.add_argument(
        "--json",
        default="gedt_results.json",
        help="JSON output filename.",
    )

    args = parser.parse_args()

    if args.self_test:
        return 0 if self_test() else 1

    print()
    print("GEDT - GLOBAL ECONOMIC DIGITAL TWIN")
    print("Version:", VERSION)
    print(
        "Timestamp:",
        datetime.now(timezone.utc).isoformat(),
    )

    # --------------------------------------------------------
    # Scenario comparison
    # --------------------------------------------------------

    if args.compare:

        scenarios = [
            "baseline",
            "education",
            "innovation",
            "sustainable",
            "crisis",
        ]

        results = compare_scenarios(
            scenarios=scenarios,
            agents=args.agents,
            periods=args.periods,
            runs=args.runs,
            seed=args.seed,
        )

        print()
        print("=" * 80)
        print("GEDT SCENARIO COMPARISON")
        print("=" * 80)

        for result in results:

            print(
                f"{str(result['scenario']):<15}"
                f" GDP={float(result['gdp_mean']):>14,.2f}"
                f" Growth={float(result['growth_mean']):>9.2f}%"
                f" Unemployment="
                f"{float(result['unemployment_mean']) * 100:>7.2f}%"
                f" Inequality="
                f"{float(result['inequality_mean']):.4f}"
            )

        print("=" * 80)

        save_json(
            {
                "project": "GEDT",
                "version": VERSION,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
                "comparison": results,
            },
            args.json,
        )

        print("Saved:", args.json)

        return 0

    # --------------------------------------------------------
    # Single scenario
    # --------------------------------------------------------

    model = GEDT(
        agents=args.agents,
        periods=args.periods,
        seed=args.seed,
        scenario=args.scenario,
    )

    history = model.run()

    result = model.summary()

    print_summary(result)

    mc = monte_carlo(
        scenario=args.scenario,
        runs=args.runs,
        agents=args.agents,
        periods=args.periods,
        seed=args.seed,
    )

    print_monte_carlo(mc)

    save_history_csv(
        history,
        args.csv,
    )

    save_json(
        {
            "project": "GEDT",
            "version": VERSION,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "scenario_result": asdict(result),
            "monte_carlo": mc,
        },
        args.json,
    )

    print()
    print("Saved:", args.csv)
    print("Saved:", args.json)
    print()
    print("GEDT RUN: COMPLETE")

    return 0


if __name__ == "__main__":
    sys.exit(main())