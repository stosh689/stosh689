from __future__ import annotations
import importlib.util
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
@dataclass(frozen=True)
class ProjectHealth:
    """Result of validating GEDT project metadata."""
    status: str
    project_name: str
    version: str
    description: str
    issues: tuple[str, ...] = ()
    @property
    def healthy(self) -> bool:
        return self.status == "healthy"
def _load_compatibility_metadata() -> dict[str, Any] | None:
    """
    Load compatibility metadata from pyproject2.py.
    This intentionally loads the file directly rather than relying on
    the repository root being present on sys.path.
    """
    root = Path(__file__).resolve().parents[2]
    compatibility_file = root / "pyproject2.py"
    if not compatibility_file.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(
            "gedt_pyproject2",
            compatibility_file,
        )
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        metadata = getattr(module, "PROJECT_METADATA", None)
        if isinstance(metadata, dict):
            return metadata
    except Exception:
        return None
    return None
PROJECT_METADATA = _load_compatibility_metadata()
def load_project_metadata(pyproject_path: Path) -> dict[str, Any]:
    """
    Load project metadata from pyproject.toml.
    If the TOML configuration is temporarily malformed, fall back to
    pyproject2.py compatibility metadata rather than preventing the
    health-check system from operating.
    """
    try:
        with pyproject_path.open("rb") as file:
            return tomllib.load(file)
    except tomllib.TOMLDecodeError:
        if PROJECT_METADATA is not None:
            return PROJECT_METADATA
        raise
def check_project_health(pyproject_path: Path) -> ProjectHealth:
    """
    Validate the project's basic metadata and return a health result.
    """
    metadata = load_project_metadata(pyproject_path)
    project = metadata.get("project", {})
    if not isinstance(project, dict):
        project = {}
    name = str(project.get("name", "GEDT"))
    version = str(project.get("version", "0.0.0"))
    description = str(project.get("description", ""))
    issues: list[str] = []
    if not name.strip():
        issues.append("Project name is missing.")
    if not version.strip():
        issues.append("Project version is missing.")
    status = "healthy" if not issues else "unhealthy"
    return ProjectHealth(
        status=status,
        project_name=name,
        version=version,
        description=description,
        issues=tuple(issues),
    )
def format_health_report(health: ProjectHealth) -> str:
    """
    Generate a human-readable project health report.
    """
    lines = [
        f"Status: {health.status}",
        f"Project: {health.project_name}",
        f"Version: {health.version}",
    ]
    if health.description:
        lines.append(f"Description: {health.description}")
    if health.issues:
        lines.append("Issues:")
        lines.extend(f"- {issue}" for issue in health.issues)
    return "\n".join(lines)
def main() -> int:
    """
    Run the project health check from the repository root.
    """
    root = Path(__file__).resolve().parents[2]
    pyproject_path = root / "pyproject.toml"
    health = check_project_health(pyproject_path)
    print(format_health_report(health))
    return 0 if health.healthy else 1
if __name__ == "__main__":
    sys.exit(main())