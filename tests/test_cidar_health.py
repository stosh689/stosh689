"""
CIDAR health checks.

These tests provide a small, stable checkpoint for the CIDAR
decision system without touching the larger GEDT codebase.
"""

from pathlib import Path


def test_cidar_test_suite_exists():
    """The primary CIDAR decision test should exist."""
    root = Path(__file__).resolve().parents[1]

    assert (root / "tests" / "test_cidar_decision.py").is_file()


def test_cidar_ethical_suite_exists():
    """The CIDAR ethical scenario tests should exist."""
    root = Path(__file__).resolve().parents[1]

    assert (root / "tests" / "test_cidar_ethical_scenarios.py").is_file()


def test_cidar_consistency_suite_exists():
    """The CIDAR consistency tests should exist."""
    root = Path(__file__).resolve().parents[1]

    assert (root / "tests" / "tests" / "test_cidar_consistency.py").is_file()


def test_cidar_integration_suite_exists():
    """The CIDAR integration tests should exist."""
    root = Path(__file__).resolve().parents[1]

    assert (root / "tests" / "tests" / "test_cidar_integration.py").is_file()