"""Script de bundling avec Nuitka."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY_POINT = ROOT / "src" / "auto_classes" / "ui" / "__main__.py"
ASSETS_DIR = ROOT / "src" / "auto_classes" / "ui" / "assets"

NUITKA_ARGS = [
    sys.executable,
    "-m",
    "nuitka",
    "--standalone",
    "--onefile",
    "--enable-plugin=tk-inter",
    # Les pictogrammes du menu sont chargés à l'exécution depuis `ui/assets` :
    # sans cette copie, `ui.assets` ne les trouverait pas dans le binaire.
    f"--include-data-dir={ASSETS_DIR}=auto_classes/ui/assets",
    "--output-dir=dist",
    "--output-filename=auto-classes",
    str(ENTRY_POINT),
]


def main() -> None:
    subprocess.run(NUITKA_ARGS, check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
