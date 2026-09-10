"""
GEDT v11.0 — Complete Release Validation

Runs the main release checks in a single command.

Usage:
    python validate_release.py

Optional:
    python validate_release.py --quick
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_VERSION = "11.0.0"


def run_command(name: str, command: list[str]) -> dict:
    """Run one validation command and capture its result."""
    start = time.perf_counter()

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)
    print("$", " ".join(command))

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    elapsed = time.perf_counter() - start

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    passed = result.returncode == 0

    print(
        f"[{'PASS' if passed else 'FAIL'}] "
        f"{name} ({elapsed:.2f}s)"
    )

    return {
        "name": name,
        "passed": passed,
        "return_code": result.returncode,
        "elapsed_seconds": round(elapsed, 4),
    }


def verify_structure() -> dict:
    """Verify required GEDT files exist."""
    required = [
        "README.md",
        "pyproject.toml",
        "release_check.py",
        "release_report.py",
        "RELEASE_CHECKLIST.md",
        "RELEASE_NOTES_v11.0-RC1.md",
        "RELEASE_MANIFEST.json",
        "src/gedt/__init__.py",
        "src/gedt/__main__.py",
        "src/gedt/algorithm_engine.py",
        "src/gedt/config.py",
        "src/gedt/benchmark.py",
        "src/gedt/scenario_benchmark.py",
        "src/gedt/uncertainty_benchmark.py",
        "src/gedt/master_evaluation.py",
        "src/gedt/scientific_evaluation.py",
        "src/gedt/performance_benchmark.py",
    ]

    missing = [
        path for path in required
        if not (ROOT / path).exists()
    ]

    passed = not missing

    print()
    print("=" * 70)
    print("PROJECT STRUCTURE")
    print("=" * 70)

    if passed:
        print("All required files are present.")
    else:
        print("Missing files:")
        for path in missing:
            print(f"  - {path}")

    return {
        "name": "Project structure",
        "passed": passed,
        "missing": missing,
        "elapsed_seconds": 0.0,
    }


def verify_manifest() -> dict:
    """Verify the release manifest."""
    path = ROOT / "RELEASE_MANIFEST.json"

    print()
    print("=" * 70)
    print("RELEASE MANIFEST")
    print("=" * 70)

    if not path.exists():
        print("Manifest not found.")
        return {
            "name": "Release manifest",
            "passed": False,
            "elapsed_seconds": 0.0,
        }

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        version = data.get("version")
        candidate = data.get("release_candidate")

        if version != EXPECTED_VERSION:
            raise ValueError(
                f"Expected version {EXPECTED_VERSION}, "
                f"found {version}"
            )

        if candidate != "RC1":
            raise ValueError(
                f"Expected RC1, found {candidate}"
            )

        print(f"Version: {version}")
        print(f"Release candidate: {candidate}")
        print("Manifest validation: PASS")

        return {
            "name": "Release manifest",
            "passed": True,
            "elapsed_seconds": 0.0,
        }

    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Manifest validation failed: {exc}")

        return {
            "name": "Release manifest",
            "passed": False,
            "error": str(exc),
            "elapsed_seconds": 0.0,
        }


def run_validation(quick: bool = False) -> dict:
    """Run the complete GEDT release validation."""
    start = time.perf_counter()

    results = []

    results.append(verify_structure())
    results.append(verify_manifest())

    commands = [
        (
            "GEDT version",
            [sys.executable, "-m", "gedt", "--version"],
        ),
        (
            "Automated test suite",
            [sys.executable, "-m", "pytest", "-ra"],
        ),
        (
            "Release gate",
            [sys.executable, "release_check.py"],
        ),
    ]

    if not quick:
        commands.extend(
            [
                (
                    "Baseline benchmark",
                    [
                        sys.executable,
                        "-m",
                        "gedt.benchmark",
                        "--periods",
                        "12",
                        "--trials",
                        "100",
                        "--seed",
                        "42",
                    ],
                ),
                (
                    "Scenario benchmark",
                    [
                        sys.executable,
                        "-m",
                        "gedt.scenario_benchmark",
                        "--periods",
                        "12",
                        "--trials",
                        "100",
                        "--seed",
                        "42",
                    ],
                ),
                (
                    "Uncertainty benchmark",
                    [
                        sys.executable,
                        "-m",
                        "gedt.uncertainty_benchmark",
                        "--periods",
                        "12",
                        "--trials",
                        "100",
                        "--seed",
                        "42",
                    ],
                ),
            ]
        )

    for name, command in commands:
        result = run_command(name, command)
        results.append(result)

    passed = sum(
        1 for result in results
        if result["passed"]
    )

    total = len(results)

    score = (
        (passed / total) * 100.0
        if total
        else 0.0
    )

    elapsed = time.perf_counter() - start

    return {
        "project": "GEDT",
        "version": EXPECTED_VERSION,
        "release_candidate": "RC1",
        "checks_passed": passed,
        "checks_total": total,
        "score_percent": round(score, 2),
        "ready": passed == total,
        "elapsed_seconds": round(elapsed, 4),
        "results": results,
    }


def print_summary(report: dict) -> None:
    """Print final release validation summary."""
    print()
    print("=" * 70)
    print("GEDT v11.0 RC1 RELEASE VALIDATION")
    print("=" * 70)

    print(
        f"Checks passed: "
        f"{report['checks_passed']}/"
        f"{report['checks_total']}"
    )

    print(
        f"Validation score: "
        f"{report['score_percent']:.2f}%"
    )

    print(
        f"Elapsed time: "
        f"{report['elapsed_seconds']:.2f}s"
    )

    print()

    if report["ready"]:
        print("RELEASE STATUS: READY FOR RC1")
    else:
        print("RELEASE STATUS: NOT READY")
        print("Fix the failed checks before release.")

    print("=" * 70)


def main() -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Validate GEDT v11.0 RC1."
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run structural, version, test, and release-gate checks only.",
    )

    parser.add_argument(
        "--output",
        default="results/release_validation.json",
        help="Output JSON report path.",
    )

    args = parser.parse_args()

    report = run_validation(
        quick=args.quick
    )

    output_path = ROOT / args.output
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print_summary(report)

    print()
    print(
        f"Validation report saved to: "
        f"{output_path}"
    )

    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())