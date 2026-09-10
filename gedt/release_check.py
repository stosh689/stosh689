"""
GEDT v11.0 Release Check

Validates the main GEDT package before release.
"""

from __future__ import annotations

import sys
import traceback


EXPECTED_VERSION = "11.0.0"


def check_import() -> bool:
    print("[1/6] Package import")

    try:
        import gedt

        version = getattr(gedt, "__version__", None)

        print(f"      Version: {version}")

        if version != EXPECTED_VERSION:
            raise RuntimeError(
                f"Expected {EXPECTED_VERSION}, found {version}"
            )

        print("      PASS")
        return True

    except Exception as exc:
        print(f"      FAIL: {exc}")
        return False


def check_configuration() -> bool:
    print("[2/6] Configuration")

    try:
        from gedt.config import GEDTConfig

        config = GEDTConfig()
        config.validate()

        print(f"      Periods: {config.periods}")
        print(f"      Trials: {config.trials}")
        print(f"      Seed: {config.seed}")
        print("      PASS")

        return True

    except Exception as exc:
        print(f"      FAIL: {exc}")
        traceback.print_exc()
        return False


def check_simulation() -> bool:
    print("[3/6] Economic simulation")

    try:
        from gedt.algorithm_engine import (
            EconomicState,
            Scenario,
            simulate,
        )

        initial = EconomicState(
            period=0,
            gdp=1000.0,
            inflation=0.02,
            unemployment=0.05,
        )

        scenario = Scenario(
            name="release_baseline",
            demand_shock=0.0,
            supply_shock=0.0,
            policy_rate_change=0.0,
        )

        result = simulate(
            initial=initial,
            periods=12,
            scenario=scenario,
        )

        expected_states = 13

        if len(result.states) != expected_states:
            raise RuntimeError(
                f"Expected {expected_states} states, "
                f"received {len(result.states)}"
            )

        if result.final_gdp <= 0:
            raise RuntimeError("Final GDP must be positive")

        print(f"      Initial GDP: {result.initial_gdp:.6f}")
        print(f"      Final GDP:   {result.final_gdp:.6f}")
        print(f"      GDP growth:  {result.gdp_growth:.6f}")
        print("      PASS")

        return True

    except Exception as exc:
        print(f"      FAIL: {exc}")
        traceback.print_exc()
        return False


def check_monte_carlo() -> bool:
    print("[4/6] Monte Carlo")

    try:
        from gedt.algorithm_engine import (
            EconomicState,
            Scenario,
            monte_carlo,
        )

        initial = EconomicState(
            period=0,
            gdp=1000.0,
            inflation=0.02,
            unemployment=0.05,
        )

        scenario = Scenario(
            name="release_monte_carlo",
            demand_shock=0.0,
            supply_shock=0.0,
            policy_rate_change=0.0,
        )

        result = monte_carlo(
            initial=initial,
            scenario=scenario,
            periods=12,
            trials=100,
            seed=42,
        )

        if result.trials != 100:
            raise RuntimeError(
                f"Expected 100 trials, received {result.trials}"
            )

        if not isinstance(result.mean_final_gdp, float):
            raise RuntimeError("Monte Carlo GDP result is not numeric")

        print(f"      Trials: {result.trials}")
        print(f"      Mean GDP: {result.mean_final_gdp:.6f}")
        print("      PASS")

        return True

    except Exception as exc:
        print(f"      FAIL: {exc}")
        traceback.print_exc()
        return False


def check_tests() -> bool:
    print("[5/6] Automated tests")

    try:
        import pytest

        exit_code = pytest.main(
            [
                "-ra",
                "tests",
            ]
        )

        if exit_code != 0:
            raise RuntimeError(
                f"pytest returned exit code {exit_code}"
            )

        print("      PASS")
        return True

    except Exception as exc:
        print(f"      FAIL: {exc}")
        traceback.print_exc()
        return False


def check_full_pipeline() -> bool:
    print("[6/6] Full GEDT pipeline")

    try:
        from gedt.__main__ import run_gedt

        result = run_gedt(
            periods=12,
            trials=100,
            seed=42,
        )

        required_keys = {
            "gedt_version",
            "periods",
            "trials",
            "seed",
            "initial_state",
            "baseline",
            "scenario_results",
            "monte_carlo",
            "engine_report",
        }

        missing = required_keys - set(result.keys())

        if missing:
            raise RuntimeError(
                f"Missing pipeline fields: {sorted(missing)}"
            )

        if result["gedt_version"] != EXPECTED_VERSION:
            raise RuntimeError(
                f"Unexpected version: {result['gedt_version']}"
            )

        if result["periods"] != 12:
            raise RuntimeError("Pipeline periods are incorrect")

        if result["trials"] != 100:
            raise RuntimeError("Pipeline trial count is incorrect")

        print(f"      Version: {result['gedt_version']}")
        print(f"      Periods: {result['periods']}")
        print(f"      Trials: {result['trials']}")
        print("      PASS")

        return True

    except Exception as exc:
        print(f"      FAIL: {exc}")
        traceback.print_exc()
        return False


def main() -> int:
    print()
    print("=" * 60)
    print("GEDT v11.0 RELEASE VALIDATION")
    print("=" * 60)
    print()

    checks = [
        check_import,
        check_configuration,
        check_simulation,
        check_monte_carlo,
        check_tests,
        check_full_pipeline,
    ]

    passed = 0

    for check in checks:
        if check():
            passed += 1
        print()

    total = len(checks)

    print("=" * 60)
    print(f"RESULT: {passed}/{total} checks passed")
    print("=" * 60)

    if passed == total:
        print()
        print("GEDT v11.0 RELEASE STATUS: PASS")
        print("The release validation gate has passed.")
        return 0

    print()
    print("GEDT v11.0 RELEASE STATUS: NOT READY")
    print("One or more validation checks failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())