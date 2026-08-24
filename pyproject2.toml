"""
GEDT clean compatibility project metadata.

This module provides a Python representation of the GEDT project metadata
for compatibility with project_health.py while the legacy pyproject.toml
remains preserved.

Do not delete or overwrite the existing project files.
"""

PROJECT_METADATA = {
    "build-system": {
        "requires": [
            "setuptools>=68",
            "wheel",
        ],
        "build-backend": "setuptools.build_meta",
    },
    "project": {
        "name": "gedt",
        "version": "1.1.0",
        "description": "Global Experimental Digital Twin Framework",
        "requires-python": ">=3.10",
        "dependencies": [
            "numpy",
            "pandas",
            "scipy",
            "matplotlib",
            "scikit-learn",
            "pytest",
            "requests",
            "flask",
            "sqlalchemy",
            "plotly",
            "networkx",
            "sympy",
            "statsmodels",
            "joblib",
            "tqdm",
        ],
    },
    "tool": {
        "pytest": {
            "ini_options": {
                "testpaths": [
                    "tests",
                ],
                "python_files": [
                    "test_*.py",
                ],
            },
        },
        "ruff": {
            "line-length": 100,
            "target-version": "py310",
        },
        "black": {
            "line-length": 100,
        },
        "setuptools": {
            "packages": {
                "find": {
                    "where": [
                        "src",
                    ],
                },
            },
        },
    },
}