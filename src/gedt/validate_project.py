"""
GEDT Project Validator

Command-line validation of the GEDT project configuration.

This module validates pyproject.toml through the existing
project_health module. It does not modify project files.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .project_health import (
    check_project_health,
    format_health_report,
)


def validate_project(
    project_root: Path | None = None,
) -> bool:
    """
    Validate GEDT project configuration.

    Returns:
        True when the project configuration is healthy.
        False otherwise.
    """
    root = (
        project_root
        or Path(__file__).resolve().parents[2]
    )

    pyproject = root / "pyproject.toml"

    health = check_project_health(pyproject)

    print(format_health_report(health))

    return health.healthy


def main() -> int:
    """CLI entry point."""
    try:
        healthy = validate_project()
    except Exception as exc:
        print(
            f"GEDT PROJECT VALIDATION ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    if healthy:
        print("\nGEDT validation: PASS")
        return 0

    print("\nGEDT validation: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())