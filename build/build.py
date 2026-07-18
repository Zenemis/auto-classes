"""Script de bundling avec Nuitka."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY_POINT = ROOT / "src" / "auto_classes" / "ui" / "__main__.py"

NUITKA_ARGS = [
    sys.executable,
    "-m",
    "nuitka",
    "--standalone",
    "--onefile",
    "--enable-plugin=tk-inter",
    "--output-dir=dist",
    "--output-filename=auto-classes",
    str(ENTRY_POINT),
]


def main() -> None:
    subprocess.run(NUITKA_ARGS, check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
