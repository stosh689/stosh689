"""
GEDT v11.0 RC1 Release Gate

Runs the major release-readiness checks for GEDT:

1. Package import/version
2. Configuration
3. Core simulation
4. Baseline benchmark
5. Scenario benchmark
6. Uncertainty benchmark
7. Master evaluation
8. Scientific evaluation
9. Performance benchmark
10. Automated test suite

The gate does not claim economic prediction accuracy.
It evaluates software integrity, reproducibility, numerical validity,
testing, and computational performance.
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.gedt import __version__
from src.gedt.algorithm_engine import EconomicState, simulate
from src.gedt.benchmark import run_benchmark
from src.gedt.config import DEFAULT_CONFIG
from src.gedt.master_evaluation import (
    run_master_evaluation,
    validate_master_evaluation,
)
from src.gedt.performance_benchmark import (
    run_performance_benchmark,
    validate_performance_benchmark,
)
from src.gedt.scenario_benchmark import (
    run_scenario_benchmark,
)
from src.gedt.scientific_evaluation import (
    build_scientific_evaluation,
    validate_scientific_evaluation,
)
from src.gedt.uncertainty_benchmark import (
    run_uncertainty_benchmark,
)


EXPECTED_VERSION = "11.0.0"

ROOT = Path(__file__).resolve().parent

TEST_COMMAND = [
    sys.executable,
    "-m",
    "pytest",
]


@dataclass
class CheckResult:
    """Result of one release check."""

    name: str
    passed: bool
    message: str
    elapsed_seconds: float = 0.0


def run_check(
    name: str,
    function: Callable[[], str],
) -> CheckResult:
    """Execute one release check safely."""

    start = time.perf_counter()

    try:
        message = function()

        elapsed = time.perf_counter() - start

        return CheckResult(
            name=name,
            passed=True,
            message=message,
            elapsed_seconds=elapsed,
        )

    except Exception as exc:
        elapsed = time.perf_counter() - start

        return CheckResult(
            name=name,
            passed=False,
            message=str(exc),
            elapsed_seconds=elapsed,
        )


def check_package() -> str:
    """Check package version."""

    if __version__ != EXPECTED_VERSION:
        raise RuntimeError(
            f"Expected GEDT {EXPECTED_VERSION}, "
            f"found {__version__}"
        )

    return f"GEDT version {__version__}"


def check_configuration() -> str:
    """Validate default configuration."""

    DEFAULT_CONFIG.validate()

    if DEFAULT_CONFIG.periods < 1:
        raise RuntimeError(
            "Configuration periods must be positive"
        )

    if DEFAULT_CONFIG.trials < 1:
        raise RuntimeError(
            "Configuration trials must be positive"
        )

    return "Default configuration valid"


def check_core_simulation() -> str:
    """Run a deterministic core simulation."""

    initial = EconomicState(
        period=0,
        gdp=1000.0,
        inflation=0.02,
        unemployment=0.05,
    )

    result = simulate(
        initial,
        periods=12,
    )

    if len(result.states) != 13:
        raise RuntimeError(
            "Unexpected simulation state count"
        )

    if result.final_gdp <= 0:
        raise RuntimeError(
            "Simulation produced non-positive GDP"
        )

    return (
        f"Simulation complete; "
        f"final GDP={result.final_gdp:.6f}"
    )


def check_baseline() -> str:
    """Run baseline benchmark."""

    result = run_benchmark(
        periods=12,
        trials=25,
        seed=42,
    )

    deterministic = result["deterministic"]

    if deterministic["final_gdp"] <= 0:
        raise RuntimeError(
            "Baseline produced non-positive GDP"
        )

    return (
        f"Baseline valid; "
        f"final GDP={deterministic['final_gdp']:.6f}"
    )


def check_scenarios() -> str:
    """Run scenario benchmark."""

    result = run_scenario_benchmark(
        periods=12,
    )

    scenarios = result["scenarios"]

    if len(scenarios) < 2:
        raise RuntimeError(
            "Scenario benchmark contains fewer than two scenarios"
        )

    return (
        f"Scenario benchmark valid; "
        f"{len(scenarios)} scenarios"
    )


def check_uncertainty() -> str:
    """Run uncertainty benchmark."""

    result = run_uncertainty_benchmark(
        periods=12,
        trials=25,
        seed=42,
    )

    if "monte_carlo" not in result:
        raise RuntimeError(
            "Monte Carlo results missing"
        )

    monte_carlo = result["monte_carlo"]

    if monte_carlo["trials"] != 25:
        raise RuntimeError(
            "Unexpected Monte Carlo trial count"
        )

    if monte_carlo["mean_final_gdp"] <= 0:
        raise RuntimeError(
            "Monte Carlo mean GDP is invalid"
        )

    return (
        f"Uncertainty benchmark valid; "
        f"{monte_carlo['trials']} trials"
    )


def check_master_evaluation() -> str:
    """Run and validate master evaluation."""

    report = run_master_evaluation(
        periods=6,
        trials=25,
        seed=42,
    )

    validate_master_evaluation(report)

    return "Master evaluation valid"


def check_scientific_evaluation() -> str:
    """Run scientific evaluation."""

    master = run_master_evaluation(
        periods=6,
        trials=25,
        seed=42,
    )

    evaluation = build_scientific_evaluation(
        master
    )

    validate_scientific_evaluation(
        evaluation
    )

    if evaluation["quality_score"] < 0:
        raise RuntimeError(
            "Scientific quality score is invalid"
        )

    return (
        f"Scientific evaluation valid; "
        f"quality={evaluation['quality_percentage']:.1f}%"
    )


def check_performance() -> str:
    """Run performance benchmark."""

    benchmark = run_performance_benchmark(
        periods=4,
        trials=25,
        seed=42,
        repeats=1,
    )

    validate_performance_benchmark(
        benchmark
    )

    seconds = benchmark["statistics"]["mean_seconds"]

    return (
        f"Performance benchmark valid; "
        f"runtime={seconds:.6f}s"
    )


def check_tests() -> str:
    """Run the automated test suite."""

    result = subprocess.run(
        TEST_COMMAND,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        output = (
            result.stdout[-3000:]
            + "\n"
            + result.stderr[-3000:]
        )

        raise RuntimeError(
            "Automated tests failed:\n"
            + output
        )

    summary = result.stdout.strip().splitlines()

    if summary:
        return summary[-1]

    return "Automated tests passed"


def run_release_gate() -> list[CheckResult]:
    """Run every RC1 release check."""

    checks = [
        (
            "Package / Version",
            check_package,
        ),
        (
            "Configuration",
            check_configuration,
        ),
        (
            "Core Simulation",
            check_core_simulation,
        ),
        (
            "Baseline Benchmark",
            check_baseline,
        ),
        (
            "Scenario Benchmark",
            check_scenarios,
        ),
        (
            "Uncertainty Benchmark",
            check_uncertainty,
        ),
        (
            "Master Evaluation",
            check_master_evaluation,
        ),
        (
            "Scientific Evaluation",
            check_scientific_evaluation,
        ),
        (
            "Performance Benchmark",
            check_performance,
        ),
        (
            "Automated Tests",
            check_tests,
        ),
    ]

    results = []

    for name, function in checks:
        result = run_check(
            name,
            function,
        )

        results.append(result)

    return results


def print_release_report(
    results: list[CheckResult],
) -> None:
    """Print the RC1 release report."""

    passed = sum(
        result.passed
        for result in results
    )

    total = len(results)

    percentage = (
        passed / total * 100
        if total
        else 0.0
    )

    release_ready = (
        passed == total
    )

    print()
    print("=" * 80)
    print("GEDT v11.0 RC1 RELEASE GATE")
    print("=" * 80)

    print()

    for result in results:
        status = (
            "PASS"
            if result.passed
            else "FAIL"
        )

        print(
            f"[{status}] "
            f"{result.name}"
        )

        print(
            f"       {result.message}"
        )

        print(
            f"       runtime="
            f"{result.elapsed_seconds:.4f}s"
        )

    print()
    print("-" * 80)

    print(
        f"Checks passed: "
        f"{passed}/{total}"
    )

    print(
        f"Release-gate score: "
        f"{percentage:.1f}%"
    )

    print()

    if release_ready:
        print(
            "RELEASE STATUS: READY FOR RC1"
        )
    else:
        print(
            "RELEASE STATUS: NOT READY"
        )

    print()
    print("=" * 80)
    print()


def main() -> int:
    """Run the release gate."""

    results = run_release_gate()

    print_release_report(
        results
    )

    return (
        0
        if all(
            result.passed
            for result in results
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )