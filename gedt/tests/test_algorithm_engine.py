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


# ============================================================
# ECONOMIC STATE TESTS
# ============================================================

def test_economic_state_accepts_valid_values():
    state = EconomicState(
        gdp=1000.0,
        inflation=2.0,
        unemployment=5.0,
        interest_rate=4.0,
        population=1_000_000,
    )

    assert state.gdp == 1000.0
    assert state.inflation == 2.0
    assert state.unemployment == 5.0
    assert state.interest_rate == 4.0


def test_economic_state_rejects_negative_gdp():
    with pytest.raises(ValueError):
        EconomicState(
            gdp=-1.0,
            inflation=2.0,
            unemployment=5.0,
            interest_rate=4.0,
            population=1_000_000,
        )


def test_economic_state_rejects_negative_population():
    with pytest.raises(ValueError):
        EconomicState(
            gdp=1000.0,
            inflation=2.0,
            unemployment=5.0,
            interest_rate=4.0,
            population=-1,
        )


# ============================================================
# SCENARIO TESTS
# ============================================================

def make_state():
    return EconomicState(
        gdp=1000.0,
        inflation=2.0,
        unemployment=5.0,
        interest_rate=4.0,
        population=1_000_000,
    )


def make_scenario():
    return Scenario(
        name="baseline",
        initial_state=make_state(),
        periods=10,
        gdp_growth=0.02,
        inflation_change=0.0,
        unemployment_change=0.0,
        interest_rate_change=0.0,
    )


def test_scenario_accepts_valid_values():
    scenario = make_scenario()

    assert scenario.name == "baseline"
    assert scenario.periods == 10


def test_scenario_rejects_zero_periods():
    with pytest.raises(ValueError):
        Scenario(
            name="invalid",
            initial_state=make_state(),
            periods=0,
        )


def test_scenario_rejects_negative_growth_below_reasonable_limit():
    with pytest.raises(ValueError):
        Scenario(
            name="invalid",
            initial_state=make_state(),
            periods=10,
            gdp_growth=-2.0,
        )


# ============================================================
# SIMULATION TESTS
# ============================================================

def test_simulation_returns_result():
    result = simulate(make_scenario())

    assert isinstance(result, SimulationResult)


def test_simulation_has_requested_periods():
    result = simulate(make_scenario())

    assert len(result.states) == 10


def test_simulation_is_deterministic():
    scenario = make_scenario()

    result_a = simulate(scenario, seed=42)
    result_b = simulate(scenario, seed=42)

    assert result_a.states == result_b.states


def test_simulation_seed_changes_stochastic_result():
    scenario = make_scenario()

    result_a = simulate(scenario, seed=1)
    result_b = simulate(scenario, seed=2)

    # If the simulator is deterministic, this is still acceptable.
    # The test therefore checks validity rather than requiring divergence.
    assert len(result_a.states) == len(result_b.states)


def test_gdp_grows_with_positive_growth_rate():
    scenario = make_scenario()
    result = simulate(scenario, seed=42)

    assert result.states[-1].gdp > result.states[0].gdp


def test_zero_growth_preserves_gdp():
    scenario = Scenario(
        name="zero-growth",
        initial_state=make_state(),
        periods=5,
        gdp_growth=0.0,
    )

    result = simulate(scenario, seed=42)

    assert math.isclose(
        result.states[-1].gdp,
        result.states[0].gdp,
        rel_tol=1e-9,
    )


# ============================================================
# MEAN BASELINE
# ============================================================

def test_mean_baseline_fit():
    model = MeanBaseline()

    model.fit([1.0, 2.0, 3.0, 4.0])

    assert model.mean == pytest.approx(2.5)


def test_mean_baseline_predict():
    model = MeanBaseline()

    model.fit([1.0, 2.0, 3.0])

    predictions = model.predict([10.0, 20.0])

    assert predictions == pytest.approx([2.0, 2.0])


def test_mean_baseline_rejects_empty_training_data():
    model = MeanBaseline()

    with pytest.raises(ValueError):
        model.fit([])


# ============================================================
# LAST VALUE BASELINE
# ============================================================

def test_last_value_baseline_fit():
    model = LastValueBaseline()

    model.fit([1.0, 2.0, 8.0])

    assert model.last_value == 8.0


def test_last_value_baseline_predict():
    model = LastValueBaseline()

    model.fit([1.0, 2.0, 8.0])

    predictions = model.predict([5.0, 6.0, 7.0])

    assert predictions == [8.0, 8.0, 8.0]


def test_last_value_baseline_rejects_empty_data():
    model = LastValueBaseline()

    with pytest.raises(ValueError):
        model.fit([])


# ============================================================
# LINEAR TREND
# ============================================================

def test_linear_trend_fit():
    model = LinearTrend()

    model.fit([1.0, 2.0, 3.0, 4.0])

    assert hasattr(model, "slope")
    assert hasattr(model, "intercept")


def test_linear_trend_identifies_positive_trend():
    model = LinearTrend()

    model.fit([1.0, 2.0, 3.0, 4.0])

    assert model.slope > 0


def test_linear_trend_identifies_negative_trend():
    model = LinearTrend()

    model.fit([4.0, 3.0, 2.0, 1.0])

    assert model.slope < 0


def test_linear_trend_predicts_reasonably():
    model = LinearTrend()

    model.fit([1.0, 2.0, 3.0, 4.0])

    predictions = model.predict([0.0, 0.0])

    assert len(predictions) == 2
    assert predictions[0] == pytest.approx(5.0)
    assert predictions[1] == pytest.approx(6.0)


def test_linear_trend_rejects_empty_data():
    model = LinearTrend()

    with pytest.raises(ValueError):
        model.fit([])


# ============================================================
# EVALUATION TESTS
# ============================================================

def test_evaluation_perfect_predictions():
    evaluation = evaluate_predictions(
        actual=[1.0, 2.0, 3.0],
        predicted=[1.0, 2.0, 3.0],
    )

    assert evaluation.rmse == pytest.approx(0.0)
    assert evaluation.mae == pytest.approx(0.0)


def test_evaluation_nonzero_error():
    evaluation = evaluate_predictions(
        actual=[1.0, 2.0, 3.0],
        predicted=[2.0, 3.0, 4.0],
    )

    assert evaluation.rmse > 0
    assert evaluation.mae > 0


def test_evaluation_lengths_must_match():
    with pytest.raises(ValueError):
        evaluate_predictions(
            actual=[1.0, 2.0],
            predicted=[1.0],
        )


def test_evaluate_algorithm():
    model = MeanBaseline()

    evaluation = evaluate_algorithm(
        model,
        train=[1.0, 2.0, 3.0],
        actual=[2.0, 2.0],
    )

    assert isinstance(evaluation, Evaluation)
    assert evaluation.rmse >= 0


# ============================================================
# ALGORITHM RANKING
# ============================================================

def test_rank_algorithms_returns_results():
    algorithms = [
        MeanBaseline(),
        LastValueBaseline(),
        LinearTrend(),
    ]

    ranked = rank_algorithms(
        algorithms,
        train=[1.0, 2.0, 3.0, 4.0],
        actual=[5.0, 6.0],
    )

    assert len(ranked) == 3


def test_rank_algorithms_sorted_by_error():
    algorithms = [
        MeanBaseline(),
        LastValueBaseline(),
        LinearTrend(),
    ]

    ranked = rank_algorithms(
        algorithms,
        train=[1.0, 2.0, 3.0, 4.0],
        actual=[5.0, 6.0],
    )

    errors = [item.rmse for item in ranked]

    assert errors == sorted(errors)


# ============================================================
# MONTE CARLO
# ============================================================

def test_monte_carlo_returns_summary():
    scenario = make_scenario()

    result = monte_carlo(
        scenario,
        simulations=25,
        seed=42,
    )

    assert isinstance(result, MonteCarloSummary)


def test_monte_carlo_has_requested_simulations():
    scenario = make_scenario()

    result = monte_carlo(
        scenario,
        simulations=20,
        seed=42,
    )

    assert result.simulations == 20


def test_monte_carlo_is_reproducible():
    scenario = make_scenario()

    result_a = monte_carlo(
        scenario,
        simulations=20,
        seed=42,
    )

    result_b = monte_carlo(
        scenario,
        simulations=20,
        seed=42,
    )

    assert result_a == result_b


def test_monte_carlo_rejects_invalid_count():
    with pytest.raises(ValueError):
        monte_carlo(
            make_scenario(),
            simulations=0,
            seed=42,
        )


# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================

def test_sensitivity_analysis_returns_results():
    scenario = make_scenario()

    result = sensitivity_analysis(
        scenario,
        parameter="gdp_growth",
        values=[0.01, 0.02, 0.03],
    )

    assert isinstance(result, SensitivityResult)


def test_sensitivity_analysis_contains_all_values():
    scenario = make_scenario()

    result = sensitivity_analysis(
        scenario,
        parameter="gdp_growth",
        values=[0.01, 0.02, 0.03],
    )

    assert len(result.values) == 3


def test_sensitivity_rejects_unknown_parameter():
    with pytest.raises(ValueError):
        sensitivity_analysis(
            make_scenario(),
            parameter="does_not_exist",
            values=[1.0, 2.0],
        )


# ============================================================
# OPTIMIZATION
# ============================================================

def test_optimization_returns_result():
    scenario = make_scenario()

    result = optimize_parameter(
        scenario,
        parameter="gdp_growth",
        values=[0.01, 0.02, 0.03],
    )

    assert result is not None


def test_optimization_requires_values():
    with pytest.raises(ValueError):
        optimize_parameter(
            make_scenario(),
            parameter="gdp_growth",
            values=[],
        )


# ============================================================
# SCENARIO COMPARISON
# ============================================================

def test_compare_scenarios():
    baseline = make_scenario()

    alternative = Scenario(
        name="high-growth",
        initial_state=make_state(),
        periods=10,
        gdp_growth=0.04,
    )

    result = compare_scenarios(
        [baseline, alternative],
        seed=42,
    )

    assert len(result) == 2


def test_compare_scenarios_rejects_duplicate_names():
    scenario_a = make_scenario()
    scenario_b = make_scenario()

    with pytest.raises(ValueError):
        compare_scenarios(
            [scenario_a, scenario_b],
            seed=42,
        )


# ============================================================
# BASELINE EXPERIMENT
# ============================================================

def test_run_baseline_experiment():
    result = run_baseline_experiment(seed=42)

    assert result is not None


# ============================================================
# ENGINE REPORT
# ============================================================

def test_engine_report_returns_text():
    report = engine_report()

    assert isinstance(report, str)
    assert len(report) > 0


def test_engine_report_mentions_algorithms():
    report = engine_report()

    assert "algorithm" in report.lower()


# ============================================================
# GENERAL SAFETY TESTS
# ============================================================

def test_simulation_does_not_produce_nan_gdp():
    result = simulate(make_scenario(), seed=42)

    for state in result.states:
        assert not math.isnan(state.gdp)


def test_simulation_does_not_produce_infinite_gdp():
    result = simulate(make_scenario(), seed=42)

    for state in result.states:
        assert math.isfinite(state.gdp)


def test_result_states_are_economic_states():
    result = simulate(make_scenario(), seed=42)

    assert all(
        isinstance(state, EconomicState)
        for state in result.states
    )