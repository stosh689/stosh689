"""
GEDT Project Health

Lightweight validation and health reporting for the GEDT project.

This module reads project metadata from pyproject.toml and reports
whether the essential project configuration is healthy.

It does not execute or modify the GEDT simulation engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import tomllib


@dataclass(frozen=True)
class ProjectHealth:
    """Result of a GEDT project health check."""

    name: str
    version: str
    python_requirement: str
    dependency_count: int
    has_build_system: bool
    has_project_metadata: bool
    has_package_configuration: bool

    @property
    def healthy(self) -> bool:
        """Return True when all required project metadata is present."""
        return all(
            (
                self.has_build_system,
                self.has_project_metadata,
                self.has_package_configuration,
                bool(self.name),
                bool(self.version),
                bool(self.python_requirement),
            )
        )


def find_pyproject(start: Path | None = None) -> Path:
    """
    Locate pyproject.toml.

    Searches the supplied directory and then walks upward through
    its parent directories.
    """
    current = (start or Path.cwd()).resolve()

    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        candidate = directory / "pyproject.toml"

        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "Could not locate pyproject.toml."
    )


def load_project_metadata(
    pyproject_path: Path | None = None,
) -> dict:
    """Load and parse pyproject.toml."""
    path = pyproject_path or find_pyproject()

    with path.open("rb") as file:
        return tomllib.load(file)


def check_project_health(
    pyproject_path: Path | None = None,
) -> ProjectHealth:
    """
    Validate the essential GEDT project metadata.

    Returns a ProjectHealth object rather than raising errors for
    normal validation failures.
    """
    metadata = load_project_metadata(pyproject_path)

    build_system = metadata.get("build-system", {})
    project = metadata.get("project", {})
    setuptools = metadata.get("tool", {}).get(
        "setuptools",
        {},
    )

    package_find = setuptools.get(
        "packages",
        {},
    ).get(
        "find",
        {},
    )

    dependencies = project.get(
        "dependencies",
        [],
    )

    return ProjectHealth(
        name=str(project.get("name", "")),
        version=str(project.get("version", "")),
        python_requirement=str(
            project.get("requires-python", "")
        ),
        dependency_count=len(dependencies),
        has_build_system=bool(
            build_system.get("build-backend")
            and build_system.get("requires")
        ),
        has_project_metadata=bool(
            project.get("name")
            and project.get("version")
            and project.get("description")
        ),
        has_package_configuration=bool(
            package_find.get("where")
        ),
    )


def format_health_report(
    health: ProjectHealth,
) -> str:
    """Create a human-readable project health report."""
    status = "HEALTHY" if health.healthy else "NEEDS_REVIEW"

    return "\n".join(
        (
            "GEDT PROJECT HEALTH",
            "===================",
            f"Status: {status}",
            f"Name: {health.name}",
            f"Version: {health.version}",
            f"Python: {health.python_requirement}",
            f"Dependencies: {health.dependency_count}",
            f"Build system: "
            f"{'OK' if health.has_build_system else 'MISSING'}",
            f"Project metadata: "
            f"{'OK' if health.has_project_metadata else 'MISSING'}",
            f"Package configuration: "
            f"{'OK' if health.has_package_configuration else 'MISSING'}",
        )
    )


def main() -> int:
    """Run the project health check from the command line."""
    try:
        health = check_project_health()
    except (FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        print(f"GEDT PROJECT HEALTH: ERROR")
        print(f"Reason: {exc}")
        return 1

    print(format_health_report(health))

    return 0 if health.healthy else 1


if __name__ == "__main__":
    sys.exit(main())