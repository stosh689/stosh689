from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HealthResult:
    name: str
    passed: bool
    message: str


def check_package() -> HealthResult:
    try:
        import gedt

        version = getattr(gedt, "__version__", "unknown")

        return HealthResult(
            "GEDT package",
            True,
            f"import successful, version {version}",
        )
    except Exception as exc:
        return HealthResult(
            "GEDT package",
            False,
            f"import failed: {exc}",
        )


def check_project_files() -> HealthResult:
    package_dir = Path(__file__).resolve().parent

    required = (
        "__init__.py",
        "__main__.py",
        "project_health.py",
    )

    missing = [
        name for name in required
        if not (package_dir / name).is_file()
    ]

    if missing:
        return HealthResult(
            "Project files",
            False,
            "missing: " + ", ".join(missing),
        )

    return HealthResult(
        "Project files",
        True,
        "all essential files present",
    )


def check_build_configuration() -> HealthResult:
    package_root = Path(__file__).resolve().parents[2]
    pyproject = package_root / "pyproject.toml"

    if not pyproject.is_file():
        return HealthResult(
            "Build configuration",
            False,
            "gedt/pyproject.toml not found",
        )

    try:
        text = pyproject.read_text(encoding="utf-8")

        required = (
            "[build-system]",
            "[project]",
            "[tool.setuptools]",
        )

        missing = [
            section for section in required
            if section not in text
        ]

        if missing:
            return HealthResult(
                "Build configuration",
                False,
                "missing: " + ", ".join(missing),
            )

        return HealthResult(
            "Build configuration",
            True,
            "configuration detected",
        )

    except OSError as exc:
        return HealthResult(
            "Build configuration",
            False,
            str(exc),
        )


def run_health_check() -> list[HealthResult]:
    return [
        check_package(),
        check_project_files(),
        check_build_configuration(),
    ]


def main() -> int:
    print("GEDT PROJECT HEALTH")
    print("=" * 60)

    results = run_health_check()

    passed = True

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.message}")

        if not result.passed:
            passed = False

    print("=" * 60)
    print("OVERALL:", "PASS" if passed else "FAIL")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())