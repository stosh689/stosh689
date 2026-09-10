"""Deterministic baseline economic simulation engine for GEDT v11."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Iterable


@dataclass(frozen=True)
class EconomicState:
    """State variables for one period of the baseline model."""

    period: int
    gdp: float
    inflation: float
    unemployment: float


@dataclass(frozen=True)
class Scenario:
    """Scenario shocks applied to baseline economic dynamics."""

    name: str = "baseline"
    demand_shock: float = 0.0
    supply_shock: float = 0.0
    policy_rate_change: float = 0.0


@dataclass(frozen=True)
class SimulationResult:
    """Immutable simulation output."""

    scenario: Scenario
    states: tuple[EconomicState, ...]

    @property
    def final_gdp(self) -> float:
        return self.states[-1].gdp

    @property
    def average_inflation(self) -> float:
        return sum(
            state.inflation for state in self.states
        ) / len(self.states)

    @property
    def average_unemployment(self) -> float:
        return sum(
            state.unemployment for state in self.states
        ) / len(self.states)


def validate_state(state: EconomicState) -> None:
    """Validate model inputs."""

    if state.period < 0:
        raise ValueError("period must be non-negative")

    if state.gdp <= 0:
        raise ValueError("gdp must be positive")

    if not 0 <= state.inflation < 1:
        raise ValueError(
            "inflation must be in [0, 1)"
        )

    if not 0 <= state.unemployment <= 1:
        raise ValueError(
            "unemployment must be in [0, 1]"
        )


def simulate(
    initial: EconomicState,
    periods: int = 12,
    scenario: Scenario | None = None,
) -> SimulationResult:
    """Run a deterministic baseline/scenario simulation.

    This is a transparent research baseline, not a calibrated
    forecast of any real-world economy.
    """

    validate_state(initial)

    if periods < 1:
        raise ValueError(
            "periods must be at least 1"
        )

    scenario = scenario or Scenario()

    if not scenario.name.strip():
        raise ValueError(
            "scenario name must not be empty"
        )

    states: list[EconomicState] = [initial]
    current = initial

    for step in range(1, periods + 1):

        growth = (
            0.02
            + 0.04 * scenario.demand_shock
            - 0.03 * scenario.supply_shock
            - 0.01 * scenario.policy_rate_change
        )

        inflation_delta = (
            0.0015 * scenario.demand_shock
            + 0.002 * scenario.supply_shock
            - 0.001 * scenario.policy_rate_change
        )

        unemployment_delta = (
            -0.004 * scenario.demand_shock
            + 0.003 * scenario.supply_shock
            + 0.002 * scenario.policy_rate_change
        )

        next_gdp = current.gdp * exp(growth)

        next_inflation = max(
            0.0,
            min(
                0.99,
                current.inflation + inflation_delta,
            ),
        )

        next_unemployment = max(
            0.0,
            min(
                1.0,
                current.unemployment
                + unemployment_delta,
            ),
        )

        current = EconomicState(
            period=initial.period + step,
            gdp=next_gdp,
            inflation=next_inflation,
            unemployment=next_unemployment,
        )

        states.append(current)

    return SimulationResult(
        scenario=scenario,
        states=tuple(states),
    )


def compare_scenarios(
    initial: EconomicState,
    scenarios: Iterable[Scenario],
    periods: int = 12,
) -> dict[str, SimulationResult]:
    """Run multiple named scenarios."""

    results: dict[str, SimulationResult] = {}

    for scenario in scenarios:

        if scenario.name in results:
            raise ValueError(
                f"duplicate scenario name: {scenario.name}"
            )

        results[scenario.name] = simulate(
            initial,
            periods,
            scenario,
        )

    return results