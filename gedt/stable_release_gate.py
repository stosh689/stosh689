"""
GEDT v11.0.0 Stable Release Gate

Promotes RC1 to stable-release readiness only when the final
RC1 audit passes completely.

Usage:
    python stable_release_gate.py

Optional:
    python stable_release_gate.py --audit results/gedt_v11_rc1_audit.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

EXPECTED_PROJECT = "GEDT"
EXPECTED_VERSION = "11.0.0"
EXPECTED_RC = "RC1"

DEFAULT_AUDIT = (
    ROOT
    / "results"
    / "gedt_v11_rc1_audit.json"
)


def load_audit(path: Path) -> dict:
    """Load the RC1 audit report."""
    if not path.exists():
        raise FileNotFoundError(
            f"Audit report not found: {path}"
        )

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid audit JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            "Audit report must contain a JSON object."
        )

    return data


def validate_audit(data: dict) -> tuple[bool, list[str]]:
    """Validate every stable-release requirement."""
    failures: list[str] = []

    if data.get("project") != EXPECTED_PROJECT:
        failures.append(
            "Project must be GEDT."
        )

    if data.get("version") != EXPECTED_VERSION:
        failures.append(
            "Version must be 11.0.0."
        )

    if data.get("release_candidate") != EXPECTED_RC:
        failures.append(
            "Release candidate must be RC1."
        )

    if data.get("checks_total") != 7:
        failures.append(
            "RC1 audit must contain exactly 7 checks."
        )

    if data.get("checks_passed") != 7:
        failures.append(
            "All 7 RC1 audit checks must pass."
        )

    if data.get("score_percent") != 100.0:
        failures.append(
            "RC1 audit score must be exactly 100%."
        )

    if data.get("ready_for_stable") is not True:
        failures.append(
            "RC1 audit must report ready_for_stable=true."
        )

    results = data.get("results")

    if not isinstance(results, list):
        failures.append(
            "Audit results must be a list."
        )
    else:
        for result in results:
            if not isinstance(result, dict):
                failures.append(
                    "Invalid audit result entry."
                )
                continue

            if result.get("passed") is not True:
                failures.append(
                    f"Failed audit check: "
                    f"{result.get('name', 'unknown')}"
                )

    return not failures, failures


def create_stable_release_record(
    audit: dict,
) -> dict:
    """Create machine-readable stable-release evidence."""
    return {
        "project": EXPECTED_PROJECT,
        "version": EXPECTED_VERSION,
        "release_status": "STABLE_RELEASE_READY",
        "release_candidate": EXPECTED_RC,
        "audit_score_percent": audit["score_percent"],
        "audit_checks_passed": audit["checks_passed"],
        "audit_checks_total": audit["checks_total"],
        "ready_for_stable": True,
        "decision": (
            "GEDT v11.0.0 has passed the automated RC1 "
            "release gate and is ready for stable-release publication."
        ),
        "scientific_position": (
            "This release remains a research and analytical "
            "framework and does not constitute a guaranteed "
            "forecast of real-world economic outcomes."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate GEDT v11.0.0 stable-release readiness."
    )

    parser.add_argument(
        "--audit",
        default=str(DEFAULT_AUDIT),
        help="Path to the RC1 audit JSON report.",
    )

    args = parser.parse_args()

    audit_path = Path(args.audit)

    print("=" * 70)
    print("GEDT v11.0.0 STABLE RELEASE GATE")
    print("=" * 70)
    print()

    try:
        audit = load_audit(audit_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    valid, failures = validate_audit(audit)

    if not valid:
        print("STABLE RELEASE: NOT READY")
        print()
        print("Requirements not satisfied:")

        for failure in failures:
            print(f"  - {failure}")

        print()
        print("=" * 70)

        return 1

    record = create_stable_release_record(audit)

    output = (
        ROOT
        / "results"
        / "gedt_v11_stable_release_ready.json"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            record,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print("RC1 audit: PASS")
    print("Audit score: 100.00%")
    print("Audit checks: 7/7")
    print()
    print("STABLE RELEASE: READY")
    print()
    print(
        "Recommended stable version: "
        "v11.0.0"
    )
    print()
    print(f"Release evidence: {output}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())