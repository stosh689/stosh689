"""
Tests for the GEDT v11.0 RC1 release report generator.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


# Make the GEDT project root importable.
GEDT_ROOT = Path(__file__).resolve().parents[1]

if str(GEDT_ROOT) not in sys.path:
    sys.path.insert(0, str(GEDT_ROOT))


import release_report


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_release_constants():
    """Verify release metadata."""

    assert release_report.RELEASE_NAME == "GEDT v11.0"
    assert release_report.RELEASE_CANDIDATE == "RC1"
    assert release_report.REPORT_VERSION == "1.0.0"


# ---------------------------------------------------------------------------
# Evidence collection
# ---------------------------------------------------------------------------


def test_collect_release_evidence():
    """Release evidence should have the expected top-level structure."""

    evidence = release_report.collect_release_evidence()

    assert isinstance(evidence, dict)

    assert "release" in evidence
    assert "generated_at" in evidence
    assert "environment" in evidence
    assert "release_gate" in evidence


def test_release_metadata():
    """Release metadata should be correct."""

    evidence = release_report.collect_release_evidence()

    release = evidence["release"]

    assert release["name"] == "GEDT v11.0"
    assert release["candidate"] == "RC1"
    assert release["report_version"] == "1.0.0"


def test_environment_metadata():
    """Execution environment information should be recorded."""

    evidence = release_report.collect_release_evidence()

    environment = evidence["environment"]

    assert "python_version" in environment
    assert "python_implementation" in environment
    assert "platform" in environment
    assert "system" in environment
    assert "machine" in environment

    assert environment["python_version"]
    assert environment["python_implementation"]
    assert environment["platform"]


# ---------------------------------------------------------------------------
# Release gate
# ---------------------------------------------------------------------------


def test_release_gate_structure():
    """Release gate evidence should contain all expected fields."""

    evidence = release_report.collect_release_evidence()

    gate = evidence["release_gate"]

    assert "checks_passed" in gate
    assert "checks_total" in gate
    assert "score_percentage" in gate
    assert "ready" in gate
    assert "checks" in gate


def test_release_gate_contains_ten_checks():
    """GEDT v11 RC1 should currently contain ten release checks."""

    evidence = release_report.collect_release_evidence()

    gate = evidence["release_gate"]

    assert gate["checks_total"] == 10
    assert len(gate["checks"]) == 10


def test_release_gate_check_names():
    """Verify all required release-gate checks."""

    evidence = release_report.collect_release_evidence()

    names = [
        check["name"]
        for check in evidence["release_gate"]["checks"]
    ]

    expected = [
        "Package / Version",
        "Configuration",
        "Core Simulation",
        "Baseline Benchmark",
        "Scenario Benchmark",
        "Uncertainty Benchmark",
        "Master Evaluation",
        "Scientific Evaluation",
        "Performance Benchmark",
        "Automated Tests",
    ]

    assert names == expected


def test_release_gate_check_types():
    """Each release-gate result should have valid fields."""

    evidence = release_report.collect_release_evidence()

    for check in evidence["release_gate"]["checks"]:
        assert isinstance(check["name"], str)
        assert isinstance(check["passed"], bool)
        assert isinstance(check["message"], str)
        assert isinstance(
            check["elapsed_seconds"],
            (int, float),
        )

        assert check["name"]
        assert check["message"]
        assert check["elapsed_seconds"] >= 0


def test_release_gate_score_range():
    """Release-gate score must remain between zero and one hundred."""

    evidence = release_report.collect_release_evidence()

    score = evidence["release_gate"]["score_percentage"]

    assert 0.0 <= score <= 100.0


def test_release_gate_pass_count():
    """Passed-check count must match individual results."""

    evidence = release_report.collect_release_evidence()

    gate = evidence["release_gate"]

    calculated = sum(
        check["passed"]
        for check in gate["checks"]
    )

    assert gate["checks_passed"] == calculated


def test_release_gate_total_count():
    """Total-check count must match the check list."""

    evidence = release_report.collect_release_evidence()

    gate = evidence["release_gate"]

    assert gate["checks_total"] == len(
        gate["checks"]
    )


def test_release_gate_ready_flag():
    """Readiness must agree with the gate results."""

    evidence = release_report.collect_release_evidence()

    gate = evidence["release_gate"]

    expected = (
        gate["checks_total"] > 0
        and gate["checks_passed"]
        == gate["checks_total"]
    )

    assert gate["ready"] == expected


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_validate_release_evidence():
    """Valid evidence should pass validation."""

    evidence = release_report.collect_release_evidence()

    result = release_report.validate_release_evidence(
        evidence
    )

    assert result is None


@pytest.mark.parametrize(
    "missing_key",
    [
        "release",
        "generated_at",
        "environment",
        "release_gate",
    ],
)
def test_validate_missing_top_level_section(
    missing_key,
):
    """Missing top-level sections should be rejected."""

    evidence = release_report.collect_release_evidence()

    del evidence[missing_key]

    with pytest.raises(ValueError):
        release_report.validate_release_evidence(
            evidence
        )


def test_validate_wrong_release_name():
    """Unexpected release names should be rejected."""

    evidence = release_report.collect_release_evidence()

    evidence["release"]["name"] = "GEDT v10.0"

    with pytest.raises(ValueError):
        release_report.validate_release_evidence(
            evidence
        )


def test_validate_wrong_release_candidate():
    """Unexpected release candidates should be rejected."""

    evidence = release_report.collect_release_evidence()

    evidence["release"]["candidate"] = "BETA"

    with pytest.raises(ValueError):
        release_report.validate_release_evidence(
            evidence
        )


def test_validate_missing_gate_field():
    """Missing gate fields should be rejected."""

    evidence = release_report.collect_release_evidence()

    del evidence["release_gate"]["ready"]

    with pytest.raises(ValueError):
        release_report.validate_release_evidence(
            evidence
        )


def test_validate_invalid_score():
    """Scores outside zero to one hundred should fail."""

    evidence = release_report.collect_release_evidence()

    evidence["release_gate"]["score_percentage"] = 101.0

    with pytest.raises(ValueError):
        release_report.validate_release_evidence(
            evidence
        )


def test_validate_negative_score():
    """Negative scores should fail."""

    evidence = release_report.collect_release_evidence()

    evidence["release_gate"]["score_percentage"] = -1.0

    with pytest.raises(ValueError):
        release_report.validate_release_evidence(
            evidence
        )


def test_validate_zero_checks():
    """A release gate with zero checks should fail."""

    evidence = release_report.collect_release_evidence()

    evidence["release_gate"]["checks_total"] = 0

    with pytest.raises(ValueError):
        release_report.validate_release_evidence(
            evidence
        )


def test_validate_passed_exceeds_total():
    """Passed checks cannot exceed total checks."""

    evidence = release_report.collect_release_evidence()

    evidence["release_gate"]["checks_passed"] = 11
    evidence["release_gate"]["checks_total"] = 10

    with pytest.raises(ValueError):
        release_report.validate_release_evidence(
            evidence
        )


def test_validate_ready_type():
    """Readiness must be boolean."""

    evidence = release_report.collect_release_evidence()

    evidence["release_gate"]["ready"] = "yes"

    with pytest.raises(ValueError):
        release_report.validate_release_evidence(
            evidence
        )


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def test_markdown_report_returns_string():
    """Markdown generation should return text."""

    evidence = release_report.collect_release_evidence()

    report = release_report.markdown_report(
        evidence
    )

    assert isinstance(report, str)
    assert len(report) > 100


def test_markdown_report_contains_title():
    """Markdown should contain the release title."""

    evidence = release_report.collect_release_evidence()

    report = release_report.markdown_report(
        evidence
    )

    assert "# GEDT v11.0 RC1" in report


def test_markdown_report_contains_release_gate():
    """Markdown should describe the release gate."""

    evidence = release_report.collect_release_evidence()

    report = release_report.markdown_report(
        evidence
    )

    assert "## Release Gate" in report
    assert "Checks passed" in report
    assert "Checks total" in report
    assert "Gate score" in report


def test_markdown_report_contains_checks():
    """Markdown should list release checks."""

    evidence = release_report.collect_release_evidence()

    report = release_report.markdown_report(
        evidence
    )

    for name in [
        "Package / Version",
        "Configuration",
        "Core Simulation",
        "Baseline Benchmark",
        "Scenario Benchmark",
        "Uncertainty Benchmark",
        "Master Evaluation",
        "Scientific Evaluation",
        "Performance Benchmark",
        "Automated Tests",
    ]:
        assert name in report


def test_markdown_report_contains_scientific_caveat():
    """The report must not overclaim economic prediction."""

    evidence = release_report.collect_release_evidence()

    report = release_report.markdown_report(
        evidence
    )

    assert "does **not** establish" in report
    assert "predict" in report.lower()
    assert "real-world" in report.lower()


def test_markdown_report_contains_reproducibility():
    """The report should document reproducibility."""

    evidence = release_report.collect_release_evidence()

    report = release_report.markdown_report(
        evidence
    )

    assert "## Reproducibility" in report
    assert "periods = 12" in report
    assert "trials  = 1000" in report
    assert "seed    = 42" in report


def test_markdown_report_contains_limitations():
    """The report should explicitly document limitations."""

    evidence = release_report.collect_release_evidence()

    report = release_report.markdown_report(
        evidence
    )

    assert "## Limitations" in report
    assert "research prototype" in report.lower()
    assert "empirical validation" in report.lower()


def test_markdown_report_status():
    """The report should reflect actual gate readiness."""

    evidence = release_report.collect_release_evidence()

    report = release_report.markdown_report(
        evidence
    )

    if evidence["release_gate"]["ready"]:
        assert "READY FOR RC1" in report
    else:
        assert "NOT READY FOR RC1" in report


# ---------------------------------------------------------------------------
# File output
# ---------------------------------------------------------------------------


def test_save_json(tmp_path):
    """JSON evidence should be written correctly."""

    evidence = release_report.collect_release_evidence()

    output = (
        tmp_path
        / "release_evidence.json"
    )

    release_report.save_json(
        evidence,
        output,
    )

    assert output.exists()

    loaded = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert loaded["release"]["name"] == "GEDT v11.0"
    assert loaded["release"]["candidate"] == "RC1"


def test_save_markdown(tmp_path):
    """Markdown report should be written correctly."""

    evidence = release_report.collect_release_evidence()

    content = release_report.markdown_report(
        evidence
    )

    output = (
        tmp_path
        / "release_report.md"
    )

    release_report.save_markdown(
        content,
        output,
    )

    assert output.exists()

    loaded = output.read_text(
        encoding="utf-8"
    )

    assert "# GEDT v11.0 RC1" in loaded


def test_json_is_serializable():
    """Entire release evidence package must be JSON serializable."""

    evidence = release_report.collect_release_evidence()

    serialized = json.dumps(
        evidence,
        indent=2,
    )

    assert isinstance(serialized, str)
    assert len(serialized) > 100


# ---------------------------------------------------------------------------
# Determinism of structure
# ---------------------------------------------------------------------------


def test_repeated_collection_preserves_structure():
    """Repeated release collection should preserve the same structure."""

    first = release_report.collect_release_evidence()
    second = release_report.collect_release_evidence()

    assert (
        first["release"]
        == second["release"]
    )

    assert (
        first["release_gate"]["checks_total"]
        == second["release_gate"]["checks_total"]
    )

    first_names = [
        check["name"]
        for check in first["release_gate"]["checks"]
    ]

    second_names = [
        check["name"]
        for check in second["release_gate"]["checks"]
    ]

    assert first_names == second_names


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


def test_release_report_end_to_end(tmp_path):
    """Exercise the complete evidence-generation workflow."""

    evidence = release_report.collect_release_evidence()

    release_report.validate_release_evidence(
        evidence
    )

    markdown = release_report.markdown_report(
        evidence
    )

    json_output = (
        tmp_path
        / "gedt_rc1.json"
    )

    markdown_output = (
        tmp_path
        / "gedt_rc1.md"
    )

    release_report.save_json(
        evidence,
        json_output,
    )

    release_report.save_markdown(
        markdown,
        markdown_output,
    )

    assert json_output.exists()
    assert markdown_output.exists()

    loaded = json.loads(
        json_output.read_text(
            encoding="utf-8"
        )
    )

    assert loaded["release"]["candidate"] == "RC1"

    markdown_text = markdown_output.read_text(
        encoding="utf-8"
    )

    assert "GEDT v11.0 RC1" in markdown_text
    assert "Release Gate" in markdown_text
    assert "Limitations" in markdown_text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_main_is_callable():
    """The module must expose a CLI entry point."""

    assert callable(
        release_report.main
    )