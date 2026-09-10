# ---------------------------------------------------------------------------
# GEDT end-to-end integration
# ---------------------------------------------------------------------------

def test_gedt_end_to_end_execution():
    """Verify the complete GEDT execution pipeline."""

    from gedt.__main__ import run_gedt

    results = run_gedt(
        periods=12,
        trials=100,
        seed=42,
    )

    assert isinstance(results, dict)

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

    scenarios = results["scenario_results"]

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

    for scenario in results["scenario_results"]:
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