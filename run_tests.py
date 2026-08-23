"""
GEDT Test Runner

Runs the project's automated test suite and provides
a simple command-line entry point.
"""

import sys
import pytest


def main() -> int:
    """Run the GEDT test suite."""
    return pytest.main(["-q", "tests"])


if __name__ == "__main__":
    sys.exit(main())