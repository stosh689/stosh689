from __future__ import annotations

import sys

from gedt import __version__


def main() -> int:
    print("GEDT")
    print("=" * 40)
    print("Global Economic Digital Twin")
    print(f"Version: {__version__}")
    print("Prototype status: READY")
    return 0


if __name__ == "__main__":
    sys.exit(main())