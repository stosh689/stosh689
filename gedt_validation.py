"""
GEDT Validation Layer
=====================

Non-destructive validation helpers for the GEDT/CIDAR project.

This module intentionally does NOT modify or replace existing project files.
It provides lightweight validation of:
    - weighted decision calculations
    - confidence-adjusted evidence
    - audit records
    - deterministic audit hashes
    - optional integration with existing CIDAR modules

Python 3.11+
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationResult:
    """Result of an individual validation check."""

    name: str
    passed: bool
    message: str
    value: Any = None
    expected: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "value": self.value,
            "expected": self.expected,
        }


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------

def _validate_numeric_sequence(
    values: Sequence[float],
    name: str,
) -> None:
    if not values:
        raise ValueError(f"{name} cannot be empty.")

    for value in values:
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"Every value in {name} must be numeric; "
                f"got {type(value).__name__}."
            )

        if not math.isfinite(float(value)):
            raise ValueError(
                f"Every value in {name} must be finite; got {value!r}."
            )


def weighted_score(
    weights: Sequence[float],
    criteria: Sequence[float],
) -> float:
    """
    Calculate a normalized weighted score.

    Example:
        weighted_score([5, 3, 2], [0.9, 0.8, 0.7])
        -> 0.83
    """
    if len(weights) != len(criteria):
        raise ValueError(
            "weights and criteria must contain the same number of values."
        )

    _validate_numeric_sequence(weights, "weights")
    _validate_numeric_sequence(criteria, "criteria")

    if any(float(weight) < 0 for weight in weights):
        raise ValueError("weights cannot be negative.")

    if any(float(value) < 0 or float(value) > 1 for value in criteria):
        raise ValueError("criteria must be between 0 and 1.")

    total_weight = sum(float(weight) for weight in weights)

    if total_weight <= 0:
        raise ValueError("The total weight must be greater than zero.")

    score = sum(
        float(weight) * float(criteria_value)
        for weight, criteria_value in zip(weights, criteria)
    ) / total_weight

    # Normalize floating-point representation for deterministic testing.
    return round(score, 10)


def confidence_adjusted_score(
    score: float,
    confidence: float,
) -> float:
    """
    Apply confidence to an individual evidence score.
    """
    if not math.isfinite(float(score)):
        raise ValueError("score must be finite.")

    if not math.isfinite(float(confidence)):
        raise ValueError("confidence must be finite.")

    if not 0 <= float(score) <= 1:
        raise ValueError("score must be between 0 and 1.")

    if not 0 <= float(confidence) <= 1:
        raise ValueError("confidence must be between 0 and 1.")

    return round(float(score) * float(confidence), 10)


def fuse_confidence_adjusted_evidence(
    *score_confidence_pairs: float,
) -> float:
    """
    Fuse score/confidence pairs.

    Arguments are supplied as:

        score1, confidence1,
        score2, confidence2,
        ...

    Example:

        fuse_confidence_adjusted_evidence(
            0.9, 1.0,
            0.8, 1.0,
            0.7, 1.0,
            0.6, 1.0,
        )

        -> 0.75
    """
    if not score_confidence_pairs:
        raise ValueError("At least one score/confidence pair is required.")

    if len(score_confidence_pairs) % 2 != 0:
        raise ValueError(
            "Evidence values must be supplied as score/confidence pairs."
        )

    adjusted_scores: list[float] = []

    for index in range(0, len(score_confidence_pairs), 2):
        score = float(score_confidence_pairs[index])
        confidence = float(score_confidence_pairs[index + 1])

        adjusted_scores.append(
            confidence_adjusted_score(score, confidence)
        )

    return round(sum(adjusted_scores) / len(adjusted_scores), 10)


# ---------------------------------------------------------------------------
# Decision validation
# ---------------------------------------------------------------------------

def validate_decision(
    weights: Sequence[float],
    criteria: Sequence[float],
    threshold: float = 0.70,
) -> ValidationResult:
    """
    Validate a weighted decision calculation.

    This function deliberately does not import or alter the existing
    ethical_decision implementation.
    """
    if not 0 <= float(threshold) <= 1:
        raise ValueError("threshold must be between 0 and 1.")

    score = weighted_score(weights, criteria)

    decision = "Approved" if score >= float(threshold) else "Review"

    return ValidationResult(
        name="weighted_decision",
        passed=True,
        message="Weighted decision calculated successfully.",
        value=decision,
        expected={
            "score": score,
            "threshold": round(float(threshold), 10),
        },
    )


# ---------------------------------------------------------------------------
# Audit records
# ---------------------------------------------------------------------------

def create_validation_record(
    weights: Sequence[float],
    criteria: Sequence[float],
    threshold: float = 0.70,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a deterministic, JSON-compatible GEDT validation record.
    """
    score = weighted_score(weights, criteria)

    decision = "Approved" if score >= float(threshold) else "Review"

    record: dict[str, Any] = {
        "version": "1.0",
        "system": "GEDT",
        "component": "CIDAR",
        "weights": [float(value) for value in weights],
        "criteria": [float(value) for value in criteria],
        "threshold": round(float(threshold), 10),
        "weighted_score": score,
        "decision": decision,
    }

    if metadata:
        record["metadata"] = dict(metadata)

    return record


def canonicalize_record(record: Mapping[str, Any]) -> str:
    """
    Convert an audit record into deterministic JSON.
    """
    return json.dumps(
        dict(record),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def generate_validation_hash(record: Mapping[str, Any]) -> str:
    """
    Generate a deterministic SHA-256 hash for an audit record.
    """
    canonical = canonicalize_record(record)

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Integrity checks
# ---------------------------------------------------------------------------

def validate_record_integrity(
    record: Mapping[str, Any],
) -> ValidationResult:
    """
    Verify that an audit record contains internally consistent values.
    """
    required_fields = {
        "version",
        "system",
        "component",
        "weights",
        "criteria",
        "threshold",
        "weighted_score",
        "decision",
    }

    missing = required_fields.difference(record.keys())

    if missing:
        return ValidationResult(
            name="record_integrity",
            passed=False,
            message=f"Missing required fields: {sorted(missing)}",
        )

    try:
        calculated = weighted_score(
            record["weights"],
            record["criteria"],
        )

        stored = round(float(record["weighted_score"]), 10)

        threshold = round(float(record["threshold"]), 10)

        expected_decision = (
            "Approved"
            if calculated >= threshold
            else "Review"
        )

        if stored != calculated:
            return ValidationResult(
                name="record_integrity",
                passed=False,
                message="Stored weighted score does not match calculation.",
                value=stored,
                expected=calculated,
            )

        if record["decision"] != expected_decision:
            return ValidationResult(
                name="record_integrity",
                passed=False,
                message="Stored decision does not match weighted score.",
                value=record["decision"],
                expected=expected_decision,
            )

    except (TypeError, ValueError, KeyError) as exc:
        return ValidationResult(
            name="record_integrity",
            passed=False,
            message=f"Record validation failed: {exc}",
        )

    return ValidationResult(
        name="record_integrity",
        passed=True,
        message="Audit record is internally consistent.",
        value=record["decision"],
        expected=expected_decision,
    )


# ---------------------------------------------------------------------------
# Existing project compatibility
# ---------------------------------------------------------------------------

def check_existing_cidar_import() -> ValidationResult:
    """
    Check whether the existing cidar module can be imported.

    This is intentionally isolated so validation can continue even if
    optional project dependencies are unavailable.
    """
    try:
        import cidar  # type: ignore

        return ValidationResult(
            name="cidar_import",
            passed=True,
            message="Existing cidar module imported successfully.",
            value=getattr(cidar, "__file__", None),
        )

    except Exception as exc:
        return ValidationResult(
            name="cidar_import",
            passed=False,
            message=f"Existing cidar module could not be imported: {exc}",
        )


def check_optional_module(module_name: str) -> ValidationResult:
    """
    Check an optional module without making it a hard dependency.
    """
    try:
        __import__(module_name)

        return ValidationResult(
            name=f"module:{module_name}",
            passed=True,
            message=f"{module_name} imported successfully.",
        )

    except Exception as exc:
        return ValidationResult(
            name=f"module:{module_name}",
            passed=False,
            message=f"{module_name} unavailable: {exc}",
        )


# ---------------------------------------------------------------------------
# Complete validation suite
# ---------------------------------------------------------------------------

def run_validation_suite() -> list[ValidationResult]:
    """
    Run non-destructive GEDT/CIDAR validation checks.
    """
    results: list[ValidationResult] = []

    # Basic weighted calculation.
    try:
        score = weighted_score(
            [5, 3, 2],
            [0.9, 0.8, 0.7],
        )

        results.append(
            ValidationResult(
                name="weighted_score",
                passed=score == 0.83,
                message="Weighted score validation completed.",
                value=score,
                expected=0.83,
            )
        )
    except Exception as exc:
        results.append(
            ValidationResult(
                name="weighted_score",
                passed=False,
                message=str(exc),
            )
        )

    # Confidence fusion.
    try:
        fused = fuse_confidence_adjusted_evidence(
            0.9, 1.0,
            0.8, 1.0,
            0.7, 1.0,
            0.6, 1.0,
        )

        results.append(
            ValidationResult(
                name="confidence_fusion",
                passed=fused == 0.75,
                message="Confidence fusion validation completed.",
                value=fused,
                expected=0.75,
            )
        )
    except Exception as exc:
        results.append(
            ValidationResult(
                name="confidence_fusion",
                passed=False,
                message=str(exc),
            )
        )

    # Low-confidence fusion.
    try:
        fused = fuse_confidence_adjusted_evidence(
            0.9, 0.5,
            0.8, 0.5,
            0.7, 0.5,
            0.6, 0.5,
        )

        results.append(
            ValidationResult(
                name="low_confidence_fusion",
                passed=fused == 0.375,
                message="Low-confidence fusion validation completed.",
                value=fused,
                expected=0.375,
            )
        )
    except Exception as exc:
        results.append(
            ValidationResult(
                name="low_confidence_fusion",
                passed=False,
                message=str(exc),
            )
        )

    # Audit record.
    try:
        record = create_validation_record(
            weights=[5, 3, 2],
            criteria=[0.9, 0.8, 0.7],
            threshold=0.70,
        )

        integrity = validate_record_integrity(record)
        results.append(integrity)

        digest = generate_validation_hash(record)

        results.append(
            ValidationResult(
                name="audit_hash",
                passed=(
                    isinstance(digest, str)
                    and len(digest) == 64
                ),
                message="Deterministic SHA-256 audit hash generated.",
                value=digest,
                expected="64-character SHA-256 digest",
            )
        )

    except Exception as exc:
        results.append(
            ValidationResult(
                name="audit_record",
                passed=False,
                message=str(exc),
            )
        )

    # Existing CIDAR import.
    results.append(check_existing_cidar_import())

    return results


def validation_summary() -> dict[str, Any]:
    """
    Return a machine-readable summary of the validation suite.
    """
    results = run_validation_suite()

    passed = sum(result.passed for result in results)
    failed = len(results) - passed

    return {
        "system": "GEDT",
        "component": "CIDAR",
        "total_checks": len(results),
        "passed": passed,
        "failed": failed,
        "success": failed == 0,
        "results": [
            result.as_dict()
            for result in results
        ],
    }


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Run validation from the command line.

    Usage:

        python gedt_validation.py
    """
    summary = validation_summary()

    print("GEDT Validation")
    print("=" * 60)

    for result in summary["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {result['name']}: {result['message']}")

        if result["value"] is not None:
            print(f"       value:    {result['value']}")

        if result["expected"] is not None:
            print(f"       expected: {result['expected']}")

    print("=" * 60)
    print(
        f"Checks: {summary['total_checks']} | "
        f"Passed: {summary['passed']} | "
        f"Failed: {summary['failed']}"
    )

    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())