"""
GEDT Validation Runner

Performs basic repository and configuration checks.
"""

from pathlib import Path
import sys


REQUIRED_FILES = [
    "pyproject_clean.toml",
    "Dockerfile.gedt",
    "run_tests.py",
    "requirements-test.txt",
    "tests/test_gedt_smoke.py",
]


def check_files() -> list[str]:
    missing = []

    for filename in REQUIRED_FILES:
        if not Path(filename).exists():
            missing.append(filename)

    return missing


def main() -> int:
    missing = check_files()

    if missing:
        print("GEDT validation FAILED")
        print("\nMissing files:")

        for filename in missing:
            print(f"  - {filename}")

        return 1

    print("GEDT validation PASSED")
    print("All required validation files are present.")

    return 0


if __name__ == "__main__":
    sys.exit(main())