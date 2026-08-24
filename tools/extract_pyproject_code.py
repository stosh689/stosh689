from __future__ import annotations
from pathlib import Path
import ast
import re
import shutil
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pyproject.toml"
BACKUP = ROOT / "pyproject_full_backup.txt"
OUTPUT = ROOT / "extracted_project_code.py"
def backup_source() -> None:
    """Create a byte-for-byte backup without modifying pyproject.toml."""
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing source file: {SOURCE}")
    shutil.copy2(SOURCE, BACKUP)
    print(f"Backup created: {BACKUP}")
def extract_python_blocks(text: str) -> list[str]:
    """
    Extract obvious Python code blocks from TOML/string content.
    This does not attempt to rewrite the original project.
    """
    blocks: list[str] = []
    # Markdown-style fenced Python blocks.
    fenced = re.findall(
        r"```(?:python|py)\s*\n(.*?)```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    blocks.extend(fenced)
    # Triple-quoted strings containing Python-looking source.
    triple = re.findall(
        r'(?:"""|\'\'\')(.*?)(?:"""|\'\'\')',
        text,
        flags=re.DOTALL,
    )
    for block in triple:
        stripped = block.strip()
        if not stripped:
            continue
        # Keep only blocks that contain recognizable Python constructs.
        if re.search(
            r"\b(def|class|import|from|if __name__|async def)\b",
            stripped,
        ):
            blocks.append(stripped)
    return blocks
def extract_inline_python(text: str) -> list[str]:
    """Find simple Python-looking lines without modifying the source."""
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if (
            stripped.startswith(("def ", "class ", "import ", "from "))
            or stripped.startswith("if __name__")
        ):
            lines.append(stripped)
    return lines
def validate_python(code: str) -> bool:
    """Check whether extracted text is syntactically valid Python."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False
def build_output() -> None:
    text = SOURCE.read_text(encoding="utf-8", errors="replace")
    blocks = extract_python_blocks(text)
    valid_blocks: list[str] = []
    for block in blocks:
        if validate_python(block):
            valid_blocks.append(block)
    header = '''"""
Generated working Python extraction.
IMPORTANT:
- This file is generated from pyproject.toml.
- The original pyproject.toml is never modified by this program.
- Review extracted code before using it in production.
"""
'''
    with OUTPUT.open("w", encoding="utf-8") as f:
        f.write(header)
        for index, block in enumerate(valid_blocks, start=1):
            f.write(f"\n\n# ===== Extracted block {index} =====\n\n")
            f.write(block)
            f.write("\n")
        if not valid_blocks:
            f.write(
                "\n# No complete standalone Python blocks were found.\n"
                "# The original pyproject.toml remains untouched.\n"
            )
    print(f"Working file created: {OUTPUT}")
    print(f"Valid Python blocks extracted: {len(valid_blocks)}")
def main() -> None:
    print("Starting safe project extraction...")
    print(f"Source: {SOURCE}")
    backup_source()
    build_output()
    print()
    print("Done.")
    print("Original pyproject.toml was NOT modified.")
if __name__ == "__main__":
    main()