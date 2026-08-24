"""Compatibility entry point for the GEDT validation layer."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from gedt_validation import (
    ValidationResult,
    weighted_score,
    confidence_adjusted_score,
    fuse_confidence_adjusted_evidence,
    validate_decision,
    create_validation_record,
    canonicalize_record,
    generate_validation_hash,
    validate_record_integrity,
    check_existing_cidar_import,
    check_optional_module,
    run_validation_suite,
    validation_summary,
    main,
)

__all__ = [
    "ROOT",
    "ValidationResult",
    "weighted_score",
    "confidence_adjusted_score",
    "fuse_confidence_adjusted_evidence",
    "validate_decision",
    "create_validation_record",
    "canonicalize_record",
    "generate_validation_hash",
    "validate_record_integrity",
    "check_existing_cidar_import",
    "check_optional_module",
    "run_validation_suite",
    "validation_summary",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())