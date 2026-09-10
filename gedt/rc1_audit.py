"""
GEDT v11.0.0-RC1 Final Audit

Runs the final release-candidate audit and produces a machine-readable
audit report.

Usage:
    python rc1_audit.py

Output:
    results/gedt_v11_rc1_audit.json
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_VERSION = "11.0.0"
EXPECTED_TAG = "v11.0.0-rc1"

REQUIRED_FILES = [
    "README.md",
    "pyproject.toml",
    "RELEASE_MANIFEST.json",
    "RELEASE_CHECKLIST.md",
    "RELEASE_NOTES_v11.0-RC1.md",
    "RC1_RELEASE_INDEX.md",
    "release_check.py",
    "release_report.py",
    "validate_release.py",
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


def check(name: str, passed: bool, message: str) -> dict:
    status = "PASS" if passed else "FAIL"

    print(f"[{status}] {name}: {message}")

    return {
        "name": name,
        "passed": passed,
        "message": message,
    }


def check_structure() -> dict:
    missing = [
        path
        for path in REQUIRED_FILES
        if not (ROOT / path).exists()
    ]

    if missing:
        return check(
            "Project structure",
            False,
            "Missing: " + ", ".join(missing),
        )

    return check(
        "Project structure",
        True,
        f"{len(REQUIRED_FILES)} required files present",
    )


def check_manifest() -> dict:
    path = ROOT / "RELEASE_MANIFEST.json"

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        return check(
            "Release manifest",
            False,
            str(exc),
        )

    valid = (
        data.get("project") == "GEDT"
        and data.get("version") == EXPECTED_VERSION
        and data.get("release_candidate") == "RC1"
    )

    return check(
        "Release manifest",
        valid,
        "GEDT 11.0.0 RC1 metadata verified"
        if valid
        else "Manifest metadata is incorrect",
    )


def run_command(
    name: str,
    command: list[str],
) -> dict:
    start = time.perf_counter()

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

    message = (
        f"exit={result.returncode}, "
        f"time={elapsed:.2f}s"
    )

    return check(
        name,
        passed,
        message,
    )


def check_version() -> dict:
    return run_command(
        "Package version",
        [
            sys.executable,
            "-m",
            "gedt",
            "--version",
        ],
    )


def check_tests() -> dict:
    return run_command(
        "Automated tests",
        [
            sys.executable,
            "-m",
            "pytest",
            "-ra",
        ],
    )


def check_release_gate() -> dict:
    return run_command(
        "Release gate",
        [
            sys.executable,
            "release_check.py",
        ],
    )


def check_git_tag() -> dict:
    result = subprocess.run(
        [
            "git",
            "tag",
            "--list",
            EXPECTED_TAG,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    found = EXPECTED_TAG in result.stdout.splitlines()

    return check(
        "RC1 Git tag",
        found,
        EXPECTED_TAG if found else "RC1 tag not found",
    )


def check_git_clean() -> dict:
    result = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    clean = result.returncode == 0 and not result.stdout.strip()

    return check(
        "Git working tree",
        clean,
        "clean"
        if clean
        else "uncommitted changes detected",
    )


def run_audit() -> dict:
    start = time.perf_counter()

    print("=" * 70)
    print("GEDT v11.0.0-RC1 FINAL AUDIT")
    print("=" * 70)
    print()

    results = [
        check_structure(),
        check_manifest(),
        check_version(),
        check_tests(),
        check_release_gate(),
        check_git_tag(),
        check_git_clean(),
    ]

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    total = len(results)

    score = (
        passed / total * 100.0
        if total
        else 0.0
    )

    elapsed = time.perf_counter() - start

    ready = passed == total

    report = {
        "project": "GEDT",
        "version": EXPECTED_VERSION,
        "release_candidate": "RC1",
        "tag": EXPECTED_TAG,
        "checks_passed": passed,
        "checks_total": total,
        "score_percent": round(score, 2),
        "ready_for_stable": ready,
        "elapsed_seconds": round(elapsed, 4),
        "results": results,
    }

    print()
    print("=" * 70)
    print("FINAL AUDIT RESULT")
    print("=" * 70)
    print(
        f"Checks passed: {passed}/{total}"
    )
    print(
        f"Audit score: {score:.2f}%"
    )

    if ready:
        print()
        print("RC1 STATUS: PASSED")
        print("GEDT v11.0.0 is ready for stable-release review.")
    else:
        print()
        print("RC1 STATUS: NOT READY")
        print("Fix failed checks before stable release.")

    print("=" * 70)

    return report


def main() -> int:
    report = run_audit()

    output = (
        ROOT
        / "results"
        / "gedt_v11_rc1_audit.json"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print()
    print(f"Audit report: {output}")

    return 0 if report["ready_for_stable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())