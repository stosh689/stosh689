"""
GEDT v11.0 RC1 Release Report Generator

Generates a formal release-evidence report from the GEDT
release gate and evaluation components.

Outputs:
- JSON machine-readable evidence
- Markdown human-readable release report

This report describes software and model-system validation.
It does not claim that GEDT predicts the real economy with certainty.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import release_check


RELEASE_NAME = "GEDT v11.0"
RELEASE_CANDIDATE = "RC1"
REPORT_VERSION = "1.0.0"


def collect_release_evidence() -> dict[str, Any]:
    """Run the release gate and collect evidence."""

    results = release_check.run_release_gate()

    passed = sum(
        result.passed
        for result in results
    )

    total = len(results)

    percentage = (
        passed / total * 100.0
        if total
        else 0.0
    )

    release_ready = (
        total > 0
        and passed == total
    )

    return {
        "release": {
            "name": RELEASE_NAME,
            "candidate": RELEASE_CANDIDATE,
            "report_version": REPORT_VERSION,
        },
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "environment": {
            "python_version": platform.python_version(),
            "python_implementation": (
                platform.python_implementation()
            ),
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "release_gate": {
            "checks_passed": passed,
            "checks_total": total,
            "score_percentage": percentage,
            "ready": release_ready,
            "checks": [
                asdict(result)
                for result in results
            ],
        },
    }


def validate_release_evidence(
    evidence: dict[str, Any],
) -> None:
    """Validate the release evidence structure."""

    required = {
        "release",
        "generated_at",
        "environment",
        "release_gate",
    }

    missing = required - set(evidence)

    if missing:
        raise ValueError(
            f"Missing release evidence sections: "
            f"{sorted(missing)}"
        )

    release = evidence["release"]

    if release.get("name") != RELEASE_NAME:
        raise ValueError(
            "Unexpected release name"
        )

    if release.get("candidate") != RELEASE_CANDIDATE:
        raise ValueError(
            "Unexpected release candidate"
        )

    gate = evidence["release_gate"]

    required_gate = {
        "checks_passed",
        "checks_total",
        "score_percentage",
        "ready",
        "checks",
    }

    missing_gate = required_gate - set(gate)

    if missing_gate:
        raise ValueError(
            f"Missing release gate fields: "
            f"{sorted(missing_gate)}"
        )

    if gate["checks_total"] < 1:
        raise ValueError(
            "Release gate must contain checks"
        )

    if not (
        0.0
        <= float(gate["score_percentage"])
        <= 100.0
    ):
        raise ValueError(
            "Invalid release gate score"
        )

    if gate["checks_passed"] > gate["checks_total"]:
        raise ValueError(
            "Passed checks exceed total checks"
        )

    if not isinstance(
        gate["ready"],
        bool,
    ):
        raise ValueError(
            "Release readiness must be boolean"
        )


def save_json(
    evidence: dict[str, Any],
    output: Path,
) -> None:
    """Save machine-readable release evidence."""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            evidence,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def markdown_report(
    evidence: dict[str, Any],
) -> str:
    """Build the human-readable Markdown report."""

    release = evidence["release"]
    gate = evidence["release_gate"]
    environment = evidence["environment"]

    status = (
        "READY FOR RC1"
        if gate["ready"]
        else "NOT READY FOR RC1"
    )

    lines = [
        f"# {release['name']} {release['candidate']}",
        "",
        "## Release Evidence Report",
        "",
        f"**Report version:** {release['report_version']}",
        "",
        f"**Generated:** {evidence['generated_at']}",
        "",
        f"**Status:** **{status}**",
        "",
        "## Release Gate",
        "",
        "| Metric | Result |",
        "|---|---:|",
        (
            f"| Checks passed | "
            f"{gate['checks_passed']} |"
        ),
        (
            f"| Checks total | "
            f"{gate['checks_total']} |"
        ),
        (
            f"| Gate score | "
            f"{gate['score_percentage']:.1f}% |"
        ),
        (
            f"| Release ready | "
            f"{gate['ready']} |"
        ),
        "",
        "## Checks",
        "",
        "| Check | Status | Runtime (s) |",
        "|---|---|---:|",
    ]

    for check in gate["checks"]:
        status_text = (
            "PASS"
            if check["passed"]
            else "FAIL"
        )

        lines.append(
            f"| {check['name']} "
            f"| {status_text} "
            f"| {check['elapsed_seconds']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Environment",
            "",
            f"- Python: `{environment['python_version']}`",
            (
                "- Implementation: "
                f"`{environment['python_implementation']}`"
            ),
            f"- System: `{environment['system']}`",
            f"- Machine: `{environment['machine']}`",
            f"- Platform: `{environment['platform']}`",
            "",
            "## Validation Scope",
            "",
            "The RC1 gate evaluates:",
            "",
            "1. Package and version integrity",
            "2. Configuration validity",
            "3. Core simulation execution",
            "4. Baseline benchmark execution",
            "5. Scenario benchmark execution",
            "6. Monte Carlo uncertainty execution",
            "7. Master evaluation execution",
            "8. Scientific evaluation execution",
            "9. Computational performance benchmark",
            "10. Automated test execution",
            "",
            "## Scientific Interpretation",
            "",
            "GEDT is evaluated here as a computational "
            "economic modelling and simulation platform.",
            "",
            "A passing release gate demonstrates that the "
            "implemented software can execute its defined "
            "analytical workflow under the tested conditions.",
            "",
            "It does **not** establish that GEDT can predict "
            "future economic outcomes with certainty, nor does "
            "it establish causal validity for real-world "
            "economic policy.",
            "",
            "Real-world validation requires independent data, "
            "out-of-sample testing, comparison with established "
            "economic models, uncertainty quantification, "
            "sensitivity analysis, and peer review.",
            "",
            "## Release Decision",
            "",
        ]
    )

    if gate["ready"]:
        lines.extend(
            [
                (
                    "**RC1 release gate: PASS.** "
                    "All configured release checks passed."
                ),
                "",
            ]
        )
    else:
        lines.extend(
            [
                (
                    "**RC1 release gate: FAIL.** "
                    "One or more release checks require "
                    "correction before release."
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Reproducibility",
            "",
            "The release process uses explicit configuration "
            "parameters and deterministic random seeds where "
            "stochastic simulation is required.",
            "",
            "Recommended baseline configuration:",
            "",
            "```text",
            "periods = 12",
            "trials  = 1000",
            "seed    = 42",
            "```",
            "",
            "## Limitations",
            "",
            "- The current economic model is a research prototype.",
            "- Synthetic or simplified dynamics must not be treated "
              "as forecasts.",
            "- Performance depends on the execution environment.",
            "- Benchmark results should be independently reproduced.",
            "- Economic validity requires external empirical validation.",
            "",
            "## Conclusion",
            "",
            f"GEDT {RELEASE_CANDIDATE} provides a structured release "
            "gate covering software integrity, simulation execution, "
            "uncertainty analysis, scientific evaluation, performance, "
            "and automated testing.",
            "",
        ]
    )

    return "\n".join(lines)


def save_markdown(
    content: str,
    output: Path,
) -> None:
    """Save the Markdown report."""

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        content,
        encoding="utf-8",
    )


def print_report(
    evidence: dict[str, Any],
) -> None:
    """Print a concise release summary."""

    gate = evidence["release_gate"]

    print()
    print("=" * 80)
    print("GEDT v11.0 RC1 RELEASE EVIDENCE")
    print("=" * 80)

    print()
    print(
        f"Checks: "
        f"{gate['checks_passed']}/"
        f"{gate['checks_total']}"
    )

    print(
        f"Score: "
        f"{gate['score_percentage']:.1f}%"
    )

    print(
        f"Ready: "
        f"{gate['ready']}"
    )

    print()

    for check in gate["checks"]:
        status = (
            "PASS"
            if check["passed"]
            else "FAIL"
        )

        print(
            f"[{status}] "
            f"{check['name']}"
        )

    print()

    if gate["ready"]:
        print(
            "RELEASE DECISION: READY FOR RC1"
        )
    else:
        print(
            "RELEASE DECISION: NOT READY"
        )

    print()
    print("=" * 80)
    print()


def main() -> int:
    """Generate the complete release evidence package."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate GEDT v11.0 RC1 release evidence."
        )
    )

    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "results/gedt_v11_rc1_release_evidence.json"
        ),
    )

    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path(
            "results/GEDT_v11_RC1_RELEASE_REPORT.md"
        ),
    )

    args = parser.parse_args()

    try:
        evidence = collect_release_evidence()

        validate_release_evidence(
            evidence
        )

        markdown = markdown_report(
            evidence
        )

        save_json(
            evidence,
            args.json_output,
        )

        save_markdown(
            markdown,
            args.markdown_output,
        )

        print_report(
            evidence
        )

        print(
            f"JSON: {args.json_output}"
        )

        print(
            f"Markdown: {args.markdown_output}"
        )

        return (
            0
            if evidence["release_gate"]["ready"]
            else 1
        )

    except Exception as exc:
        print(
            f"RELEASE REPORT FAILED: {exc}"
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())