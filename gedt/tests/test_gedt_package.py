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


# ============================================================================
# TEST HELPERS
# ============================================================================

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


# ============================================================================
# PROJECT STRUCTURE
# ============================================================================

def test_gedt_project_structure():
    project_root = Path(__file__).resolve().parents[1]

    assert (project_root / "README.md").exists()
    assert (project_root / "src" / "gedt" / "__init__.py").exists()
    assert (
        project_root
        / "src"
        / "gedt"
        / "algorithm_engine.py"
    ).exists()


# ============================================================================
# ECONOMIC STATE
# ============================================================================

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


# ============================================================================
# SCENARIO
# ============================================================================

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


# ============================================================================
# SIMULATION
# ============================================================================

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


def test_simulation_rejects_negative_periods():
    with pytest.raises(ValueError):
        simulate(
            initial=make_state(),
            periods=-1,
            scenario=make_scenario(),
        )


def test_simulation_preserves_initial_state():
    state = make_state()

    result = simulate(
        initial=state,
        periods=5,
        scenario=make_scenario(),
    )

    assert result.states[0] == state


def test_simulation_periods_are_sequential():
    result = simulate(
        initial=make_state(),
        periods=10,
        scenario=make_scenario(),
    )

    periods = [
        state.period
        for state in result.states
    ]

    assert periods == list(range(11))


def test_simulation_gdp_is_finite():
    result = simulate(
        initial=make_state(),
        periods=20,
        scenario=make_scenario(),
    )

    for state in result.states:
        assert math.isfinite(state.gdp)


# ============================================================================
# SIMULATION RESULT
# ============================================================================

def test_simulation_result_initial_gdp():
    result = simulate(
        initial=make_state(),
        periods=5,
        scenario=make_scenario(),
    )

    assert result.initial_gdp == 1000.0


def test_simulation_result_final_gdp_is_finite():
    result = simulate(
        initial=make_state(),
        periods=5,
        scenario=make_scenario(),
    )

    assert math.isfinite(result.final_gdp)


def test_simulation_result_growth_is_finite():
    result = simulate(
        initial=make_state(),
        periods=5,
        scenario=make_scenario(),
    )

    assert math.isfinite(result.gdp_growth)


def test_simulation_result_average_inflation_is_finite():
    result = simulate(
        initial=make_state(),
        periods=5,
        scenario=make_scenario(),
    )

    assert math.isfinite(
        result.average_inflation
    )


def test_simulation_result_average_unemployment_is_finite():
    result = simulate(
        initial=make_state(),
        periods=5,
        scenario=make_scenario(),
    )

    assert math.isfinite(
        result.average_unemployment
    )


# ============================================================================
# MEAN BASELINE
# ============================================================================

def test_mean_baseline_fit():
    algorithm = MeanBaseline()

    result = algorithm.fit(
        make_growth_data()
    )

    assert result is algorithm


def test_mean_baseline_predict():
    algorithm = MeanBaseline()

    algorithm.fit(
        make_growth_data()
    )

    predictions = algorithm.predict(3)

    assert len(predictions) == 3

    for prediction in predictions:
        assert prediction == pytest.approx(104.0)


def test_mean_baseline_rejects_empty_data():
    algorithm = MeanBaseline()

    with pytest.raises(ValueError):
        algorithm.fit([])


def test_mean_baseline_requires_fit():
    algorithm = MeanBaseline()

    with pytest.raises(RuntimeError):
        algorithm.predict(1)


# ============================================================================
# LAST VALUE BASELINE
# ============================================================================

def test_last_value_baseline_fit():
    algorithm = LastValueBaseline()

    result = algorithm.fit(
        make_growth_data()
    )

    assert result is algorithm


def test_last_value_baseline_predict():
    algorithm = LastValueBaseline()

    algorithm.fit(
        make_growth_data()
    )

    predictions = algorithm.predict(4)

    assert predictions == [
        pytest.approx(108.0),
        pytest.approx(108.0),
        pytest.approx(108.0),
        pytest.approx(108.0),
    ]


def test_last_value_baseline_rejects_empty_data():
    algorithm = LastValueBaseline()

    with pytest.raises(ValueError):
        algorithm.fit([])


# ============================================================================
# LINEAR TREND
# ============================================================================

def test_linear_trend_fit():
    algorithm = LinearTrend()

    result = algorithm.fit(
        make_growth_data()
    )

    assert result is algorithm


def test_linear_trend_predict():
    algorithm = LinearTrend()

    algorithm.fit(
        make_growth_data()
    )

    predictions = algorithm.predict(3)

    assert len(predictions) == 3

    assert predictions[0] == pytest.approx(110.0)
    assert predictions[1] == pytest.approx(112.0)
    assert predictions[2] == pytest.approx(114.0)


def test_linear_trend_slope():
    algorithm = LinearTrend()

    algorithm.fit(
        make_growth_data()
    )

    assert algorithm.slope == pytest.approx(2.0)


def test_linear_trend_intercept():
    algorithm = LinearTrend()

    algorithm.fit(
        make_growth_data()
    )

    assert algorithm.intercept == pytest.approx(100.0)


def test_linear_trend_sample_size():
    algorithm = LinearTrend()

    algorithm.fit(
        make_growth_data()
    )

    assert algorithm.sample_size == 5


def test_linear_trend_negative_slope():
    algorithm = LinearTrend()

    algorithm.fit(
        [
            110.0,
            108.0,
            106.0,
            104.0,
            102.0,
        ]
    )

    assert algorithm.slope == pytest.approx(-2.0)


def test_linear_trend_rejects_too_few_observations():
    algorithm = LinearTrend()

    with pytest.raises(ValueError):
        algorithm.fit([100.0])


def test_linear_trend_requires_fit():
    algorithm = LinearTrend()

    with pytest.raises(RuntimeError):
        algorithm.predict(1)


def test_linear_trend_rejects_invalid_horizon():
    algorithm = LinearTrend()

    algorithm.fit(
        make_growth_data()
    )

    with pytest.raises(ValueError):
        algorithm.predict(0)


# ============================================================================
# ALGORITHM EVALUATION
# ============================================================================

def test_evaluation_dataclass_exists():
    evaluation = Evaluation(
        algorithm="test",
        rmse=0.0,
        mae=0.0,
        observations=1,
    )

    assert evaluation.algorithm == "test"
    assert evaluation.rmse == 0.0
    assert evaluation.mae == 0.0
    assert evaluation.observations == 1


def test_perfect_prediction_has_zero_error():
    actual = [
        1.0,
        2.0,
        3.0,
        4.0,
    ]

    predicted = [
        1.0,
        2.0,
        3.0,
        4.0,
    ]

    evaluation = evaluate_predictions(
        actual,
        predicted,
    )

    assert evaluation.rmse == pytest.approx(0.0)
    assert evaluation.mae == pytest.approx(0.0)


def test_prediction_error_is_positive():
    actual = [
        1.0,
        2.0,
        3.0,
        4.0,
    ]

    predicted = [
        2.0,
        3.0,
        4.0,
        5.0,
    ]

    evaluation = evaluate_predictions(
        actual,
        predicted,
    )

    assert evaluation.rmse > 0.0
    assert evaluation.mae > 0.0


def test_prediction_length_mismatch_rejected():
    with pytest.raises(ValueError):
        evaluate_predictions(
            [1.0, 2.0],
            [1.0],
        )


def test_evaluate_mean_algorithm():
    algorithm = MeanBaseline()

    evaluation = evaluate_algorithm(
        algorithm,
        make_growth_data(),
    )

    assert isinstance(
        evaluation,
        Evaluation,
    )

    assert evaluation.rmse >= 0.0
    assert evaluation.mae >= 0.0


def test_evaluate_last_value_algorithm():
    algorithm = LastValueBaseline()

    evaluation = evaluate_algorithm(
        algorithm,
        make_growth_data(),
    )

    assert isinstance(
        evaluation,
        Evaluation,
    )


def test_evaluate_linear_trend_algorithm():
    algorithm = LinearTrend()

    evaluation = evaluate_algorithm(
        algorithm,
        make_growth_data(),
    )

    assert isinstance(
        evaluation,
        Evaluation,
    )

    assert math.isfinite(
        evaluation.rmse
    )


# ============================================================================
# ALGORITHM RANKING
# ============================================================================

def test_rank_algorithms_returns_results():
    algorithms = [
        MeanBaseline(),
        LastValueBaseline(),
        LinearTrend(),
    ]

    rankings = rank_algorithms(
        algorithms,
        make_growth_data(),
    )

    assert len(rankings) == 3


def test_rank_algorithms_sorted_by_rmse():
    algorithms = [
        MeanBaseline(),
        LastValueBaseline(),
        LinearTrend(),
    ]

    rankings = rank_algorithms(
        algorithms,
        make_growth_data(),
    )

    rmses = [
        result.rmse
        for result in rankings
    ]

    assert rmses == sorted(rmses)


# ============================================================================
# MONTE CARLO
# ============================================================================

def test_monte_carlo_returns_summary():
    result = monte_carlo(
        initial=make_state(),
        scenario=make_scenario(),
        periods=5,
        trials=100,
        seed=42,
    )

    assert isinstance(
        result,
        MonteCarloSummary,
    )


def test_monte_carlo_reproducible():
    first = monte_carlo(
        initial=make_state(),
        scenario=make_scenario(),
        periods=5,
        trials=100,
        seed=42,
    )

    second = monte_carlo(
        initial=make_state(),
        scenario=make_scenario(),
        periods=5,
        trials=100,
        seed=42,
    )

    assert first == second


def test_monte_carlo_different_seed_changes_result():
    first = monte_carlo(
        initial=make_state(),
        scenario=make_scenario(),
        periods=5,
        trials=100,
        seed=42,
    )

    second = monte_carlo(
        initial=make_state(),
        scenario=make_scenario(),
        periods=5,
        trials=100,
        seed=99,
    )

    assert first != second


def test_monte_carlo_rejects_invalid_trials():
    with pytest.raises(ValueError):
        monte_carlo(
            initial=make_state(),
            scenario=make_scenario(),
            periods=5,
            trials=0,
            seed=42,
        )


# ============================================================================
# SENSITIVITY ANALYSIS
# ============================================================================

def test_sensitivity_analysis_returns_results():
    result = sensitivity_analysis(
        initial=make_state(),
        scenario=make_scenario(),
        parameter="demand_shock",
        values=[
            -0.10,
            0.0,
            0.10,
        ],
        periods=5,
    )

    assert isinstance(
        result,
        list,
    )

    assert len(result) == 3

    for item in result:
        assert isinstance(
            item,
            SensitivityResult,
        )


def test_sensitivity_analysis_contains_requested_values():
    values = [
        -0.10,
        0.0,
        0.10,
    ]

    result = sensitivity_analysis(
        initial=make_state(),
        scenario=make_scenario(),
        parameter="demand_shock",
        values=values,
        periods=5,
    )

    returned_values = [
        item.parameter_value
        for item in result
    ]

    assert returned_values == values


def test_sensitivity_analysis_rejects_unknown_parameter():
    with pytest.raises(ValueError):
        sensitivity_analysis(
            initial=make_state(),
            scenario=make_scenario(),
            parameter="unknown_parameter",
            values=[0.0, 1.0],
            periods=5,
        )


# ============================================================================
# OPTIMIZATION
# ============================================================================

def test_optimize_parameter_returns_result():
    result = optimize_parameter(
        initial=make_state(),
        scenario=make_scenario(),
        parameter="demand_shock",
        values=[
            -0.10,
            0.0,
            0.10,
        ],
        periods=5,
    )

    assert result is not None


def test_optimize_parameter_rejects_empty_values():
    with pytest.raises(ValueError):
        optimize_parameter(
            initial=make_state(),
            scenario=make_scenario(),
            parameter="demand_shock",
            values=[],
            periods=5,
        )


# ============================================================================
# SCENARIO COMPARISON
# ============================================================================

def test_compare_scenarios():
    baseline = Scenario(
        name="baseline",
        demand_shock=0.0,
        supply_shock=0.0,
        policy_rate_change=0.0,
    )

    stress = Scenario(
        name="stress",
        demand_shock=-0.10,
        supply_shock=0.05,
        policy_rate_change=0.02,
    )

    results = compare_scenarios(
        initial=make_state(),
        scenarios=[
            baseline,
            stress,
        ],
        periods=5,
    )

    assert len(results) == 2


def test_compare_scenarios_preserves_names():
    scenarios = [
        Scenario(
            name="baseline",
            demand_shock=0.0,
            supply_shock=0.0,
            policy_rate_change=0.0,
        ),
        Scenario(
            name="stress",
            demand_shock=-0.10,
            supply_shock=0.05,
            policy_rate_change=0.02,
        ),
    ]

    results = compare_scenarios(
        initial=make_state(),
        scenarios=scenarios,
        periods=5,
    )

    names = [
        result.scenario.name
        for result in results
    ]

    assert names == [
        "baseline",
        "stress",
    ]


# ============================================================================
# BASELINE EXPERIMENT
# ============================================================================

def test_run_baseline_experiment():
    result = run_baseline_experiment()

    assert result is not None


def test_baseline_experiment_is_reproducible():
    first = run_baseline_experiment()
    second = run_baseline_experiment()

    assert first == second


# ============================================================================
# ENGINE REPORT
# ============================================================================

def test_engine_report_returns_text():
    report = engine_report()

    assert isinstance(
        report,
        str,
    )

    assert len(report) > 0


def test_engine_report_mentions_gedt():
    report = engine_report()

    assert "GEDT" in report


# ============================================================================
# STRESS SCENARIOS
# ============================================================================

def test_negative_demand_shock_produces_finite_result():
    scenario = Scenario(
        name="demand_stress",
        demand_shock=-0.20,
        supply_shock=0.0,
        policy_rate_change=0.0,
    )

    result = simulate(
        initial=make_state(),
        periods=12,
        scenario=scenario,
    )

    assert math.isfinite(
        result.final_gdp
    )


def test_supply_shock_produces_finite_result():
    scenario = Scenario(
        name="supply_stress",
        demand_shock=0.0,
        supply_shock=0.20,
        policy_rate_change=0.0,
    )

    result = simulate(
        initial=make_state(),
        periods=12,
        scenario=scenario,
    )

    assert math.isfinite(
        result.final_gdp
    )


def test_policy_rate_change_produces_finite_result():
    scenario = Scenario(
        name="policy_stress",
        demand_shock=0.0,
        supply_shock=0.0,
        policy_rate_change=0.05,
    )

    result = simulate(
        initial=make_state(),
        periods=12,
        scenario=scenario,
    )

    assert math.isfinite(
        result.final_gdp
    )


# ============================================================================
# NUMERICAL SAFETY
# ============================================================================

def test_simulation_outputs_are_finite():
    result = simulate(
        initial=make_state(),
        periods=25,
        scenario=make_scenario(),
    )

    for state in result.states:
        assert math.isfinite(
            state.gdp
        )

        assert math.isfinite(
            state.inflation
        )

        assert math.isfinite(
            state.unemployment
        )


def test_monte_carlo_outputs_are_finite():
    result = monte_carlo(
        initial=make_state(),
        scenario=make_scenario(),
        periods=10,
        trials=250,
        seed=42,
    )

    for value in vars(result).values():
        if isinstance(value, (int, float)):
            assert math.isfinite(
                float(value)
            )


# ============================================================================
# GEDT END-TO-END INTEGRATION
# ============================================================================

def test_gedt_end_to_end_execution():
    """Verify the complete GEDT execution pipeline."""

    from gedt.__main__ import run_gedt

    results = run_gedt(
        periods=12,
        trials=100,
        seed=42,
    )

    assert isinstance(
        results,
        dict,
    )

    assert results["gedt_version"] == "11.0.0"
    assert results["periods"] == 12
    assert results["trials"] == 100
    assert results["seed"] == 42

    assert "initial_state" in results
    assert "baseline" in results
    assert "scenario_results" in results
    assert "monte_carlo" in results
    assert "engine_report" in results


def test_gedt_end_to_end_has_scenarios():
    """Verify that the integrated pipeline produces scenarios."""

    from gedt.__main__ import run_gedt

    results = run_gedt(
        periods=12,
        trials=100,
        seed=42,
    )

    scenarios = results[
        "scenario_results"
    ]

    assert len(scenarios) == 4

    names = [
        scenario["scenario"]
        for scenario in scenarios
    ]

    assert "baseline" in names
    assert "demand_stress" in names
    assert "supply_stress" in names
    assert "tight_policy" in names


def test_gedt_end_to_end_is_reproducible():
    """Verify deterministic execution with a fixed seed."""

    from gedt.__main__ import run_gedt

    first = run_gedt(
        periods=12,
        trials=100,
        seed=42,
    )

    second = run_gedt(
        periods=12,
        trials=100,
        seed=42,
    )

    assert first == second


def test_gedt_end_to_end_changes_with_seed():
    """Verify stochastic analysis responds to seed changes."""

    from gedt.__main__ import run_gedt

    first = run_gedt(
        periods=12,
        trials=100,
        seed=42,
    )

    second = run_gedt(
        periods=12,
        trials=100,
        seed=99,
    )

    assert first != second


def test_gedt_rejects_invalid_periods():
    """Verify invalid simulation periods are rejected."""

    from gedt.__main__ import run_gedt

    with pytest.raises(ValueError):
        run_gedt(
            periods=0,
            trials=100,
            seed=42,
        )


def test_gedt_rejects_invalid_trials():
    """Verify invalid Monte Carlo trial counts are rejected."""

    from gedt.__main__ import run_gedt

    with pytest.raises(ValueError):
        run_gedt(
            periods=12,
            trials=0,
            seed=42,
        )


def test_gedt_outputs_finite_scenario_results():
    """Verify integrated economic results are numerically safe."""

    from gedt.__main__ import run_gedt

    results = run_gedt(
        periods=12,
        trials=100,
        seed=42,
    )

    for scenario in results[
        "scenario_results"
    ]:
        assert math.isfinite(
            scenario["initial_gdp"]
        )

        assert math.isfinite(
            scenario["final_gdp"]
        )

        assert math.isfinite(
            scenario["gdp_growth"]
        )

        assert math.isfinite(
            scenario["average_inflation"]
        )

        assert math.isfinite(
            scenario["average_unemployment"]
        )


# ============================================================================
# RELEASE READINESS
# ============================================================================

def test_gedt_version_is_present():
    from gedt.__main__ import VERSION

    assert VERSION == "11.0.0"


def test_gedt_has_single_execution_function():
    from gedt.__main__ import run_gedt

    assert callable(run_gedt)


def test_gedt_cli_entry_point_exists():
    from gedt.__main__ import main

    assert callable(main)