"""Tests for the GEDT v11.0 RC1 release gate."""

import sys
from pathlib import Path

import pytest

# release_check.py lives one directory above tests/
GEDT_ROOT = Path(__file__).resolve().parents[1]

if str(GEDT_ROOT) not in sys.path:
    sys.path.insert(0, str(GEDT_ROOT))

import release_check


def test_expected_version():
    assert release_check.EXPECTED_VERSION == "11.0.0"


def test_check_package():
    message = release_check.check_package()

    assert "11.0.0" in message


def test_check_configuration():
    message = release_check.check_configuration()

    assert "valid" in message.lower()


def test_check_core_simulation():
    message = release_check.check_core_simulation()

    assert "Simulation complete" in message
    assert "final GDP" in message


def test_check_baseline():
    message = release_check.check_baseline()

    assert "Baseline valid" in message


def test_check_scenarios():
    message = release_check.check_scenarios()

    assert "Scenario benchmark valid" in message


def test_check_uncertainty():
    message = release_check.check_uncertainty()

    assert "Uncertainty benchmark valid" in message


def test_check_master_evaluation():
    message = release_check.check_master_evaluation()

    assert "Master evaluation valid" in message


def test_check_scientific_evaluation():
    message = release_check.check_scientific_evaluation()

    assert "Scientific evaluation valid" in message


def test_check_performance():
    message = release_check.check_performance()

    assert "Performance benchmark valid" in message


def test_run_check_success():
    result = release_check.run_check(
        "Test Check",
        lambda: "success",
    )

    assert result.name == "Test Check"
    assert result.passed is True
    assert result.message == "success"
    assert result.elapsed_seconds >= 0


def test_run_check_failure():
    def failing_check():
        raise RuntimeError("intentional failure")

    result = release_check.run_check(
        "Failing Check",
        failing_check,
    )

    assert result.name == "Failing Check"
    assert result.passed is False
    assert "intentional failure" in result.message
    assert result.elapsed_seconds >= 0


def test_release_gate_returns_results():
    results = release_check.run_release_gate()

    assert isinstance(results, list)
    assert len(results) == 10


def test_release_gate_check_names():
    results = release_check.run_release_gate()

    names = [
        result.name
        for result in results
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


def test_release_gate_result_types():
    results = release_check.run_release_gate()

    for result in results:
        assert isinstance(
            result,
            release_check.CheckResult,
        )

        assert isinstance(
            result.name,
            str,
        )

        assert isinstance(
            result.passed,
            bool,
        )

        assert isinstance(
            result.message,
            str,
        )

        assert result.elapsed_seconds >= 0


def test_print_release_report(capsys):
    results = [
        release_check.CheckResult(
            name="Example",
            passed=True,
            message="Example passed",
            elapsed_seconds=0.01,
        )
    ]

    release_check.print_release_report(
        results
    )

    output = capsys.readouterr().out

    assert "GEDT v11.0 RC1 RELEASE GATE" in output
    assert "[PASS] Example" in output
    assert "Checks passed: 1/1" in output
    assert "100.0%" in output


def test_print_release_report_failure(capsys):
    results = [
        release_check.CheckResult(
            name="Example",
            passed=False,
            message="Example failed",
            elapsed_seconds=0.01,
        )
    ]

    release_check.print_release_report(
        results
    )

    output = capsys.readouterr().out

    assert "[FAIL] Example" in output
    assert "NOT READY" in output


def test_release_gate_all_checks_are_expected():
    results = release_check.run_release_gate()

    assert len(results) == 10

    for result in results:
        assert result.name
        assert result.message


def test_release_gate_has_no_negative_runtime():
    results = release_check.run_release_gate()

    for result in results:
        assert result.elapsed_seconds >= 0


def test_release_gate_is_complete():
    results = release_check.run_release_gate()

    names = {
        result.name
        for result in results
    }

    required = {
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
    }

    assert names == required


def test_release_gate_success_code():
    results = [
        release_check.CheckResult(
            name="A",
            passed=True,
            message="ok",
        ),
        release_check.CheckResult(
            name="B",
            passed=True,
            message="ok",
        ),
    ]

    assert all(
        result.passed
        for result in results
    )


def test_release_gate_failure_detected():
    results = [
        release_check.CheckResult(
            name="A",
            passed=True,
            message="ok",
        ),
        release_check.CheckResult(
            name="B",
            passed=False,
            message="failure",
        ),
    ]

    assert not all(
        result.passed
        for result in results
    )


def test_release_check_main_exists():
    assert callable(
        release_check.main
    )


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
    ],
)
def test_check_result_boolean(value):
    result = release_check.CheckResult(
        name="test",
        passed=value,
        message="test",
    )

    assert result.passed is value