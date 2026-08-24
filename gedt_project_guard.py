"""
GEDT Project Guard

Safe project-level validation utilities.

This file intentionally does NOT modify, delete, or rewrite application
source code. It checks project configuration and reports problems.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tomllib


ROOT = Path(__file__).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"


def check_pyproject() -> bool:
    """Validate pyproject.toml syntax without modifying it."""
    if not PYPROJECT.exists():
        print("ERROR: pyproject.toml was not found.")
        return False

    try:
        with PYPROJECT.open("rb") as file:
            data = tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        print("ERROR: pyproject.toml is not valid TOML.")
        print(f"Details: {exc}")
        return False

    print("PASS: pyproject.toml is valid TOML.")

    if "build-system" in data:
        print("PASS: build-system section detected.")
    else:
        print("INFO: no build-system section detected.")

    if "project" in data:
        print("PASS: project section detected.")
    else:
        print("INFO: no project section detected.")

    return True


def check_tests_directory() -> bool:
    """Check that the test directory exists."""
    tests = ROOT / "tests"

    if not tests.exists():
        print("INFO: tests directory was not found.")
        return True

    print("PASS: tests directory exists.")
    return True


def main() -> int:
    print("=" * 60)
    print("GEDT PROJECT GUARD")
    print("=" * 60)
    print("Application source code will NOT be modified.")
    print()

    pyproject_ok = check_pyproject()
    tests_ok = check_tests_directory()

    print()
    print("=" * 60)

    if pyproject_ok and tests_ok:
        print("PROJECT GUARD: PASS")
        return 0

    print("PROJECT GUARD: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())