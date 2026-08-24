from pathlib import Path


def test_gedt_project_structure():
    project_root = Path(__file__).resolve().parents[1]

    assert (project_root / "README.md").exists()
    assert (project_root / "src" / "gedt" / "__init__.py").exists()
    
    
    Add GEDT package structure test