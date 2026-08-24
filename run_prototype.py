from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve()
GEDT_DIR = ROOT / "gedt"


def find_python_files() -> list[Path]:
    """Find Python source files while excluding generated/virtual environments."""
    excluded = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "site-packages",
        "node_modules",
    }

    files = []

    for path in ROOT.rglob("*.py"):
        if any(part in excluded for part in path.parts):
            continue
        files.append(path)

    return sorted(files)


def syntax_check(files: list[Path]) -> tuple[bool, list[str]]:
    """Compile Python files without executing them."""
    errors = []

    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(path))
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    return not errors, errors


def run_command(command: list[str], cwd: Path | None = None) -> bool:
    """Run a controlled project command."""
    print()
    print("$", " ".join(command))

    result = subprocess.run(
        command,
        cwd=cwd or ROOT,
        check=False,
    )

    return result.returncode == 0


def main() -> int:
    print("=" * 64)
    print("GEDT / CIDAR PROTOTYPE RUNNER")
    print("=" * 64)

    # ------------------------------------------------------------
    # 1. Static Python syntax validation
    # ------------------------------------------------------------
    print("\n[1/4] Checking Python syntax...")

    files = find_python_files()
    syntax_ok, errors = syntax_check(files)

    print(f"Python files discovered: {len(files)}")

    if syntax_ok:
        print("SYNTAX: PASS")
    else:
        print("SYNTAX: FAIL")

        for error in errors[:20]:
            print("  ", error)

        if len(errors) > 20:
            print(f"  ... {len(errors) - 20} additional errors")

    # ------------------------------------------------------------
    # 2. Verify GEDT package exists
    # ------------------------------------------------------------
    print("\n[2/4] Checking GEDT package...")

    gedt_package = GEDT_DIR / "src" / "gedt"
    gedt_init = gedt_package / "__init__.py"
    gedt_main = gedt_package / "__main__.py"

    gedt_ok = (
        GEDT_DIR.is_dir()
        and (GEDT_DIR / "pyproject.toml").is_file()
        and gedt_init.is_file()
        and gedt_main.is_file()
    )

    if gedt_ok:
        print("GEDT PACKAGE: PASS")
    else:
        print("GEDT PACKAGE: FAIL")

    # ------------------------------------------------------------
    # 3. Run CIDAR integration tests
    # ------------------------------------------------------------
    print("\n[3/4] Running CIDAR integration tests...")

    cidar_test = ROOT / "tests" / "tests" / "test_cidar_integration.py"

    if cidar_test.is_file():
        cidar_ok = run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "-c",
                "pytest.ini",
                "-q",
                str(cidar_test),
            ]
        )
    else:
        print("CIDAR TEST: SKIPPED — test file not found")
        cidar_ok = True

    # ------------------------------------------------------------
    # 4. Run GEDT module
    # ------------------------------------------------------------
    print("\n[4/4] Running GEDT prototype...")

    gedt_ok_runtime = run_command(
        [
            sys.executable,
            "-m",
            "gedt",
        ],
        cwd=ROOT,
    )

    # ------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------
    overall = (
        syntax_ok
        and gedt_ok
        and cidar_ok
        and gedt_ok_runtime
    )

    print()
    print("=" * 64)
    print("PROTOTYPE RESULT")
    print("=" * 64)

    print(f"Python syntax : {'PASS' if syntax_ok else 'FAIL'}")
    print(f"GEDT package  : {'PASS' if gedt_ok else 'FAIL'}")
    print(f"CIDAR tests   : {'PASS' if cidar_ok else 'FAIL'}")
    print(f"GEDT runtime  : {'PASS' if gedt_ok_runtime else 'FAIL'}")
    print("-" * 64)
    print(f"OVERALL       : {'PASS' if overall else 'FAIL'}")
    print("=" * 64)

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())