from pathlib import Path
import shutil


def patch_pyproject() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / "pyproject.toml"
    backup = root / "pyproject.toml.backup"

    if not target.exists():
        raise FileNotFoundError(f"Missing: {target}")

    text = target.read_text(encoding="utf-8")

    marker = '[tool.setuptools.packages.find]\nwhere = ["src"]'

    if marker not in text:
        raise RuntimeError(
            "Could not find the valid setuptools configuration. "
            "No changes were made."
        )

    # Preserve the original before making any change.
    shutil.copy2(target, backup)

    # Keep the valid TOML configuration and remove everything
    # that was accidentally appended after it.
    clean_text = text.split(marker, 1)[0] + marker + "\n"

    target.write_text(clean_text, encoding="utf-8")

    print(f"Patched: {target}")
    print(f"Backup:  {backup}")
    print("The repository's other files were not modified.")


if __name__ == "__main__":
    patch_pyproject()