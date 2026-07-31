"""Bundling de l'UI en exécutable autonome, via Nuitka.

    python build/build.py                 # exe + empreinte SHA-256 dans dist/
    python build/build.py --no-checksum   # exe seul
    python build/build.py --dry-run       # affiche la commande Nuitka sans compiler

Le nom du binaire porte la version et la plateforme (`auto-classes-0.1.0-windows-x86_64.exe`) :
les artefacts de plusieurs plateformes se retrouvent côte à côte dans une release GitHub,
un nom neutre les rendrait indistinguables.
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "src"
ENTRY_POINT = SOURCE_DIR / "auto_classes" / "ui" / "__main__.py"
ASSETS_DIR = SOURCE_DIR / "auto_classes" / "ui" / "assets"

COMPANY_NAME = "auto-classes"
PRODUCT_NAME = "auto-classes"
FILE_DESCRIPTION = "Automatisation de la création de classes d'élèves"

# Le tableau des architectures que rapporte `platform.machine()` diffère d'un OS à
# l'autre pour une même machine (AMD64 sous Windows, x86_64 ailleurs) : on normalise
# pour que le nom du binaire ne dépende pas de la plateforme de build.
MACHINE_ALIASES = {"amd64": "x86_64", "arm64": "aarch64"}


def read_version() -> str:
    """Version lue dans les sources, sans importer le paquet.

    Importer `auto_classes` exigerait qu'il soit installé (ou que `src/` soit dans
    `sys.path`) ; le build doit pouvoir tourner sur une copie du dépôt seule.
    """
    init = SOURCE_DIR / "auto_classes" / "__init__.py"
    for line in init.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError(f"__version__ introuvable dans {init}")


def platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    return f"{system}-{MACHINE_ALIASES.get(machine, machine)}"


def executable_name(version: str) -> str:
    suffix = ".exe" if platform.system() == "Windows" else ""
    return f"auto-classes-{version}-{platform_tag()}{suffix}"


def check_interpreter_is_buildable() -> None:
    """Refuse le Python du Microsoft Store, avec lequel Nuitka ne peut pas lier.

    Cette distribution n'expose pas `python3xx.lib` : Nuitka va jusqu'au bout de la
    compilation C avant d'échouer sur `unable to find dynamic system library`. Autant
    le dire tout de suite, et nommer le remède.
    """
    if "WindowsApps" in sys.base_prefix:
        raise SystemExit(
            "Nuitka ne sait pas lier le Python du Microsoft Store "
            f"({sys.executable}).\nInstalle CPython depuis python.org et relance le build "
            "avec cet interpréteur."
        )


def nuitka_command(version: str, output_dir: Path) -> list[str]:
    args = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=tk-inter",
        # Les pictogrammes du menu sont chargés à l'exécution depuis `ui/assets` :
        # sans cette copie, `ui.assets` ne les trouverait pas dans le binaire.
        f"--include-data-dir={ASSETS_DIR}=auto_classes/ui/assets",
        # customtkinter charge ses thèmes JSON et ses polices depuis son propre paquet,
        # par chemin de fichier : Nuitka ne peut pas les déduire des imports.
        "--include-package-data=customtkinter",
        # Sans quoi la compilation s'interrompt sur une question interactive (Nuitka
        # récupère au besoin le compilateur ou `dependency walker`) : intenable en CI.
        "--assume-yes-for-downloads",
        # Supprime les dossiers intermédiaires `.build`/`.onefile-build` : seul le
        # binaire final nous intéresse, et ils pèsent plusieurs centaines de Mo.
        "--remove-output",
        f"--output-dir={output_dir}",
        f"--output-filename={executable_name(version)}",
        f"--product-name={PRODUCT_NAME}",
        f"--product-version={version}",
        f"--file-version={version}",
        f"--file-description={FILE_DESCRIPTION}",
        f"--company-name={COMPANY_NAME}",
    ]
    if platform.system() == "Windows":
        # Application graphique : une console qui s'ouvre derrière la fenêtre serait du bruit.
        args.append("--windows-console-mode=disable")
    args.append(str(ENTRY_POINT))
    return args


def write_checksum(executable: Path) -> Path:
    """Empreinte au format `sha256sum`, vérifiable par `sha256sum -c` (ou l'équivalent PowerShell)."""
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    checksum_path = executable.with_suffix(executable.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {executable.name}\n", encoding="utf-8")
    return checksum_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="build", description="Bundling d'auto-classes avec Nuitka")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "dist",
        help="dossier de sortie du binaire (défaut : dist/)",
    )
    parser.add_argument("--no-checksum", action="store_true", help="ne pas écrire le fichier .sha256")
    parser.add_argument(
        "--print-version",
        action="store_true",
        help="afficher la version du paquet et s'arrêter (utilisé par la CD pour valider un tag)",
    )
    parser.add_argument("--dry-run", action="store_true", help="afficher la commande Nuitka sans l'exécuter")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    version = read_version()
    if args.print_version:
        print(version)
        return 0

    output_dir: Path = args.output_dir
    command = nuitka_command(version, output_dir)

    if args.dry_run:
        print(" ".join(command))
        return 0

    check_interpreter_is_buildable()
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, check=True, cwd=ROOT)

    executable = output_dir / executable_name(version)
    if not executable.is_file():
        raise SystemExit(f"Nuitka n'a produit aucun binaire à l'emplacement attendu : {executable}")
    print(f"Binaire : {executable}")

    if not args.no_checksum:
        print(f"Empreinte : {write_checksum(executable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
