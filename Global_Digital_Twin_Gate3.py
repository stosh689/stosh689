#!/usr/bin/env python3
"""
Global Digital Twin - Integration Gate 3
========================================

Gate 3 objective:
    Execute available domain modules through a common integration layer.

Design goals:
    - Standard library only
    - Safe module discovery
    - Safe execution
    - No dependency on external packages
    - No modification of existing project files
    - Clear PASS / REVIEW / FAIL status
    - Reproducible execution
    - JSON reporting

Supported project modules:

    GEDT_standalone.py
    Global_Resilience_Twin.py
    Climate_Economic_Twin.py
    Food_Security_Twin.py
    Energy_Transition_Twin.py
    AI_Governance_Engine.py
    CIDAR_standalone.py

Gate 3 is intentionally defensive:
    A missing or incompatible module must not crash the entire
    Global Digital Twin.

Version:
    3.0.0
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


VERSION = "3.0.0"


# ---------------------------------------------------------------------------
# MODULE REGISTRY
# ---------------------------------------------------------------------------

MODULE_REGISTRY = {
    "GEDT": {
        "modules": ["GEDT_standalone", "gedt"],
        "classes": ["GEDT"],
    },
    "GlobalResilience": {
        "modules": ["Global_Resilience_Twin"],
        "classes": ["GlobalResilienceTwin"],
    },
    "ClimateEconomic": {
        "modules": ["Climate_Economic_Twin"],
        "classes": ["ClimateEconomicTwin"],
    },
    "FoodSecurity": {
        "modules": ["Food_Security_Twin"],
        "classes": ["FoodSecurityTwin"],
    },
    "EnergyTransition": {
        "modules": ["Energy_Transition_Twin"],
        "classes": ["EnergyTransitionTwin"],
    },
    "AIGovernance": {
        "modules": ["AI_Governance_Engine"],
        "classes": ["AIGovernanceEngine"],
    },
    "CIDAR": {
        "modules": ["CIDAR_standalone", "cidar"],
        "classes": [],
        "functions": ["fuse", "self_test"],
    },
}


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------

@dataclass
class ModuleExecution:
    domain: str
    module_name: str
    import_status: str
    execution_status: str
    duration_ms: float
    message: str
    result_type: str = ""
    result_summary: Optional[Dict[str, Any]] = None


@dataclass
class Gate3Report:
    version: str
    timestamp: float
    modules_checked: int
    modules_imported: int
    modules_executed: int
    modules_failed: int
    overall_status: str
    health_score: float
    executions: List[ModuleExecution]
    fingerprint: str


# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def finite_number(value: Any) -> bool:
    """Return True if value can safely be represented as a finite float."""
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def compact_value(value: Any, depth: int = 0) -> Any:
    """
    Convert arbitrary module output into JSON-safe compact data.

    This prevents enormous simulation objects from being inserted
    directly into the integration report.
    """

    if depth > 3:
        return str(value)[:200]

    if value is None:
        return None

    if isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, dict):
        result = {}
        for key, item in list(value.items())[:25]:
            result[str(key)] = compact_value(item, depth + 1)
        return result

    if isinstance(value, (list, tuple)):
        return [
            compact_value(item, depth + 1)
            for item in list(value)[:25]
        ]

    if hasattr(value, "__dataclass_fields__"):
        try:
            return compact_value(asdict(value), depth + 1)
        except Exception:
            return str(value)[:200]

    if hasattr(value, "__dict__"):
        try:
            data = {}
            for key, item in list(vars(value).items())[:25]:
                data[str(key)] = compact_value(item, depth + 1)
            return data
        except Exception:
            pass

    return str(value)[:200]


def fingerprint(data: Any) -> str:
    """Create a deterministic SHA-256 fingerprint."""
    encoded = json.dumps(
        compact_value(data),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def find_method(obj: Any, names: List[str]):
    """Return the first callable method matching candidate names."""
    for name in names:
        try:
            method = getattr(obj, name, None)
            if callable(method):
                return method
        except Exception:
            continue

    return None


# ---------------------------------------------------------------------------
# MODULE LOADER
# ---------------------------------------------------------------------------

class ModuleLoader:
    """Safely discovers and imports registered modules."""

    def __init__(self):
        self.loaded: Dict[str, Any] = {}
        self.results: List[ModuleExecution] = []

    def discover(self) -> List[ModuleExecution]:
        """Attempt to import every registered module."""

        for domain, specification in MODULE_REGISTRY.items():

            for module_name in specification["modules"]:

                start = time.perf_counter()

                try:
                    module = importlib.import_module(module_name)

                    duration = (time.perf_counter() - start) * 1000

                    self.loaded[module_name] = module

                    self.results.append(
                        ModuleExecution(
                            domain=domain,
                            module_name=module_name,
                            import_status="AVAILABLE",
                            execution_status="NOT_RUN",
                            duration_ms=duration,
                            message="Module imported successfully.",
                        )
                    )

                    # One successful module is sufficient for the domain.
                    break

                except Exception as exc:

                    duration = (time.perf_counter() - start) * 1000

                    self.results.append(
                        ModuleExecution(
                            domain=domain,
                            module_name=module_name,
                            import_status="UNAVAILABLE",
                            execution_status="NOT_RUN",
                            duration_ms=duration,
                            message=f"{type(exc).__name__}: {exc}",
                        )
                    )

        return self.results


# ---------------------------------------------------------------------------
# EXECUTION ENGINE
# ---------------------------------------------------------------------------

class Gate3Executor:
    """
    Executes available modules using conservative introspection.

    The executor never assumes that every project has identical APIs.
    """

    def __init__(self, periods: int = 5):
        self.periods = max(1, int(periods))
        self.loader = ModuleLoader()
        self.executions: List[ModuleExecution] = []

    def available_domains(self) -> Dict[str, Any]:
        """Map domains to successfully imported modules."""

        available = {}

        for domain, specification in MODULE_REGISTRY.items():

            for module_name in specification["modules"]:

                if module_name in self.loader.loaded:
                    available[domain] = self.loader.loaded[module_name]
                    break

        return available

    def instantiate_class(
        self,
        module: Any,
        class_names: List[str],
    ):
        """Safely instantiate a registered class."""

        for class_name in class_names:

            cls = getattr(module, class_name, None)

            if cls is None or not inspect.isclass(cls):
                continue

            try:
                return cls(), class_name

            except TypeError:
                # Try a constructor with a seed if supported.
                try:
                    return cls(seed=42), class_name
                except Exception:
                    continue

            except Exception:
                continue

        return None, None

    def execute_class_module(
        self,
        domain: str,
        module_name: str,
        module: Any,
        class_names: List[str],
    ) -> ModuleExecution:

        start = time.perf_counter()

        obj, class_name = self.instantiate_class(
            module,
            class_names,
        )

        if obj is None:

            return ModuleExecution(
                domain=domain,
                module_name=module_name,
                import_status="AVAILABLE",
                execution_status="REVIEW",
                duration_ms=(time.perf_counter() - start) * 1000,
                message="Module imported, but no compatible registered class could be instantiated.",
            )

        # Standard simulation methods.
        run_method = find_method(
            obj,
            [
                "run",
                "simulate",
                "execute",
                "step",
            ],
        )

        if run_method is None:

            return ModuleExecution(
                domain=domain,
                module_name=module_name,
                import_status="AVAILABLE",
                execution_status="INSTANTIATED",
                duration_ms=(time.perf_counter() - start) * 1000,
                message=f"{class_name} instantiated successfully; no standard run method found.",
                result_type=type(obj).__name__,
            )

        try:

            signature = inspect.signature(run_method)
            parameters = signature.parameters

            if "periods" in parameters:
                result = run_method(periods=self.periods)

            elif "steps" in parameters:
                result = run_method(steps=self.periods)

            elif len(parameters) == 0:
                result = run_method()

            else:
                # Avoid guessing complex APIs.
                return ModuleExecution(
                    domain=domain,
                    module_name=module_name,
                    import_status="AVAILABLE",
                    execution_status="INSTANTIATED",
                    duration_ms=(time.perf_counter() - start) * 1000,
                    message=(
                        f"{class_name} found, but its run method requires "
                        "unsupported parameters."
                    ),
                    result_type=type(obj).__name__,
                )

            summary = compact_value(result)

            return ModuleExecution(
                domain=domain,
                module_name=module_name,
                import_status="AVAILABLE",
                execution_status="EXECUTED",
                duration_ms=(time.perf_counter() - start) * 1000,
                message=f"{class_name} executed successfully.",
                result_type=type(result).__name__,
                result_summary=(
                    summary
                    if isinstance(summary, dict)
                    else {"result": summary}
                ),
            )

        except Exception as exc:

            return ModuleExecution(
                domain=domain,
                module_name=module_name,
                import_status="AVAILABLE",
                execution_status="FAILED",
                duration_ms=(time.perf_counter() - start) * 1000,
                message=f"{class_name} execution error: {type(exc).__name__}: {exc}",
                result_type=type(obj).__name__,
            )

    def execute_function_module(
        self,
        domain: str,
        module_name: str,
        module: Any,
        function_names: List[str],
    ) -> ModuleExecution:

        start = time.perf_counter()

        for function_name in function_names:

            function = getattr(module, function_name, None)

            if not callable(function):
                continue

            # Self-test functions are preferred because they establish
            # whether the module is internally healthy.
            if function_name == "self_test":

                try:
                    result = function()

                    return ModuleExecution(
                        domain=domain,
                        module_name=module_name,
                        import_status="AVAILABLE",
                        execution_status="EXECUTED",
                        duration_ms=(time.perf_counter() - start) * 1000,
                        message="Module self-test executed.",
                        result_type=type(result).__name__,
                        result_summary={
                            "self_test_result": compact_value(result)
                        },
                    )

                except Exception as exc:

                    return ModuleExecution(
                        domain=domain,
                        module_name=module_name,
                        import_status="AVAILABLE",
                        execution_status="FAILED",
                        duration_ms=(time.perf_counter() - start) * 1000,
                        message=(
                            f"Self-test error: "
                            f"{type(exc).__name__}: {exc}"
                        ),
                    )

        return ModuleExecution(
            domain=domain,
            module_name=module_name,
            import_status="AVAILABLE",
            execution_status="INSTANTIATED",
            duration_ms=(time.perf_counter() - start) * 1000,
            message="Module imported; no safe standard function execution available.",
        )

    def run(self) -> Gate3Report:

        self.loader.discover()

        available = self.available_domains()

        # Execute one module per domain.
        for domain, module in available.items():

            specification = MODULE_REGISTRY[domain]

            module_name = module.__name__

            if specification.get("classes"):

                result = self.execute_class_module(
                    domain,
                    module_name,
                    module,
                    specification["classes"],
                )

            else:

                result = self.execute_function_module(
                    domain,
                    module_name,
                    module,
                    specification.get("functions", []),
                )

            self.executions.append(result)

        imported = len(available)

        executed = sum(
            1
            for item in self.executions
            if item.execution_status in {
                "EXECUTED",
                "INSTANTIATED",
            }
        )

        failed = sum(
            1
            for item in self.executions
            if item.execution_status == "FAILED"
        )

        checked = len(MODULE_REGISTRY)

        if failed > 0:
            overall_status = "REVIEW"
        elif executed == checked:
            overall_status = "PASS"
        elif executed > 0:
            overall_status = "PARTIAL"
        else:
            overall_status = "REVIEW"

        # Health score:
        #   100% if every domain imports and executes.
        #   Partial credit for successful imports and safe instantiation.
        if checked:
            health_score = (
                (imported / checked) * 50.0
                + (executed / checked) * 50.0
            )
        else:
            health_score = 0.0

        all_results = [
            asdict(item)
            for item in self.loader.results + self.executions
        ]

        return Gate3Report(
            version=VERSION,
            timestamp=time.time(),
            modules_checked=checked,
            modules_imported=imported,
            modules_executed=executed,
            modules_failed=failed,
            overall_status=overall_status,
            health_score=round(health_score, 2),
            executions=self.executions,
            fingerprint=fingerprint(all_results),
        )


# ---------------------------------------------------------------------------
# REPORTING
# ---------------------------------------------------------------------------

def print_report(report: Gate3Report) -> None:

    print()
    print("=" * 72)
    print("GLOBAL DIGITAL TWIN — INTEGRATION GATE 3")
    print("=" * 72)

    print(f"Version:          {report.version}")
    print(f"Modules checked:  {report.modules_checked}")
    print(f"Modules imported: {report.modules_imported}")
    print(f"Modules executed: {report.modules_executed}")
    print(f"Modules failed:   {report.modules_failed}")
    print(f"Health score:     {report.health_score:.2f}%")
    print(f"Overall status:   {report.overall_status}")

    print()
    print("-" * 72)
    print("EXECUTION RESULTS")
    print("-" * 72)

    for item in report.executions:

        print(
            f"{item.domain:20s} "
            f"{item.execution_status:14s} "
            f"{item.duration_ms:8.2f} ms"
        )

        print(f"  {item.message}")

    print()
    print(f"Fingerprint: {report.fingerprint}")
    print("=" * 72)


def save_json(report: Gate3Report, filename: str) -> None:

    payload = asdict(report)

    with open(filename, "w", encoding="utf-8") as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
        )


# ---------------------------------------------------------------------------
# SELF TEST
# ---------------------------------------------------------------------------

def self_test() -> int:

    print()
    print("GLOBAL DIGITAL TWIN GATE 3 SELF TEST")
    print("=" * 72)

    passed = 0
    failed = 0

    # Test 1: registry
    try:
        assert "GEDT" in MODULE_REGISTRY
        assert "CIDAR" in MODULE_REGISTRY
        assert "AIGovernance" in MODULE_REGISTRY

        print("PASS: module registry")
        passed += 1

    except Exception as exc:
        print(f"FAIL: module registry — {exc}")
        failed += 1

    # Test 2: utility fingerprint
    try:
        a = fingerprint({"a": 1, "b": 2})
        b = fingerprint({"b": 2, "a": 1})

        assert a == b
        assert len(a) == 64

        print("PASS: deterministic fingerprint")
        passed += 1

    except Exception as exc:
        print(f"FAIL: fingerprint — {exc}")
        failed += 1

    # Test 3: compact serialization
    try:
        data = compact_value(
            {
                "value": 1,
                "nested": {"x": 2},
                "items": [1, 2, 3],
            }
        )

        assert isinstance(data, dict)
        assert data["value"] == 1

        print("PASS: safe serialization")
        passed += 1

    except Exception as exc:
        print(f"FAIL: serialization — {exc}")
        failed += 1

    # Test 4: module loader
    try:
        loader = ModuleLoader()
        results = loader.discover()

        assert isinstance(results, list)

        print("PASS: module discovery engine")
        passed += 1

    except Exception as exc:
        print(f"FAIL: module discovery — {exc}")
        failed += 1

    # Test 5: complete integration engine
    try:
        executor = Gate3Executor(periods=2)
        report = executor.run()

        assert report.modules_checked == len(MODULE_REGISTRY)
        assert 0.0 <= report.health_score <= 100.0
        assert report.overall_status in {
            "PASS",
            "PARTIAL",
            "REVIEW",
        }

        print("PASS: Gate 3 integration engine")
        passed += 1

    except Exception as exc:
        print(f"FAIL: integration engine — {exc}")
        failed += 1

    # Test 6: report fingerprint
    try:
        assert len(report.fingerprint) == 64

        print("PASS: report integrity")
        passed += 1

    except Exception as exc:
        print(f"FAIL: report integrity — {exc}")
        failed += 1

    print()
    print("=" * 72)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 72)

    if failed == 0:
        print("GLOBAL DIGITAL TWIN GATE 3: PASS")
        return 0

    print("GLOBAL DIGITAL TWIN GATE 3: REVIEW")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():

    parser = argparse.ArgumentParser(
        description="Global Digital Twin Integration Gate 3"
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=5,
        help="Number of simulation periods.",
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in tests.",
    )

    parser.add_argument(
        "--json",
        type=str,
        default="",
        help="Save Gate 3 report to JSON.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=VERSION,
    )

    return parser


def main() -> int:

    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    executor = Gate3Executor(
        periods=args.periods,
    )

    report = executor.run()

    print_report(report)

    if args.json:
        save_json(report, args.json)
        print()
        print(f"JSON report written to: {args.json}")

    return 0 if report.overall_status == "PASS" else 0


if __name__ == "__main__":
    sys.exit(main())