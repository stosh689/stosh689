"""
Tests for the unified GEDT validation entry point.
"""

from pathlib import Path

from src.gedt.gedt_validation import ROOT


def test_repository_root_exists():
    """The validator should resolve the repository root."""
    assert ROOT.is_dir()


def test_pyproject_exists():
    """The repository must contain pyproject.toml."""
    assert (ROOT / "pyproject.toml").is_file()


def test_cidar_decision_tests_exist():
    """The core CIDAR decision tests must be present."""
    assert (
        ROOT / "tests" / "test_cidar_decision.py"
    ).is_file()


def test_project_health_module_exists():
    """The project-health module must be present."""
    assert (
        ROOT / "src" / "gedt" / "project_health.py"
    ).is_file()


def test_project_validator_module_exists():
    """The project validator must be present."""
    assert (
        ROOT / "src" / "gedt" / "validate_project.py"
    ).is_file()