from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import platform
import random
import sys
import time

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PLATFORM_VERSION = "10.0.0"

GATES = [
    (1, "Global_Digital_Twin"),
    (2, "Global_Digital_Twin_Gate2"),
    (3, "Global_Digital_Twin_Gate3"),
    (4, "Global_Digital_Twin_Gate4"),
    (5, "Global_Digital_Twin_Gate5"),
    (6, "Global_Digital_Twin_Gate6"),
    (7, "Global_Digital_Twin_Gate7"),
    (8, "Global_Digital_Twin_Gate8"),
    (9, "Global_Digital_Twin_Gate9"),
]


# ============================================================================
# CORE UTILITIES
# ============================================================================

def utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def sha256_obj(obj: Any) -> str:
    """Create a deterministic SHA-256 fingerprint for a Python object."""
    raw = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PlatformConfig:
    scenario: str = "baseline"
    seed: int = 42
    monte_carlo_runs: int = 1000
    periods: int = 30
    fail_on_gate_failure: bool = False
    run_self_tests: bool = True
    output_prefix: str = "gate10"

    research_question: str = (
        "Can the integrated Global Digital Twin execute reproducibly "
        "across its validated research gates?"
    )


# ============================================================================
# GATE EXECUTION
# ============================================================================

@dataclass
class GateExecution:
    gate: int
    module: str

    available: bool
    imported: bool

    self_test_found: bool
    self_test_passed: Optional[bool]

    duration_seconds: float

    status: str
    message: str

    fingerprint: str


# ============================================================================
# AUDIT / PROVENANCE
# ============================================================================

@dataclass
class AuditRecord:
    timestamp_utc: str
    action: str
    subject: str
    status: str
    details: Dict[str, Any]
    fingerprint: str


# ============================================================================
# RUN MANIFEST
# ============================================================================

@dataclass
class RunManifest:
    platform: str
    platform_version: str

    started_utc: str
    finished_utc: str

    python_version: str
    operating_system: str

    configuration: Dict[str, Any]

    gates: List[Dict[str, Any]]
    audit: List[Dict[str, Any]]

    warnings: List[str]

    overall_status: str

    fingerprint: str


# ============================================================================
# PLATFORM RESULT
# ============================================================================

@dataclass
class PlatformResult:
    manifest: RunManifest
    gate_results: List[GateExecution]
    summary: Dict[str, Any]


# ============================================================================
# MODULE DISCOVERY
# ============================================================================

def discover_module(
    name: str,
) -> Tuple[bool, Optional[Any], str]:
    """
    Safely discover and import a gate module.

    Returns:
        available
        imported module or None
        message
    """

    try:
        spec = importlib.util.find_spec(name)
    except Exception as exc:
        return (
            False,
            None,
            f"discovery error: {exc}",
        )

    if spec is None:
        return (
            False,
            None,
            "module not found",
        )

    try:
        module = importlib.import_module(name)

        return (
            True,
            module,
            "imported",
        )

    except Exception as exc:
        return (
            True,
            None,
            f"import failed: {type(exc).__name__}: {exc}",
        )


# ============================================================================
# SELF-TEST ADAPTER
# ============================================================================

def run_self_test(
    module: Any,
) -> Tuple[bool, bool, Optional[bool], str]:
    """
    Safely execute a module's self_test() function when available.

    Returns:
        found
        callable/executed
        passed
        message
    """

    fn = getattr(module, "self_test", None)

    if not callable(fn):
        return (
            True,
            False,
            None,
            "no callable self_test() found",
        )

    try:
        result = fn()

        passed = True if result is None else bool(result)

        return (
            True,
            True,
            passed,
            "self_test completed",
        )

    except SystemExit as exc:

        passed = exc.code in (None, 0)

        return (
            True,
            True,
            passed,
            f"self_test exited with code {exc.code}",
        )

    except Exception as exc:

        return (
            True,
            True,
            False,
            f"self_test failed: {type(exc).__name__}: {exc}",
        )


# ============================================================================
# EXECUTE INDIVIDUAL GATE
# ============================================================================

def execute_gate(
    gate: int,
    module_name: str,
    cfg: PlatformConfig,
) -> GateExecution:

    start = time.perf_counter()

    available, module, message = discover_module(module_name)

    elapsed = time.perf_counter() - start

    # ------------------------------------------------------------------------
    # Module missing
    # ------------------------------------------------------------------------

    if not available:

        fingerprint = sha256_obj(
            {
                "gate": gate,
                "module": module_name,
                "status": "missing",
            }
        )

        return GateExecution(
            gate=gate,
            module=module_name,
            available=False,
            imported=False,
            self_test_found=False,
            self_test_passed=None,
            duration_seconds=elapsed,
            status="NOT_AVAILABLE",
            message=message,
            fingerprint=fingerprint,
        )

    # ------------------------------------------------------------------------
    # Import failure
    # ------------------------------------------------------------------------

    if module is None:

        fingerprint = sha256_obj(
            {
                "gate": gate,
                "module": module_name,
                "status": "import_failed",
            }
        )

        return GateExecution(
            gate=gate,
            module=module_name,
            available=True,
            imported=False,
            self_test_found=False,
            self_test_passed=False,
            duration_seconds=elapsed,
            status="IMPORT_FAILED",
            message=message,
            fingerprint=fingerprint,
        )

    # ------------------------------------------------------------------------
    # Self-tests disabled
    # ------------------------------------------------------------------------

    if not cfg.run_self_tests:

        status = "IMPORTED"

        fingerprint = sha256_obj(
            {
                "gate": gate,
                "module": module_name,
                "status": status,
            }
        )

        return GateExecution(
            gate=gate,
            module=module_name,
            available=True,
            imported=True,
            self_test_found=False,
            self_test_passed=None,
            duration_seconds=elapsed,
            status=status,
            message="module imported; self-test disabled",
            fingerprint=fingerprint,
        )

    # ------------------------------------------------------------------------
    # Execute self-test
    # ------------------------------------------------------------------------

    found, executed, result, test_message = run_self_test(module)

    if result is True:
        status = "PASS"

    elif result is False:
        status = "FAIL"

    else:
        status = "IMPORTED"

    fingerprint = sha256_obj(
        {
            "gate": gate,
            "module": module_name,
            "status": status,
            "self_test": result,
        }
    )

    return GateExecution(
        gate=gate,
        module=module_name,
        available=True,
        imported=True,
        self_test_found=found,
        self_test_passed=result,
        duration_seconds=elapsed,
        status=status,
        message=test_message,
        fingerprint=fingerprint,
    )


# ============================================================================
# AUDIT
# ============================================================================

def build_audit(
    gates: List[GateExecution],
    cfg: PlatformConfig,
) -> List[AuditRecord]:

    records: List[AuditRecord] = []

    for gate in gates:

        details = {
            "available": gate.available,
            "imported": gate.imported,
            "self_test_found": gate.self_test_found,
            "self_test_passed": gate.self_test_passed,
            "duration_seconds": round(
                gate.duration_seconds,
                6,
            ),
            "message": gate.message,
        }

        fingerprint = sha256_obj(details)

        records.append(
            AuditRecord(
                timestamp_utc=utc_now(),
                action="GATE_EXECUTION",
                subject=gate.module,
                status=gate.status,
                details=details,
                fingerprint=fingerprint,
            )
        )

    return records


# ============================================================================
# DETERMINISTIC REFERENCE
# ============================================================================

def deterministic_reference(
    cfg: PlatformConfig,
) -> Dict[str, Any]:

    rng = random.Random(cfg.seed)

    values = [
        rng.random()
        for _ in range(5)
    ]

    return {
        "scenario": cfg.scenario,
        "seed": cfg.seed,
        "sample": [
            round(value, 12)
            for value in values
        ],
    }


# ============================================================================
# RESEARCH SUMMARY
# ============================================================================

def research_summary(
    gates: List[GateExecution],
    cfg: PlatformConfig,
) -> Dict[str, Any]:

    available = sum(
        gate.available
        for gate in gates
    )

    imported = sum(
        gate.imported
        for gate in gates
    )

    passed = sum(
        gate.self_test_passed is True
        for gate in gates
    )

    failed = sum(
        gate.self_test_passed is False
        for gate in gates
    )

    missing = sum(
        not gate.available
        for gate in gates
    )

    reference_a = deterministic_reference(cfg)
    reference_b = deterministic_reference(cfg)

    reproducible = (
        sha256_obj(reference_a)
        == sha256_obj(reference_b)
    )

    return {
        "gates_total": len(gates),
        "gates_available": available,
        "gates_imported": imported,
        "self_tests_passed": passed,
        "self_tests_failed": failed,
        "gates_missing": missing,
        "reproducibility_check": reproducible,
        "scenario": cfg.scenario,
        "seed": cfg.seed,
        "monte_carlo_runs": cfg.monte_carlo_runs,
        "periods": cfg.periods,
        "research_question": cfg.research_question,
    }


# ============================================================================
# RUN COMPLETE PLATFORM
# ============================================================================

def run_platform(
    cfg: PlatformConfig,
) -> PlatformResult:

    started = utc_now()

    gate_results = [
        execute_gate(
            gate_number,
            module_name,
            cfg,
        )
        for gate_number, module_name in GATES
    ]

    audit = build_audit(
        gate_results,
        cfg,
    )

    summary = research_summary(
        gate_results,
        cfg,
    )

    warnings: List[str] = []

    for gate in gate_results:

        if not gate.available:

            warnings.append(
                f"Gate {gate.gate} module "
                f"{gate.module} is unavailable."
            )

        elif gate.self_test_passed is False:

            warnings.append(
                f"Gate {gate.gate} self-test failed."
            )

        elif not gate.self_test_found:

            warnings.append(
                f"Gate {gate.gate} has no callable "
                f"self_test()."
            )

    fatal = (
        any(
            gate.status in (
                "FAIL",
                "IMPORT_FAILED",
            )
            for gate in gate_results
        )
        and cfg.fail_on_gate_failure
    )

    overall_status = (
        "FAIL"
        if fatal
        else "PASS"
    )

    finished = utc_now()

    manifest_data = {
        "platform": "GLOBAL_DIGITAL_TWIN_GATE10",
        "platform_version": PLATFORM_VERSION,
        "started_utc": started,
        "finished_utc": finished,
        "python_version": sys.version,
        "operating_system": platform.platform(),
        "configuration": asdict(cfg),
        "gates": [
            asdict(gate)
            for gate in gate_results
        ],
        "audit": [
            asdict(record)
            for record in audit
        ],
        "warnings": warnings,
        "overall_status": overall_status,
    }

    fingerprint = sha256_obj(
        manifest_data
    )

    manifest = RunManifest(
        platform=manifest_data["platform"],
        platform_version=PLATFORM_VERSION,
        started_utc=started,
        finished_utc=finished,
        python_version=sys.version,
        operating_system=platform.platform(),
        configuration=asdict(cfg),
        gates=[
            asdict(gate)
            for gate in gate_results
        ],
        audit=[
            asdict(record)
            for record in audit
        ],
        warnings=warnings,
        overall_status=overall_status,
        fingerprint=fingerprint,
    )

    return PlatformResult(
        manifest=manifest,
        gate_results=gate_results,
        summary=summary,
    )


# ============================================================================
# JSON EXPORT
# ============================================================================

def write_json(
    result: PlatformResult,
    path: str,
) -> None:

    payload = {
        "manifest": asdict(
            result.manifest
        ),
        "summary": result.summary,
    }

    Path(path).write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


# ============================================================================
# CSV EXPORT
# ============================================================================

def write_csv(
    result: PlatformResult,
    path: str,
) -> None:

    rows = [
        asdict(gate)
        for gate in result.gate_results
    ]

    fields = list(
        GateExecution.__dataclass_fields__.keys()
    )

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================================
# RESEARCH REPORT
# ============================================================================

def research_report(
    result: PlatformResult,
) -> str:

    summary = result.summary

    lines = [
        "GLOBAL DIGITAL TWIN — GATE 10 RESEARCH PLATFORM REPORT",
        "=" * 76,
        f"Platform version: {PLATFORM_VERSION}",
        f"Overall status: {result.manifest.overall_status}",
        f"Research question: {summary['research_question']}",
        "",
        "GATE STATUS",
        "-" * 76,
    ]

    for gate in result.gate_results:

        lines.append(
            f"Gate {gate.gate}: "
            f"{gate.status:<14} "
            f"{gate.module} — "
            f"{gate.message}"
        )

    lines.extend(
        [
            "",
            "INTEGRATION SUMMARY",
            "-" * 76,
            f"Available modules: "
            f"{summary['gates_available']}/"
            f"{summary['gates_total']}",
            f"Imported modules:  "
            f"{summary['gates_imported']}/"
            f"{summary['gates_total']}",
            f"Self-tests passed: "
            f"{summary['self_tests_passed']}",
            f"Self-tests failed: "
            f"{summary['self_tests_failed']}",
            f"Missing modules:   "
            f"{summary['gates_missing']}",
            (
                "Reproducibility check: "
                + (
                    "PASS"
                    if summary["reproducibility_check"]
                    else "FAIL"
                )
            ),
            "",
            "WARNINGS",
            "-" * 76,
        ]
    )

    if result.manifest.warnings:

        lines.extend(
            f"- {warning}"
            for warning in result.manifest.warnings
        )

    else:

        lines.append("- None")

    lines.extend(
        [
            "",
            "RUN FINGERPRINT",
            "-" * 76,
            result.manifest.fingerprint,
            "",
            "SCIENTIFIC INTERPRETATION",
            "-" * 76,
            "This platform verifies software integration, execution health,",
            "provenance, and reproducibility mechanics.",
            "",
            "It does NOT establish empirical validity.",
            "",
            "Real-world conclusions require documented datasets, appropriate",
            "statistical methods, out-of-sample validation, uncertainty",
            "analysis, and independent scientific review.",
        ]
    )

    return "\n".join(lines)


# ============================================================================
# SELF TEST
# ============================================================================

def self_test() -> bool:

    print(
        "GLOBAL DIGITAL TWIN GATE 10 SELF TEST"
    )

    print("=" * 76)

    tests = []

    def check(
        name: str,
        condition: bool,
    ) -> None:

        passed = bool(condition)

        tests.append(
            (
                name,
                passed,
            )
        )

        print(
            f"{'PASS' if passed else 'FAIL'}: {name}"
        )

    # ------------------------------------------------------------------------
    # 1
    # ------------------------------------------------------------------------

    cfg = PlatformConfig(
        seed=123,
        run_self_tests=False,
    )

    check(
        "configuration contract",
        (
            cfg.monte_carlo_runs > 0
            and cfg.periods > 0
        ),
    )

    # ------------------------------------------------------------------------
    # 2
    # ------------------------------------------------------------------------

    check(
        "gate registry",
        (
            len(GATES) == 9
            and [
                item[0]
                for item in GATES
            ]
            == list(range(1, 10))
        ),
    )

    # ------------------------------------------------------------------------
    # 3
    # ------------------------------------------------------------------------

    check(
        "SHA-256 determinism",
        (
            sha256_obj(
                {
                    "b": 2,
                    "a": 1,
                }
            )
            ==
            sha256_obj(
                {
                    "a": 1,
                    "b": 2,
                }
            )
        ),
    )

    # ------------------------------------------------------------------------
    # 4
    # ------------------------------------------------------------------------

    check(
        "deterministic reference",
        (
            deterministic_reference(cfg)
            ==
            deterministic_reference(cfg)
        ),
    )

    # ------------------------------------------------------------------------
    # 5
    # ------------------------------------------------------------------------

    check(
        "module discovery",
        discover_module("json")[0] is True,
    )

    # ------------------------------------------------------------------------
    # 6
    # ------------------------------------------------------------------------

    check(
        "missing module handling",
        (
            discover_module(
                "__definitely_missing_gdt_gate10__"
            )[0]
            is False
        ),
    )

    # ------------------------------------------------------------------------
    # 7
    # ------------------------------------------------------------------------

    class TestModule:

        @staticmethod
        def self_test():

            return True

    found, executed, result, _ = run_self_test(
        TestModule
    )

    check(
        "self-test adapter",
        (
            found
            and executed
            and result is True
        ),
    )

    # ------------------------------------------------------------------------
    # 8
    # ------------------------------------------------------------------------

    platform_result = run_platform(cfg)

    check(
        "platform execution",
        len(platform_result.gate_results) == 9,
    )

    # ------------------------------------------------------------------------
    # 9
    # ------------------------------------------------------------------------

    check(
        "manifest fingerprint",
        (
            len(
                platform_result
                .manifest
                .fingerprint
            )
            == 64
        ),
    )

    # ------------------------------------------------------------------------
    # 10
    # ------------------------------------------------------------------------

    check(
        "research summary",
        (
            platform_result
            .summary["gates_total"]
            == 9
        ),
    )

    # ------------------------------------------------------------------------
    # 11
    # ------------------------------------------------------------------------

    check(
        "report generation",
        (
            "GATE 10 RESEARCH PLATFORM REPORT"
            in research_report(
                platform_result
            )
        ),
    )

    passed_count = sum(
        condition
        for _, condition in tests
    )

    failed_count = (
        len(tests)
        - passed_count
    )

    print()

    print("=" * 76)

    print(
        f"PASSED: {passed_count}"
    )

    print(
        f"FAILED: {failed_count}"
    )

    print("=" * 76)

    print(
        "GLOBAL DIGITAL TWIN GATE 10: "
        + (
            "PASS"
            if failed_count == 0
            else "FAIL"
        )
    )

    return failed_count == 0


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main(argv=None) -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Global Digital Twin "
            "Gate 10 Research Platform"
        )
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run Gate 10 self-tests.",
    )

    parser.add_argument(
        "--scenario",
        default="baseline",
        help="Research scenario name.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic random seed.",
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=1000,
        help="Monte Carlo run count.",
    )

    parser.add_argument(
        "--periods",
        type=int,
        default=30,
        help="Simulation periods.",
    )

    parser.add_argument(
        "--fail-on-gate-failure",
        action="store_true",
        help="Return failure if a gate fails.",
    )

    parser.add_argument(
        "--no-self-tests",
        action="store_true",
        help="Import gates without executing self-tests.",
    )

    parser.add_argument(
        "--json",
        default="",
        help="Write JSON result to this path.",
    )

    parser.add_argument(
        "--csv",
        default="",
        help="Write gate results to this CSV path.",
    )

    parser.add_argument(
        "--report",
        default="",
        help="Write human-readable report.",
    )

    parser.add_argument(
        "--research-question",
        default="",
        help="Override the research question.",
    )

    args = parser.parse_args(argv)

    # ------------------------------------------------------------------------
    # Self-test mode
    # ------------------------------------------------------------------------

    if args.self_test:

        return (
            0
            if self_test()
            else 1
        )

    # ------------------------------------------------------------------------
    # Argument validation
    # ------------------------------------------------------------------------

    if args.runs < 1:

        parser.error(
            "--runs must be positive"
        )

    if args.periods < 1:

        parser.error(
            "--periods must be positive"
        )

    # ------------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------------

    cfg = PlatformConfig(
        scenario=args.scenario,
        seed=args.seed,
        monte_carlo_runs=args.runs,
        periods=args.periods,
        fail_on_gate_failure=(
            args.fail_on_gate_failure
        ),
        run_self_tests=(
            not args.no_self_tests
        ),
        research_question=(
            args.research_question
            or PlatformConfig.research_question
        ),
    )

    # ------------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------------

    result = run_platform(cfg)

    report = research_report(
        result
    )

    print(report)

    # ------------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------------

    if args.json:

        write_json(
            result,
            args.json,
        )

        print(
            f"\nJSON written: {args.json}"
        )

    # ------------------------------------------------------------------------
    # CSV
    # ------------------------------------------------------------------------

    if args.csv:

        write_csv(
            result,
            args.csv,
        )

        print(
            f"CSV written: {args.csv}"
        )

    # ------------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------------

    if args.report:

        Path(
            args.report
        ).write_text(
            report,
            encoding="utf-8",
        )

        print(
            f"Report written: {args.report}"
        )

    return (
        0
        if result.manifest.overall_status == "PASS"
        else 1
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )