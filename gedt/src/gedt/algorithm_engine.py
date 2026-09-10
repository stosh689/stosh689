from pathlib import Path
import math

import pytest

from gedt.algorithm_engine import (
    EconomicState,
    Scenario,
    SimulationResult,
    MeanBaseline,
    LastValueBaseline,
    LinearTrend,
    Evaluation,
    MonteCarloSummary,
    SensitivityResult,
    simulate,
    evaluate_predictions,
    evaluate_algorithm,
    rank_algorithms,
    monte_carlo,
    sensitivity_analysis,
    optimize_parameter,
    compare_scenarios,
    run_baseline_experiment,
    engine_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_state() -> EconomicState:
    return EconomicState(
        period=0,
        gdp=1000.0,
        inflation=0.02,
        unemployment=0.05,
    )


def make_scenario() -> Scenario:
    return Scenario(
        name="baseline",
        demand_shock=0.0,
        supply_shock=0.0,
        policy_rate_change=0.0,
    )


def make_growth_data() -> list[float]:
    return [
        100.0,
        102.0,
        104.0,
        106.0,
        108.0,
    ]


# ---------------------------------------------------------------------------
# Project structure
# ---------------------------------------------------------------------------

def test_gedt_project_structure():
    project_root = Path(__file__).resolve().parents[1]

    assert (project_root / "README.md").exists()
    assert (project_root / "src" / "gedt" / "__init__.py").exists()
    assert (project_root / "src" / "gedt" / "algorithm_engine.py").exists()


# ---------------------------------------------------------------------------
# EconomicState
# ---------------------------------------------------------------------------

def test_economic_state_valid():
    state = make_state()

    assert state.period == 0
    assert state.gdp == 1000.0
    assert state.inflation == 0.02
    assert state.unemployment == 0.05


def test_economic_state_rejects_negative_gdp():
    with pytest.raises(ValueError):
        EconomicState(
            period=0,
            gdp=-1.0,
            inflation=0.02,
            unemployment=0.05,
        )


def test_economic_state_rejects_invalid_inflation():
    with pytest.raises(ValueError):
        EconomicState(
            period=0,
            gdp=1000.0,
            inflation=-2.0,
            unemployment=0.05,
        )


def test_economic_state_rejects_invalid_unemployment():
    with pytest.raises(ValueError):
        EconomicState(
            period=0,
            gdp=1000.0,
            inflation=0.02,
            unemployment=-1.0,
        )


# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------

def test_scenario_valid():
    scenario = make_scenario()

    assert scenario.name == "baseline"
    assert scenario.demand_shock == 0.0
    assert scenario.supply_shock == 0.0
    assert scenario.policy_rate_change == 0.0


def test_scenario_can_contain_shocks():
    scenario = Scenario(
        name="stress",
        demand_shock=-0.10,
        supply_shock=0.05,
        policy_rate_change=0.02,
    )

    assert scenario.demand_shock == -0.10
    assert scenario.supply_shock == 0.05
    assert scenario.policy_rate_change == 0.02


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def test_simulation_returns_simulation_result():
    result = simulate(
        initial=make_state(),
        periods=5,
        scenario=make_scenario(),
    )

    assert isinstance(result, SimulationResult)


def test_simulation_contains_initial_plus_periods():
    result = simulate(
        initial=make_state(),
        periods=5,
        scenario=make_scenario(),
    )

    assert len(result.states) == 6


def test_simulation_is_deterministic():
    first = simulate(
        initial=make_state(),
        periods=10,
        scenario=make_scenario(),
    )

    second = simulate(
        initial=make_state(),
        periods=10,
        scenario=make_scenario(),
    )

    assert first.states == second.states


def test_simulation_rejects_zero_periods():
    with pytest.raises(ValueError):
        simulate(
            initial=make_state(),
            periods=0,
            scenario=make_scenario(),
        )


def test_simulation_rejects_negative_period