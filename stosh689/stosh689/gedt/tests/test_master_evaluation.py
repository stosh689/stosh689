"""Tests for the GEDT v11.0 master evaluation."""
import json
import pytest
from gedt.master_evaluation import (
    EVALUATION_NAME,
    EVALUATION_VERSION,
    run_master_evaluation,
    save_master_evaluation,
    validate_master_evaluation,
)
def test_master_evaluation_metadata():
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    assert report["evaluation"]["name"] == EVALUATION_NAME
    assert report["evaluation"]["version"] == EVALUATION_VERSION
    assert report["gedt"]["version"] == "11.0.0"
def test_master_evaluation_has_required_sections():
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    required = {
        "evaluation",
        "gedt",
        "experiment",
        "baseline",
        "scenarios",
        "uncertainty",
    }
    assert required.issubset(report.keys())
def test_master_evaluation_parameters():
    report = run_master_evaluation(
        periods=6,
        trials=25,
        seed=123,
    )
    assert report["experiment"]["periods"] == 6
    assert report["experiment"]["trials"] == 25
    assert report["experiment"]["seed"] == 123
def test_baseline_is_present():
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    baseline = report["baseline"]
    assert "deterministic" in baseline
    assert baseline["deterministic"]["initial_gdp"] > 0
    assert baseline["deterministic"]["final_gdp"] > 0
def test_scenario_benchmark_is_present():
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    scenarios = report["scenarios"]
    assert "scenarios" in scenarios
    assert len(scenarios["scenarios"]) >= 1
def test_uncertainty_benchmark_is_present():
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    uncertainty = report["uncertainty"]
    assert "monte_carlo" in uncertainty
def test_monte_carlo_trial_count():
    trials = 25
    report = run_master_evaluation(
        periods=4,
        trials=trials,
        seed=42,
    )
    monte_carlo = report["uncertainty"]["monte_carlo"]
    assert monte_carlo["trials"] == trials
def test_master_evaluation_is_deterministic():
    first = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    second = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    assert first == second
def test_different_seed_changes_stochastic_results():
    first = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    second = run_master_evaluation(
        periods=4,
        trials=20,
        seed=99,
    )
    first_mc = first["uncertainty"]["monte_carlo"]
    second_mc = second["uncertainty"]["monte_carlo"]
    assert first_mc != second_mc
def test_master_evaluation_validation():
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    validate_master_evaluation(report)
def test_missing_section_fails_validation():
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    del report["baseline"]
    with pytest.raises(ValueError):
        validate_master_evaluation(report)
def test_missing_monte_carlo_fails_validation():
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    del report["uncertainty"]["monte_carlo"]
    with pytest.raises(ValueError):
        validate_master_evaluation(report)
def test_invalid_periods():
    with pytest.raises(ValueError):
        run_master_evaluation(
            periods=0,
            trials=20,
            seed=42,
        )
def test_invalid_trials():
    with pytest.raises(ValueError):
        run_master_evaluation(
            periods=4,
            trials=0,
            seed=42,
        )
def test_json_serializable():
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    encoded = json.dumps(
        report,
        indent=2,
        sort_keys=True,
    )
    decoded = json.loads(encoded)
    assert decoded == report
def test_save_master_evaluation(tmp_path):
    report = run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )
    output = tmp_path / "master_evaluation.json"
    save_master_evaluation(
        report,
        output,
    )
    assert output.exists()
    loaded = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )
    assert loaded == report
def test_saved_file_is_valid_json(tmp_path):
    report = run_master_evaluation(
        periods=3,
        trials=10,
        seed=42,
    )
    output = tmp_path / "evaluation.json"
    save_master_evaluation(
        report,
        output,
    )
    text = output.read_text(
        encoding="utf-8"
    )
    parsed = json.loads(text)
    assert isinstance(parsed, dict)
    assert "evaluation" in parsed
def test_end_to_end_master_pipeline():
    report = run_master_evaluation(
        periods=3,
        trials=10,
        seed=42,
    )
    validate_master_evaluation(report)
    assert report["baseline"]["deterministic"]["final_gdp"] > 0
    assert len(
        report["scenarios"]["scenarios"]
    ) >= 1
    monte_carlo = report["uncertainty"]["monte_carlo"]
    assert monte_carlo["trials"] == 10
    assert monte_carlo["mean_final_gdp"] > 0
    assert monte_carlo["min_final_gdp"] > 0
    assert monte_carlo["max_final_gdp"] > 0