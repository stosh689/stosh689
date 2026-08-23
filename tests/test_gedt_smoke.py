from gedt.simulation.engine import SimulationEngine


def test_engine_runs():
    engine = SimulationEngine()

    result = engine.run(
        population_size=100,
        years=5,
        innovation_rate=0.05,
        seed=42,
    )

    assert result is not None
    assert "final_productivity" in result
    assert "history" in result
    assert len(result["history"]) == 5


def test_engine_is_reproducible():
    engine = SimulationEngine()

    first = engine.run(
        population_size=100,
        years=5,
        innovation_rate=0.05,
        seed=42,
    )

    second = engine.run(
        population_size=100,
        years=5,
        innovation_rate=0.05,
        seed=42,
    )

    assert first["final_productivity"] == second["final_productivity"]