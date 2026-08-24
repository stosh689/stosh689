"""Tests for the standalone GEDT metadata validator."""

from metadata_program import GEDTMetadata
from metadata_validator import (
    is_valid_gedt,
    validate_gedt,
    validate_metadata,
)


def test_canonical_gedt_metadata_is_valid():
    result = validate_gedt()

    assert result.valid is True
    assert result.errors == ()


def test_is_valid_gedt_returns_true():
    assert is_valid_gedt() is True


def test_valid_custom_metadata():
    metadata = GEDTMetadata(
        name="gedt",
        version="2.0.0",
        description="Test GEDT project",
        python_requires=">=3.11",
        dependencies=("numpy", "pytest"),
    )

    result = validate_metadata(metadata)

    assert result.valid is True
    assert result.errors == ()


def test_empty_project_name_fails():
    metadata = GEDTMetadata(
        name="",
        version="1.0.0",
        description="Test",
        python_requires=">=3.10",
        dependencies=("numpy",),
    )

    result = validate_metadata(metadata)

    assert result.valid is False
    assert "Project name cannot be empty." in result.errors


def test_invalid_version_fails():
    metadata = GEDTMetadata(
        name="gedt",
        version="invalid",
        description="Test",
        python_requires=">=3.10",
        dependencies=("numpy",),
    )

    result = validate_metadata(metadata)

    assert result.valid is False
    assert any("Invalid project version" in error for error in result.errors)


def test_invalid_python_requirement_fails():
    metadata = GEDTMetadata(
        name="gedt",
        version="1.0.0",
        description="Test",
        python_requires="python3",
        dependencies=("numpy",),
    )

    result = validate_metadata(metadata)

    assert result.valid is False
    assert any("Invalid Python requirement" in error for error in result.errors)


def test_duplicate_dependencies_fail():
    metadata = GEDTMetadata(
        name="gedt",
        version="1.0.0",
        description="Test",
        python_requires=">=3.10",
        dependencies=("numpy", "pytest", "NumPy"),
    )

    result = validate_metadata(metadata)

    assert result.valid is False
    assert any("Duplicate dependency" in error for error in result.errors)


def test_empty_dependency_fails():
    metadata = GEDTMetadata(
        name="gedt",
        version="1.0.0",
        description="Test",
        python_requires=">=3.10",
        dependencies=("numpy", ""),
    )

    result = validate_metadata(metadata)

    assert result.valid is False
    assert "Dependency list contains an empty entry." in result.errors


def test_empty_dependency_list_fails():
    metadata = GEDTMetadata(
        name="gedt",
        version="1.0.0",
        description="Test",
        python_requires=">=3.10",
        dependencies=(),
    )

    result = validate_metadata(metadata)

    assert result.valid is False
    assert "Dependency list cannot be empty." in result.errors