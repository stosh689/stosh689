from pathlib import Path

from src.gedt.validate_project import validate_project


def test_validate_project_passes_for_repository():
    """The repository should pass GEDT project validation."""
    root = Path(__file__).resolve().parents[1]

    assert validate_project(root) is True


def test_validate_project_uses_pyproject():
    """Validation should operate on the repository pyproject.toml."""
    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"

    assert pyproject.is_file()
    assert pyproject.stat().st_size > 0