from pathlib import Path

from src.gedt.project_health import (
    ProjectHealth,
    check_project_health,
    format_health_report,
)


def test_project_health_returns_valid_result():
    """GEDT project metadata should produce a health result."""
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"

    health = check_project_health(pyproject)

    assert isinstance(health, ProjectHealth)
    assert health.name == "gedt"
    assert health.version
    assert health.python_requirement
    assert health.dependency_count >= 1


def test_project_health_is_healthy():
    """The cleaned project configuration should be healthy."""
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"

    health = check_project_health(pyproject)

    assert health.healthy is True


def test_health_report_contains_status():
    """The generated report should contain a clear status."""
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"

    health = check_project_health(pyproject)
    report = format_health_report(health)

    assert "GEDT PROJECT HEALTH" in report
    assert "Status: HEALTHY" in report
    assert "Name: gedt" in report