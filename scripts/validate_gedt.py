"""
GEDT Repository Validation

Checks that the clean GEDT foundation files exist.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "pyproject_clean.toml",
    "Dockerfile.gedt",
    "run_tests.py",
    "requirements-test.txt",
    "tests/test_gedt_smoke.py",
]


def check_files() -> list[str]:
    return [
        filename
        for filename in REQUIRED_FILES
        if not (ROOT / filename).exists()
    ]


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