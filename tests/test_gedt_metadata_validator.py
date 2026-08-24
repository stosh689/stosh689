"""Validation utilities for the standalone GEDT metadata program.
This module deliberately avoids pyproject.toml and the existing large
application codebase. It validates only the clean metadata representation
provided by metadata_program.py.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from metadata_program import GEDTMetadata, get_metadata
_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
_PYTHON_PATTERN = re.compile(r"^>=\d+\.\d+$")
@dataclass(frozen=True)
class ValidationResult:
    """Result of validating GEDT project metadata."""
    valid: bool
    errors: tuple[str, ...]
    def __bool__(self) -> bool:
        return self.valid
def validate_metadata(metadata: GEDTMetadata) -> ValidationResult:
    """Validate a GEDTMetadata object without touching project source files."""
    errors: list[str] = []
    if not metadata.name.strip():
        errors.append("Project name cannot be empty.")
    if not _VERSION_PATTERN.match(metadata.version):
        errors.append(f"Invalid project version: {metadata.version!r}")
    if not _PYTHON_PATTERN.match(metadata.python_requires):
        errors.append(
            f"Invalid Python requirement: {metadata.python_requires!r}"
        )
    if not metadata.dependencies:
        errors.append("Dependency list cannot be empty.")
    normalized: set[str] = set()
    for dependency in metadata.dependencies:
        dependency = dependency.strip()
        if not dependency:
            errors.append("Dependency list contains an empty entry.")
            continue
        key = dependency.lower()
        if key in normalized:
            errors.append(f"Duplicate dependency: {dependency}")
        normalized.add(key)
    return ValidationResult(
        valid=not errors,
        errors=tuple(errors),
    )
def validate_gedt() -> ValidationResult:
    """Validate the canonical standalone GEDT metadata."""
    return validate_metadata(get_metadata())
def is_valid_gedt() -> bool:
    """Return True when GEDT metadata passes validation."""
    return validate_gedt().valid
def main() -> int:
    """Run validation from the command line."""
    result = validate_gedt()
    if result.valid:
        print("GEDT metadata validation: PASSED")
        return 0
    print("GEDT metadata validation: FAILED")
    for error in result.errors:
        print(f"ERROR: {error}")
    return 1
if __name__ == "__main__":
    raise SystemExit(main())