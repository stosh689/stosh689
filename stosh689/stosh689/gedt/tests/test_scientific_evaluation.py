"""Tests for GEDT v11.0 scientific evaluation."""

import json

import pytest

from gedt.scientific_evaluation import (
    EVALUATION_NAME,
    EVALUATION_VERSION,
    build_scientific_evaluation,
    calculate_baseline_metrics,
    calculate_scenario_metrics,
    calculate_uncertainty_metrics,
    run_master_evaluation,
    save_scientific_evaluation,
    validate_scientific_evaluation,
)


def make_report():
    """Create a small deterministic report for testing."""
    return run_master_evaluation(
        periods=4,
        trials=20,
        seed=42,
    )


def test_evaluation_metadata():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    assert evaluation["evaluation"]["name"] == EVALUATION_NAME
    assert evaluation["evaluation"]["version"] == EVALUATION_VERSION
    assert evaluation["gedt"]["version"] == "11.0.0"


def test_required_sections_exist():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    required = {
        "evaluation",
        "gedt",
        "experiment",
        "baseline_metrics",
        "scenario_metrics",
        "uncertainty_metrics",
        "reproducibility_metrics",
        "quality_checks",
        "quality_score",
        "quality_percentage",
        "status",
    }

    assert required.issubset(evaluation.keys())


def test_baseline_metrics():
    report = make_report()

    metrics = calculate_baseline_metrics(report)

    assert metrics["initial_gdp"] > 0
    assert metrics["final_gdp"] > 0
    assert "absolute_gdp_change" in metrics
    assert "relative_gdp_change" in metrics
    assert "reported_gdp_growth" in metrics
    assert "average_inflation" in metrics
    assert "average_unemployment" in metrics
    assert metrics["numerically_valid"] is True


def test_scenario_metrics():
    report = make_report()

    metrics = calculate_scenario_metrics(report)

    assert metrics["scenario_count"] >= 1
    assert "comparisons" in metrics
    assert isinstance(metrics["comparisons"], list)


def test_scenario_baseline_exists():
    report = make_report()

    metrics = calculate_scenario_metrics(report)

    names = [
        item["scenario"]
        for item in metrics["comparisons"]
    ]

    assert "baseline" in names


def test_uncertainty_metrics():
    report = make_report()

    metrics = calculate_uncertainty_metrics(report)

    assert metrics["trials"] == 20
    assert metrics["mean_final_gdp"] > 0
    assert metrics["std_final_gdp"] >= 0
    assert metrics["min_final_gdp"] > 0
    assert metrics["max_final_gdp"] > 0
    assert metrics["range_final_gdp"] >= 0
    assert metrics["finite_results"] is True


def test_uncertainty_bounds():
    report = make_report()

    metrics = calculate_uncertainty_metrics(report)

    assert (
        metrics["min_final_gdp"]
        <= metrics["mean_final_gdp"]
        <= metrics["max_final_gdp"]
    )


def test_quality_score_is_valid():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    assert 0.0 <= evaluation["quality_score"] <= 1.0
    assert 0.0 <= evaluation["quality_percentage"] <= 100.0


def test_quality_percentage_matches_score():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    assert evaluation["quality_percentage"] == pytest.approx(
        evaluation["quality_score"] * 100.0
    )


def test_quality_checks_exist():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    checks = evaluation["quality_checks"]

    assert "baseline_valid" in checks
    assert "positive_final_gdp" in checks
    assert "scenario_coverage" in checks
    assert "uncertainty_available" in checks
    assert "finite_uncertainty_results" in checks
    assert "reproducible" in checks


def test_quality_checks_are_boolean():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    for value in evaluation["quality_checks"].values():
        assert isinstance(value, bool)


def test_reproducibility_is_reported():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    reproducibility = evaluation[
        "reproducibility_metrics"
    ]

    assert reproducibility["same_seed"] == 42
    assert "identical_runs" in reproducibility
    assert "reproducible" in reproducibility


def test_reproducibility_is_true():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    assert (
        evaluation["reproducibility_metrics"][
            "reproducible"
        ]
        is True
    )


def test_status_is_valid():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    assert evaluation["status"] in {
        "PASS",
        "REVIEW",
    }


def test_validation_accepts_valid_report():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    validate_scientific_evaluation(evaluation)


def test_missing_section_fails_validation():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    del evaluation["baseline_metrics"]

    with pytest.raises(ValueError):
        validate_scientific_evaluation(evaluation)


def test_invalid_quality_score_fails_validation():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    evaluation["quality_score"] = 2.0

    with pytest.raises(ValueError):
        validate_scientific_evaluation(evaluation)


def test_invalid_quality_percentage_fails_validation():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    evaluation["quality_percentage"] = 101.0

    with pytest.raises(ValueError):
        validate_scientific_evaluation(evaluation)


def test_invalid_status_fails_validation():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    evaluation["status"] = "UNKNOWN"

    with pytest.raises(ValueError):
        validate_scientific_evaluation(evaluation)


def test_json_serializable():
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    encoded = json.dumps(
        evaluation,
        indent=2,
        sort_keys=True,
    )

    decoded = json.loads(encoded)

    assert decoded == evaluation


def test_save_evaluation(tmp_path):
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    output = tmp_path / "scientific_evaluation.json"

    save_scientific_evaluation(
        evaluation,
        output,
    )

    assert output.exists()

    loaded = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert loaded == evaluation


def test_saved_evaluation_contains_status(tmp_path):
    report = make_report()

    evaluation = build_scientific_evaluation(report)

    output = tmp_path / "evaluation.json"

    save_scientific_evaluation(
        evaluation,
        output,
    )

    loaded = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert loaded["status"] in {
        "PASS",
        "REVIEW",
    }


def test_evaluation_is_repeatable():
    first_report = make_report()
    second_report = make_report()

    first = build_scientific_evaluation(
        first_report
    )

    second = build_scientific_evaluation(
        second_report
    )

    assert first == second


def test_scenario_dispersion_is_nonnegative():
    report = make_report()

    metrics = calculate_scenario_metrics(report)

    assert metrics["scenario_dispersion"] >= 0


def test_end_to_end_scientific_evaluation():
    report = run_master_evaluation(
        periods=3,
        trials=10,
        seed=42,
    )

    evaluation = build_scientific_evaluation(report)

    validate_scientific_evaluation(evaluation)

    assert evaluation["gedt"]["version"] == "11.0.0"
    assert evaluation["baseline_metrics"]["final_gdp"] > 0
    assert evaluation["scenario_metrics"]["scenario_count"] >= 1
    assert evaluation["uncertainty_metrics"]["trials"] == 10
    assert evaluation["reproducibility_metrics"]["reproducible"] is True